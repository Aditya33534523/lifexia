"""
Webhook Routes for LIFEXIA WhatsApp Integration
Handles incoming messages from WhatsApp users via Meta Cloud API
"""

from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)

# This will be set from app.py
whatsapp_service = None

# Verify token for Meta (Use this in the Meta Developer Portal)
VERIFY_TOKEN = "lifexia_webhook_verify_2024"


def init_webhook_service(service):
    """Initialize the WhatsApp service for webhooks"""
    global whatsapp_service
    whatsapp_service = service
    logger.info("Webhook service initialized")


@webhook_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Meta webhook verification endpoint.
    Configure this in Meta Developer Console:
    - Callback URL: https://your-domain.com/api/whatsapp/webhook
    - Verify Token: lifexia_webhook_verify_2024
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("WhatsApp Webhook verified successfully!")
            return challenge, 200
        else:
            logger.warning("Webhook verification failed - invalid token")
            return "Forbidden", 403

    return "Not Found", 404


@webhook_bp.route('/webhook', methods=['POST'])
def handle_incoming_message():
    """
    Handle incoming WhatsApp messages.
    This endpoint receives messages from users and:
    1. Records the user message (opens 24h window)
    2. Processes the message with RAG chatbot
    3. Sends a response back via WhatsApp
    """
    data = request.get_json()
    logger.info(f"Received WhatsApp webhook payload")

    try:
        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    value = change.get('value', {})

                    # Process incoming messages
                    if 'messages' in value:
                        for message in value['messages']:
                            from_number = message.get('from')
                            message_type = message.get('type')

                            # Record that user messaged us (opens 24h window)
                            if whatsapp_service and from_number:
                                whatsapp_service.record_user_message(from_number)
                                logger.info(f"Recorded message from {from_number} - 24h window opened")

                            # Extract message content based on type
                            message_content = None
                            if message_type == 'text':
                                message_content = message.get('text', {}).get('body')
                            elif message_type == 'button':
                                message_content = message.get('button', {}).get('text')
                            elif message_type == 'interactive':
                                interactive = message.get('interactive', {})
                                if interactive.get('type') == 'button_reply':
                                    message_content = interactive.get('button_reply', {}).get('title')
                                elif interactive.get('type') == 'list_reply':
                                    message_content = interactive.get('list_reply', {}).get('title')

                            if message_content:
                                logger.info(f"Message from {from_number}: {message_content}")

                                # Process message with RAG chatbot
                                response_text = process_user_query(message_content, from_number)

                                # Send response back via WhatsApp
                                if whatsapp_service and response_text:
                                    result = whatsapp_service.send_text_message(from_number, response_text)
                                    logger.info(f"Sent response to {from_number}: success={result.get('success')}")

                    # Handle status updates (delivered, read, etc.)
                    if 'statuses' in value:
                        for status in value['statuses']:
                            message_id = status.get('id')
                            status_type = status.get('status')
                            logger.info(f"Message {message_id} status: {status_type}")

        return jsonify({"status": "received", "success": True}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


def process_user_query(query: str, phone_number: str) -> str:
    """
    Process incoming WhatsApp user query.
    Routes to RAG service for drug info or provides menu options.
    """
    try:
        query_lower = query.strip().lower()

        # Handle menu commands
        if query_lower in ['hi', 'hello', 'hey', 'start', 'menu']:
            return """Welcome to *LIFEXIA* - Your AI Health Assistant!

I can help you with:

1. *Drug Information* - Ask about any medicine
   Example: "Tell me about Paracetamol"

2. *Nearby Hospitals* - Find hospitals near you
   Send your location or type "hospitals near me"

3. *Emergency Help* - Quick emergency contacts
   Type "emergency" for immediate help

4. *Ayushman Card* - Find hospitals accepting PMJAY
   Type "ayushman hospitals"

How can I help you today?"""

        if query_lower in ['emergency', 'sos', 'help']:
            return """*EMERGENCY CONTACTS*

Call *108* for Ambulance (India)
Call *112* for General Emergency
Call *102* for Maternity Emergency

*Nearest Emergency Hospitals:*
- Civil Hospital: +91-79-22683721
- SAL Hospital: +91-79-40200200
- Star Hospital: +91-79-27560456

Stay calm and call emergency services immediately.

- LIFEXIA Emergency System"""

        if 'ayushman' in query_lower:
            return """*Ayushman Bharat Card Hospitals (Ahmedabad)*

1. Civil Hospital - All specialties (FREE)
2. SAL Hospital - Cardiac, Neuro, Ortho
3. Star Hospital - Multi-specialty
4. Zydus Hospital - Transplant, Oncology
5. Apollo Hospital - All specialties
6. KD Hospital - Multi-specialty

All these hospitals provide *cashless treatment* under AB-PMJAY.

Required Documents:
- Ayushman Bharat Card
- Aadhaar Card
- Valid ID Proof

- LIFEXIA Health Network"""

        # Use RAG service for drug queries
        rag_service = current_app.config.get('RAG_SERVICE')
        if rag_service:
            try:
                response = rag_service.query(query, user_type='patient')
                if response:
                    return response
            except Exception as e:
                logger.error(f"RAG query failed: {e}")

        # Default helpful response
        return f"""Thank you for your question about: *{query}*

I'm processing your request. Here's what I can help with:

- *Medicine info*: Ask "What is [medicine name]?"
- *Dosage*: Ask "Dosage for [medicine name]"
- *Side effects*: Ask "Side effects of [medicine name]"
- *Interactions*: Ask "Can I take [med1] with [med2]?"

Type *menu* to see all options.

- LIFEXIA Health Assistant"""

    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try again or call 108 for emergencies."
