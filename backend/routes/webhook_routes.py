"""
Webhook Routes for LIFEXIA WhatsApp Integration
Handles incoming messages from WhatsApp users via Meta Cloud API
Users can chat with LifeXia directly on WhatsApp — no website needed.

FIXES APPLIED:
- Reads WHATSAPP_VERIFY_TOKEN from app config / env (no more hardcoded token)
- Uses current_app.config for service access (app factory compatible)
- Adds per-user conversation context tracking for natural chat flow
"""

from flask import Blueprint, request, jsonify, current_app
import os
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)

# ─── In-memory conversation context per WhatsApp user ───────────────
# Stores recent messages so the RAG service can provide contextual responses
# In production, replace with Redis or a database
_user_conversations = defaultdict(list)
MAX_CONTEXT_MESSAGES = 5


def _get_conversation_context(phone_number: str) -> str:
    """Build conversation context string from recent messages"""
    history = _user_conversations.get(phone_number, [])
    if not history:
        return ''

    lines = []
    for msg in history[-MAX_CONTEXT_MESSAGES:]:
        role = msg['role']
        text = msg['text'][:200]  # Truncate for context window
        lines.append(f"{role}: {text}")

    return "\n".join(lines)


def _record_message(phone_number: str, role: str, text: str):
    """Record a message in conversation history"""
    _user_conversations[phone_number].append({
        'role': role,
        'text': text,
        'timestamp': datetime.now().isoformat()
    })
    # Keep only recent messages
    if len(_user_conversations[phone_number]) > MAX_CONTEXT_MESSAGES * 2:
        _user_conversations[phone_number] = _user_conversations[phone_number][-MAX_CONTEXT_MESSAGES:]


# ─── Webhook Verification (GET) ────────────────────────────────────

@webhook_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Meta webhook verification endpoint.
    Configure this in Meta Developer Console:
    - Callback URL: https://your-domain.com/api/whatsapp/webhook
    - Verify Token: (value of WHATSAPP_VERIFY_TOKEN in .env)
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Read verify token from config/env (NOT hardcoded)
    verify_token = current_app.config.get('WHATSAPP_VERIFY_TOKEN') or os.getenv('WHATSAPP_VERIFY_TOKEN', '')

    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            logger.info("✅ WhatsApp Webhook verified successfully!")
            return challenge, 200
        else:
            logger.warning(f"❌ Webhook verification failed — token mismatch")
            return "Forbidden", 403

    return "Not Found", 404


# ─── Incoming Message Handler (POST) ───────────────────────────────

@webhook_bp.route('/webhook', methods=['POST'])
def handle_incoming_message():
    """
    Handle incoming WhatsApp messages.
    This endpoint receives messages from users and:
    1. Records the user message (opens 24h response window)
    2. Processes the message with the RAG chatbot
    3. Sends the AI response back via WhatsApp
    """
    data = request.get_json()
    logger.info("📩 Received WhatsApp webhook payload")

    try:
        # Get services from app config (app-factory safe)
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        rag_service = current_app.config.get('RAG_SERVICE')

        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    value = change.get('value', {})

                    # ── Process incoming messages ──
                    if 'messages' in value:
                        for message in value['messages']:
                            from_number = message.get('from')
                            message_type = message.get('type')

                            # Record that user messaged us (opens 24h window)
                            if whatsapp_service and from_number:
                                whatsapp_service.record_user_message(from_number)
                                logger.info(f"📱 Message from {from_number} — 24h window opened")

                            # Extract message content based on type
                            message_content = _extract_message_content(message, message_type)

                            if message_content and from_number:
                                logger.info(f"💬 [{from_number}]: {message_content}")

                                # Record user message in conversation history
                                _record_message(from_number, 'User', message_content)

                                # Process with RAG chatbot
                                response_text = _process_user_query(
                                    message_content, from_number, rag_service
                                )

                                # Record assistant response
                                _record_message(from_number, 'Assistant', response_text)

                                # Send response back via WhatsApp
                                if whatsapp_service and response_text:
                                    # Clean markdown for WhatsApp formatting
                                    wa_text = _clean_for_whatsapp(response_text)
                                    result = whatsapp_service.send_text_message(
                                        from_number, wa_text[:4096]
                                    )
                                    logger.info(
                                        f"📤 Response sent to {from_number}: "
                                        f"success={result.get('success')}"
                                    )

                    # ── Handle status updates (delivered, read, etc.) ──
                    if 'statuses' in value:
                        for status in value['statuses']:
                            status_type = status.get('status')
                            recipient = status.get('recipient_id', 'unknown')
                            logger.debug(f"📊 Message to {recipient}: {status_type}")

        return jsonify({"status": "received", "success": True}), 200

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Helper Functions ──────────────────────────────────────────────

def _extract_message_content(message: dict, message_type: str) -> str | None:
    """Extract text content from various WhatsApp message types"""
    if message_type == 'text':
        return message.get('text', {}).get('body')
    elif message_type == 'button':
        return message.get('button', {}).get('text')
    elif message_type == 'interactive':
        interactive = message.get('interactive', {})
        if interactive.get('type') == 'button_reply':
            return interactive.get('button_reply', {}).get('title')
        elif interactive.get('type') == 'list_reply':
            return interactive.get('list_reply', {}).get('title')
    elif message_type == 'image':
        caption = message.get('image', {}).get('caption', '')
        return caption if caption else "I sent an image"
    elif message_type == 'location':
        lat = message.get('location', {}).get('latitude')
        lng = message.get('location', {}).get('longitude')
        if lat and lng:
            return f"hospitals near me (location: {lat},{lng})"
    return None


def _clean_for_whatsapp(text: str) -> str:
    """Convert markdown formatting to WhatsApp-friendly format"""
    # WhatsApp uses *bold* (not **bold**) and _italic_ (not *italic*)
    text = text.replace('##', '')  # Remove markdown headers
    text = text.replace('**', '*')  # Convert bold
    text = text.replace('---', '─' * 20)  # Horizontal rules
    return text.strip()


def _process_user_query(query: str, phone_number: str, rag_service) -> str:
    """
    Process incoming WhatsApp user query.
    Routes to RAG service for drug info or provides menu options.
    """
    try:
        query_lower = query.strip().lower()

        # ── Handle menu / greeting commands ──
        if query_lower in ['hi', 'hello', 'hey', 'start', 'menu', 'help']:
            return """👋 Welcome to *LIFEXIA* — Your AI Health Assistant on WhatsApp!

I can help you with:

1️⃣ *Drug Information* — Ask about any medicine
   Example: "Tell me about Paracetamol"

2️⃣ *Dosage & Side Effects* — Detailed drug info
   Example: "Side effects of Ibuprofen"

3️⃣ *Drug Interactions* — Check safety
   Example: "Can I take Aspirin with Ibuprofen?"

4️⃣ *Nearby Hospitals* — Send your location 📍

5️⃣ *Emergency Help* — Type "emergency"

6️⃣ *Ayushman Card Hospitals* — Type "ayushman"

Just type your question and I'll help! 💊"""

        # ── Emergency contacts ──
        if query_lower in ['emergency', 'sos', '108']:
            return """🚨 *EMERGENCY CONTACTS*

📞 *108* — Ambulance (India)
📞 *112* — General Emergency
📞 *102* — Maternity Emergency

🏥 *Nearest Emergency Hospitals:*
• Civil Hospital: +91-79-22683721
• SAL Hospital: +91-79-40200200
• Star Hospital: +91-79-27560456

Stay calm and call emergency services immediately.

— LIFEXIA Emergency System"""

        # ── Ayushman card info ──
        if 'ayushman' in query_lower:
            return """🏥 *Ayushman Bharat Card Hospitals (Ahmedabad)*

1. Civil Hospital — All specialties (FREE)
2. SAL Hospital — Cardiac, Neuro, Ortho
3. Star Hospital — Multi-specialty
4. Zydus Hospital — Transplant, Oncology
5. Apollo Hospital — All specialties
6. KD Hospital — Multi-specialty

All provide *cashless treatment* under AB-PMJAY.

📋 *Required Documents:*
• Ayushman Bharat Card
• Aadhaar Card
• Valid ID Proof

— LIFEXIA Health Network"""

        # ── Use RAG service for drug/health queries ──
        if rag_service:
            try:
                # Build conversation context for more natural responses
                context = _get_conversation_context(phone_number)
                response = rag_service.query(
                    question=query,
                    user_type='patient',
                    context=context
                )
                if response:
                    return response
            except Exception as e:
                logger.error(f"RAG query failed for WhatsApp user {phone_number}: {e}")

        # ── Default helpful response ──
        return f"""Thank you for asking about: *{query}*

I'm processing your request. Here's what I can help with:

💊 *Medicine info* — Ask "What is [medicine name]?"
📋 *Dosage* — Ask "Dosage for [medicine name]"
⚠️ *Side effects* — Ask "Side effects of [medicine name]"
🔄 *Interactions* — Ask "Can I take [med1] with [med2]?"

Type *menu* to see all options.

— LIFEXIA Health Assistant"""

    except Exception as e:
        logger.error(f"Query processing error for {phone_number}: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try again or type *menu* for options.\n\nFor emergencies, call *108*."
