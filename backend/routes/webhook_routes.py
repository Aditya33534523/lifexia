from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/webhook')

# Verify token for Meta (Use this in the Meta Developer Portal)
VERIFY_TOKEN = "lifexia_secure_token_123"

@webhook_bp.route('/whatsapp', methods=['GET'])
def verify():
    # Meta verification logic
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("WhatsApp Webhook verified successfully!")
            return challenge, 200
        else:
            return "Forbidden", 403
    return "Not Found", 404

@webhook_bp.route('/whatsapp', methods=['POST'])
def handle_message():
    # Handle incoming WhatsApp messages
    data = request.get_json()
    logger.info(f"Received WhatsApp message: {data}")
    
    # You can extend this to process user messages and reply automatically
    return jsonify({"status": "received"}), 200
