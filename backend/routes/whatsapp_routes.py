from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')

# Import will be done in app.py: from backend.services.whatsapp_service import WhatsAppService
# whatsapp_service = WhatsAppService(access_token, phone_number_id)

# This will be initialized in app.py with actual service
whatsapp_service = None

def init_whatsapp_service(service):
    """Initialize the WhatsApp service (called from app.py)"""
    global whatsapp_service
    whatsapp_service = service

@whatsapp_bp.route('/test', methods=['GET'])
def test_config():
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
    return jsonify(whatsapp_service.test_config()), 200

@whatsapp_bp.route('/send-template', methods=['POST'])
def send_template():
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
        
    data = request.get_json()
    to_number = data.get('to_number')
    template_name = data.get('template_name', 'hello_world')
    language_code = data.get('language_code', 'en_US')
    components = data.get('components')
    
    if not to_number:
        return jsonify({"error": "Missing to_number", "success": False}), 400
        
    result = whatsapp_service.send_template_message(to_number, template_name, components, language_code)
    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code

@whatsapp_bp.route('/send-message', methods=['POST'])
def send_message():
    """
    Send a text message (only works within 24h window).
    For chatbot responses, use /send-chat instead which has smart fallback.
    """
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
        
    data = request.get_json()
    to_number = data.get('to_number')
    message = data.get('message')
    
    if not to_number or not message:
        return jsonify({"error": "Missing to_number or message", "success": False}), 400
        
    result = whatsapp_service.send_text_message(to_number, message)
    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code

@whatsapp_bp.route('/send-chat', methods=['POST'])
def send_chat():
    """
    Smart send for chatbot responses.
    Tries text message first, falls back to template if user hasn't messaged in 24h.
    
    Request body:
    {
        "to_number": "919824794027",
        "message": "Your prescription is ready!",
        "fallback_template": "hello_world"  // optional
    }
    """
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
        
    data = request.get_json()
    to_number = data.get('to_number')
    message = data.get('message')
    fallback_template = data.get('fallback_template', 'hello_world')
    
    if not to_number or not message:
        return jsonify({"error": "Missing to_number or message", "success": False}), 400
        
    result = whatsapp_service.send_chat_response(to_number, message, fallback_template)
    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code

@whatsapp_bp.route('/broadcast', methods=['POST'])
def broadcast():
    """
    Sends a message to multiple recipients.
    
    Request body:
    {
        "numbers": ["919824794027", "918888888888"],
        "template_name": "hello_world",  // optional
        "components": [...],              // optional
        "message": "Text message"        // optional, requires template_name to be null
    }
    """
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
        
    data = request.get_json()
    numbers = data.get('numbers', [])
    message = data.get('message')
    template = data.get('template_name')
    components = data.get('components')
    
    if not numbers:
        return jsonify({"error": "Missing numbers array", "success": False}), 400
        
    results = whatsapp_service.send_broadcast(
        numbers, 
        template_name=template, 
        components=components,
        message_text=message
    )
    return jsonify(results), 200

@whatsapp_bp.route('/quick-send', methods=['POST'])
def quick_send():
    """Testing endpoint for hello_world template."""
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
        
    # You can configure this test number in .env as ADMIN_WHATSAPP_NUMBER
    data = request.get_json() or {}
    to_number = data.get('to_number', '919824794027')  # Default test number
        
    result = whatsapp_service.send_template_message(to_number, 'hello_world')
    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code

@whatsapp_bp.route('/check-window/<phone_number>', methods=['GET'])
def check_window(phone_number):
    """Check if a phone number is within the 24-hour messaging window"""
    if not whatsapp_service:
        return jsonify({"error": "WhatsApp service not initialized", "success": False}), 500
        
    is_within = whatsapp_service.is_within_24h_window(phone_number)
    return jsonify({
        "phone_number": phone_number,
        "within_24h_window": is_within,
        "can_send_text": is_within,
        "must_use_template": not is_within
    }), 200