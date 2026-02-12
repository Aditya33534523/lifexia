from flask import Blueprint, request, jsonify
from backend.services.chat_store import append_message
from backend.services.rag_service import get_rag_service

WELCOME_MESSAGE = "Welcome to LifeXia! I'm your intelligent pharmacy assistant. How can I help you today?"
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

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
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    user_email = data.get('user_email', 'guest@lifexia.local')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    conversation = append_message(user_email, 'user', message, data.get('session_id'))
    
    # Get response from RAG service
    rag_service = get_rag_service()
    response_text = rag_service.query(message)
    
    append_message(user_email, 'assistant', response_text, conversation['session_id'])
    
    return jsonify({
        'response': response_text,
        'session_id': conversation['session_id'],
    }), 200
