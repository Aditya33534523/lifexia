from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/whatsapp')

# Verify token for Meta (Use this in the Meta Developer Portal)
VERIFY_TOKEN = "lifexia_webhook_verify_token_2024"

# This will be set from app.py
whatsapp_service = None

def init_webhook_service(service):
    """Initialize the WhatsApp service for webhooks"""
    global whatsapp_service
    whatsapp_service = service

@webhook_bp.route('/webhook', methods=['GET'])
def verify():
    """
    Meta webhook verification endpoint.
    Configure this in Meta Developer Console:
    - Callback URL: https://your-domain.com/api/whatsapp/webhook
    - Verify Token: lifexia_webhook_verify_token_2024
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("âœ… WhatsApp Webhook verified successfully!")
            return challenge, 200
        else:
            logger.warning("âŒ Webhook verification failed - invalid token")
            return "Forbidden", 403
    return "Not Found", 404

@webhook_bp.route('/webhook', methods=['POST'])
def handle_message():
    """
    Handle incoming WhatsApp messages.
    This endpoint receives messages from users and:
    1. Records the user message (opens 24h window)
    2. Processes the message
    3. Sends a response back
    """
    data = request.get_json()
    logger.info(f"ðŸ“¨ Received WhatsApp webhook: {data}")
    
    try:
        # Extract message data from WhatsApp webhook payload
        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    # Check if this is a message event
                    if 'messages' in value:
                        for message in value['messages']:
                            from_number = message.get('from')
                            message_type = message.get('type')
                            timestamp = message.get('timestamp')
                            
                            # Record that user messaged us (opens 24h window)
                            if whatsapp_service and from_number:
                                whatsapp_service.record_user_message(from_number)
                                logger.info(f"âœ… Recorded message from {from_number} - 24h window opened")
                            
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
                                logger.info(f"ðŸ“ Message from {from_number}: {message_content}")
                                
                                # TODO: Process message with your chatbot/RAG system
                                # Example: response = process_with_rag(message_content)
                                
                                # For now, send a simple acknowledgment
                                response_text = f"Thank you for your message! You said: {message_content}"
                                
                                # Send response (will use text since we just got a message from user)
                                if whatsapp_service:
                                    result = whatsapp_service.send_chat_response(
                                        from_number,
                                        response_text
                                    )
                                    logger.info(f"ðŸ“¤ Sent response to {from_number}: {result}")
                    
                    # Check for status updates (delivered, read, etc.)
                    if 'statuses' in value:
                        for status in value['statuses']:
                            message_id = status.get('id')
                            status_type = status.get('status')
                            logger.info(f"ðŸ“Š Message {message_id} status: {status_type}")
        
        return jsonify({"status": "received", "success": True}), 200
        
    except Exception as e:
        logger.error(f"âŒ Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500
