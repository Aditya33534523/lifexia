from flask import Blueprint, jsonify

from backend.services.chat_store import delete_conversation, get_conversation, list_history

history_bp = Blueprint('history', __name__, url_prefix='/api/history')


@history_bp.route('/<path:user_email>', methods=['GET'])
def get_history(user_email):
    return jsonify(list_history(user_email)), 200


@history_bp.route('/conversation/<session_id>', methods=['GET'])
def get_conversation_details(session_id):
    conversation = get_conversation(session_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found', 'messages': []}), 404

    return jsonify({'session_id': session_id, 'messages': conversation['messages']}), 200


@history_bp.route('/delete/<int:conversation_id>', methods=['DELETE'])
def remove_conversation(conversation_id):
    deleted = delete_conversation(conversation_id)
    if not deleted:
        return jsonify({'error': 'Conversation not found'}), 404
    return jsonify({'deleted': True}), 200
