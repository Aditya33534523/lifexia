from flask import Blueprint, request, jsonify
from backend.services.whatsapp_service import WhatsAppService
from backend.config import Config

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')
whatsapp_service = WhatsAppService()

@whatsapp_bp.route('/test', methods=['GET'])
def test_config():
    return jsonify(whatsapp_service.test_config()), 200

@whatsapp_bp.route('/send-template', methods=['POST'])
def send_template():
    data = request.get_json()
    to_number = data.get('to_number')
    template_name = data.get('template_name', 'hello_world')
    language_code = data.get('language_code', 'en_US')
    
    if not to_number:
        return jsonify({"error": "Missing to_number", "success": False}), 400
        
    result = whatsapp_service.send_template_message(to_number, template_name, language_code)
    return jsonify(result), 200

@whatsapp_bp.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    to_number = data.get('to_number')
    message = data.get('message')
    
    if not to_number or not message:
        return jsonify({"error": "Missing to_number or message", "success": False}), 400
        
    result = whatsapp_service.send_text_message(to_number, message)
    return jsonify(result), 200

@whatsapp_bp.route('/broadcast', methods=['POST'])
def broadcast():
    """Sends a message to multiple recipients."""
    data = request.get_json()
    numbers = data.get('numbers', [])
    message = data.get('message')
    template = data.get('template_name')
    components = data.get('components') # Dynamic variables
    
    if not numbers:
        return jsonify({"error": "Missing numbers", "success": False}), 400
        
    results = whatsapp_service.send_broadcast(
        numbers, 
        template_name=template, 
        components=components,
        message_text=message
    )
    return jsonify({"success": True, "results": results}), 200

@whatsapp_bp.route('/quick-send', methods=['POST'])
def quick_send():
    """Testing endpoint for hello_world template."""
    to_number = Config.ADMIN_WHATSAPP_NUMBER
    if not to_number:
        return jsonify({"error": "ADMIN_WHATSAPP_NUMBER not configured", "success": False}), 400
        
    result = whatsapp_service.send_template_message(to_number, 'hello_world')
    return jsonify(result), 200
