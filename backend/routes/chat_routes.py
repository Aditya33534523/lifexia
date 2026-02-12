from flask import Blueprint, request, jsonify
from backend.services.chat_store import append_message
from backend.services.rag_service import get_rag_service

WELCOME_MESSAGE = "Welcome to LifeXia! I'm your intelligent pharmacy assistant. How can I help you today?"
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# This will be set from app.py
whatsapp_service = None

def init_chat_whatsapp(service):
    """Initialize WhatsApp service for chat"""
    global whatsapp_service
    whatsapp_service = service

@chat_bp.route('/init', methods=['POST'])
def init_chat():
    data = request.get_json(silent=True) or {}
    user_email = data.get('user_email', 'guest@lifexia.local')
    conversation = append_message(user_email, 'assistant', WELCOME_MESSAGE, data.get('session_id'))
    return jsonify({
        'session_id': conversation['session_id'],
        'welcome_message': WELCOME_MESSAGE,
        'messages': conversation['messages'],
    }), 200

@chat_bp.route('/send',methods=['POST'])
@chat_bp.route('/message', methods=['POST'])
def handle_message():
    """
    Handle chat messages and optionally send to WhatsApp.
    
    Request body:
    {
        "message": "What is the dosage for aspirin?",
        "user_email": "user@example.com",
        "session_id": "session_abc123",
        "whatsapp_number": "919824794027",  // optional
        "send_whatsapp": true                // optional
    }
    """
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    user_email = data.get('user_email', 'guest@lifexia.local')
    whatsapp_number = data.get('whatsapp_number')
    send_whatsapp = data.get('send_whatsapp', False)

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Store user message
    conversation = append_message(user_email, 'user', message, data.get('session_id'))
    
    # Get response from RAG service
    rag_service = get_rag_service()
    response_text = rag_service.query(message)
    
    # Store assistant response
    append_message(user_email, 'assistant', response_text, conversation['session_id'])
    
    # Optionally send response via WhatsApp
    whatsapp_result = None
    if send_whatsapp and whatsapp_number and whatsapp_service:
        whatsapp_result = whatsapp_service.send_chat_response(
            whatsapp_number,
            response_text
        )
    
    response = {
        'response': response_text,
        'session_id': conversation['session_id'],
    }
    
    if whatsapp_result:
        response['whatsapp'] = {
            'sent': whatsapp_result.get('success', False),
            'method': whatsapp_result.get('method'),
            'fallback_used': whatsapp_result.get('fallback_used', False)
        }
    
    return jsonify(response), 200

@chat_bp.route('/send-to-whatsapp', methods=['POST'])
def send_to_whatsapp():
    """
    Send a specific message to WhatsApp (useful for sharing chat responses).
    
    Request body:
    {
        "to_number": "919824794027",
        "message": "Your prescription details: ...",
        "session_id": "session_abc123"  // optional, for logging
    }
    """
    if not whatsapp_service:
        return jsonify({
            'error': 'WhatsApp service not configured',
            'success': False
        }), 500
    
    data = request.get_json(silent=True) or {}
    to_number = data.get('to_number')
    message = data.get('message')
    
    if not to_number or not message:
        return jsonify({
            'error': 'Both to_number and message are required',
            'success': False
        }), 400
    
    result = whatsapp_service.send_chat_response(to_number, message)
    status_code = 200 if result.get('success') else 500
    
    return jsonify(result), status_code