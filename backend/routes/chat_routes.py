"""
Chat Routes for LIFEXIA
Handles user queries about medications with RAG-based responses
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/query', methods=['POST'])
def process_chat_query():
    """
    Process user chat query about medications
    Returns accurate drug information using RAG
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_type = data.get('user_type', 'patient')  # 'patient' or 'student'
        user_id = session.get('user_id', 'anonymous')
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Get RAG service
        rag_service = current_app.config.get('RAG_SERVICE')
        
        if not rag_service:
            return jsonify({
                'success': False,
                'error': 'Chat service is temporarily unavailable'
            }), 503
        
        # Get chat history for context
        chat_history = session.get('chat_history', [])
        context = '\n'.join([
            f"User: {msg['user']}\nAssistant: {msg['assistant']}"
            for msg in chat_history[-3:]  # Last 3 messages
        ])
        
        # Process query with RAG
        response_text = rag_service.query(
            question=user_message,
            user_type=user_type,
            context=context
        )
        
        # Update chat history
        chat_entry = {
            'user': user_message,
            'assistant': response_text,
            'timestamp': datetime.now().isoformat(),
            'user_type': user_type
        }
        
        chat_history.append(chat_entry)
        session['chat_history'] = chat_history[-10:]  # Keep last 10 messages
        
        return jsonify({
            'success': True,
            'response': response_text,
            'timestamp': datetime.now().isoformat(),
            'message_id': len(chat_history)
        })
        
    except Exception as e:
        logger.error(f"Chat query error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An error occurred processing your request'
        }), 500

@chat_bp.route('/drug-search', methods=['POST'])
def search_drug():
    """Direct drug database search"""
    try:
        data = request.json
        drug_name = data.get('drug_name', '').strip()
        
        if not drug_name:
            return jsonify({
                'success': False,
                'error': 'Drug name is required'
            }), 400
        
        rag_service = current_app.config.get('RAG_SERVICE')
        
        if not rag_service:
            return jsonify({
                'success': False,
                'error': 'Service temporarily unavailable'
            }), 503
        
        # Search drug directly
        drug_info = rag_service.search_drug(drug_name)
        
        if drug_info:
            user_type = data.get('user_type', 'patient')
            formatted_response = rag_service._format_response_for_user(drug_info, user_type)
            
            return jsonify({
                'success': True,
                'found': True,
                'drug_info': drug_info,
                'formatted_response': formatted_response
            })
        else:
            return jsonify({
                'success': True,
                'found': False,
                'message': f'No information found for "{drug_name}". Please check the spelling or try a different drug name.'
            })
            
    except Exception as e:
        logger.error(f"Drug search error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500

@chat_bp.route('/emergency-drugs', methods=['GET'])
def get_emergency_drugs():
    """Get list of common emergency medications"""
    try:
        rag_service = current_app.config.get('RAG_SERVICE')
        
        if not rag_service:
            return jsonify({
                'success': False,
                'error': 'Service unavailable'
            }), 503
        
        drug_list = rag_service.get_emergency_drugs_list()
        categories = rag_service.get_drug_categories()
        
        return jsonify({
            'success': True,
            'drugs': drug_list,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Emergency drugs error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve drug list'
        }), 500

@chat_bp.route('/history', methods=['GET'])
def get_chat_history():
    """Get user's chat history"""
    try:
        chat_history = session.get('chat_history', [])
        
        return jsonify({
            'success': True,
            'history': chat_history,
            'count': len(chat_history)
        })
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve history'
        }), 500

@chat_bp.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear chat history"""
    try:
        session['chat_history'] = []
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        })
        
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear history'
        }), 500

@chat_bp.route('/quick-info/<drug_name>', methods=['GET'])
def quick_drug_info(drug_name):
    """Get quick drug information (for emergency use)"""
    try:
        rag_service = current_app.config.get('RAG_SERVICE')
        
        if not rag_service:
            return jsonify({
                'success': False,
                'error': 'Service unavailable'
            }), 503
        
        drug_info = rag_service.search_drug(drug_name)
        
        if drug_info:
            # Return essential info only
            quick_info = {
                'name': drug_info['name'],
                'generic': drug_info['generic'],
                'dosage': drug_info['dosage'],
                'warnings': drug_info['warning'],
                'use': drug_info['use']
            }
            
            return jsonify({
                'success': True,
                'drug': quick_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Drug not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Quick info error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve information'
        }), 500

@chat_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback on chatbot response"""
    try:
        data = request.json
        message_id = data.get('message_id')
        rating = data.get('rating')  # 1-5
        comment = data.get('comment', '')
        
        # Store feedback (implement database storage)
        feedback_entry = {
            'message_id': message_id,
            'rating': rating,
            'comment': comment,
            'timestamp': datetime.now().isoformat(),
            'user_id': session.get('user_id', 'anonymous')
        }
        
        logger.info(f"Feedback received: {feedback_entry}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit feedback'
        }), 500