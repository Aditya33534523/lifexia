"""
Chat Routes for LIFEXIA
Handles user queries about medications with RAG-based responses
Supports both /query (chat.html) and /message (index.html) endpoints
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/init', methods=['POST'])
def init_chat():
    """Initialize chat session"""
    try:
        data = request.json or {}
        user_email = data.get('user_email', 'anonymous')

        session_id = session.get('chat_session_id') or str(uuid.uuid4())
        session['chat_session_id'] = session_id

        return jsonify({
            'success': True,
            'session_id': session_id,
            'welcome_message': "Welcome to **LIFEXIA**! I'm your AI-powered health assistant.\n\nI can help you with:\n- **Drug Information** - Dosages, side effects, interactions\n- **Nearby Hospitals** - Use the Health Grid map above\n- **Emergency Help** - Quick access to emergency contacts\n- **WhatsApp Support** - Toggle 'Send to WhatsApp' below\n\nHow can I assist you today?"
        })
    except Exception as e:
        logger.error(f"Chat init error: {e}")
        return jsonify({
            'success': True,
            'session_id': 'default',
            'welcome_message': 'Welcome to LIFEXIA! How can I help you today?'
        })


@chat_bp.route('/message', methods=['POST'])
def process_chat_message():
    """
    Process user chat message from index.html (main interface)
    This is the primary endpoint used by the modern UI
    Returns accurate drug information using RAG + built-in drug database
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_email = data.get('user_email', 'anonymous')
        incoming_session_id = data.get('session_id')
        send_whatsapp = data.get('send_whatsapp', False)
        whatsapp_number = data.get('whatsapp_number', '')

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        # Get or create session ID
        session_id = incoming_session_id or session.get('chat_session_id') or str(uuid.uuid4())
        session['chat_session_id'] = session_id

        # Get RAG service
        rag_service = current_app.config.get('RAG_SERVICE')

        if not rag_service:
            return jsonify({
                'success': False,
                'response': 'Chat service is temporarily unavailable. Please try again shortly.',
                'session_id': session_id
            }), 503

        # Determine user type from session or default
        user_type = session.get('user_type', 'patient')

        # Process query with RAG service (includes built-in drug database)
        response_text = rag_service.query(
            question=user_message,
            user_type=user_type,
            context=''
        )

        # Store in chat history via chat_store if available
        try:
            from backend.services.chat_store import get_or_create_conversation, append_message
            conv = get_or_create_conversation(user_email, session_id)
            append_message(user_email, session_id, 'user', user_message)
            append_message(user_email, session_id, 'assistant', response_text)
        except ImportError:
            logger.debug("chat_store not available, using session-based history")
            # Fallback to session-based history
            chat_history = session.get('chat_history', [])
            chat_history.append({
                'user': user_message,
                'assistant': response_text,
                'timestamp': datetime.now().isoformat()
            })
            session['chat_history'] = chat_history[-20:]

        # Handle WhatsApp forwarding if requested
        whatsapp_result = None
        if send_whatsapp and whatsapp_number:
            try:
                whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
                if whatsapp_service:
                    # Clean markdown for WhatsApp
                    wa_text = response_text.replace('##', '').replace('**', '*').replace('---', '')
                    wa_result = whatsapp_service.send_text_message(whatsapp_number, wa_text[:4096])
                    whatsapp_result = {
                        'sent': wa_result.get('success', False),
                        'message_id': wa_result.get('message_id')
                    }
                else:
                    whatsapp_result = {
                        'sent': False,
                        'error': 'WhatsApp service not configured'
                    }
            except Exception as wa_err:
                logger.error(f"WhatsApp send error: {wa_err}")
                whatsapp_result = {'sent': False, 'error': str(wa_err)}

        result = {
            'success': True,
            'response': response_text,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }

        if whatsapp_result:
            result['whatsapp'] = whatsapp_result

        return jsonify(result)

    except Exception as e:
        logger.error(f"Chat message error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'response': 'Sorry, I encountered an error processing your request. Please try again.',
            'error': str(e)
        }), 500


@chat_bp.route('/query', methods=['POST'])
def process_chat_query():
    """
    Process user chat query from chat.html (legacy/alternative interface)
    Returns accurate drug information using RAG
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_type = data.get('user_type', 'patient')

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

        # Process query with RAG
        response_text = rag_service.query(
            question=user_message,
            user_type=user_type,
            context=''
        )

        # Update session chat history
        chat_history = session.get('chat_history', [])
        chat_history.append({
            'user': user_message,
            'assistant': response_text,
            'timestamp': datetime.now().isoformat(),
            'user_type': user_type
        })
        session['chat_history'] = chat_history[-10:]

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

        drug_info = rag_service.search_drug(drug_name)

        if drug_info:
            user_type = data.get('user_type', 'patient')
            formatted_response = rag_service._format_drug_response(drug_info, user_type)

            return jsonify({
                'success': True,
                'found': True,
                'drug_info': {
                    'name': drug_info['name'],
                    'category': drug_info['category'],
                    'use': drug_info['use']
                },
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
        return jsonify({'success': False, 'error': 'Failed to retrieve history'}), 500


@chat_bp.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear chat history"""
    try:
        session['chat_history'] = []
        return jsonify({'success': True, 'message': 'Chat history cleared'})
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear history'}), 500


@chat_bp.route('/quick-info/<drug_name>', methods=['GET'])
def quick_drug_info(drug_name):
    """Get quick drug information (for emergency use)"""
    try:
        rag_service = current_app.config.get('RAG_SERVICE')

        if not rag_service:
            return jsonify({'success': False, 'error': 'Service unavailable'}), 503

        drug_info = rag_service.search_drug(drug_name)

        if drug_info:
            quick_info = {
                'name': drug_info['name'],
                'generic': drug_info['generic'],
                'dosage': drug_info['dosage'],
                'warnings': drug_info['warning'],
                'use': drug_info['use']
            }
            return jsonify({'success': True, 'drug': quick_info})
        else:
            return jsonify({'success': False, 'error': 'Drug not found'}), 404

    except Exception as e:
        logger.error(f"Quick info error: {e}")
        return jsonify({'success': False, 'error': 'Failed to retrieve information'}), 500
