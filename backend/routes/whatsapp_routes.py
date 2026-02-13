
from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/send-message', methods=['POST'])
def send_message():
    """Send text message to user"""
    try:
        data = request.json
        to_number = data.get('to_number')
        message = data.get('message')
        
        if not to_number or not message:
            return jsonify({
                'success': False,
                'error': 'Phone number and message required'
            }), 400
        
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        
        if not whatsapp_service:
            return jsonify({
                'success': False,
                'error': 'WhatsApp service unavailable'
            }), 503
        
        result = whatsapp_service.send_text_message(to_number, message)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@whatsapp_bp.route('/medication-reminder', methods=['POST'])
def send_medication_reminder():
    """Send medication reminder"""
    try:
        data = request.json
        to_number = data.get('to_number')
        medication = data.get('medication_name')
        dosage = data.get('dosage')
        time = data.get('time')
        
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        result = whatsapp_service.send_medication_reminder(
            to_number, medication, dosage, time
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Medication reminder error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@whatsapp_bp.route('/emergency-alert', methods=['POST'])
def send_emergency_alert():
    """Send emergency health alert"""
    try:
        data = request.json
        to_number = data.get('to_number')
        alert_type = data.get('alert_type')
        details = data.get('details')
        location = data.get('location')
        
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        result = whatsapp_service.send_emergency_alert(
            to_number, alert_type, details, location
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Emergency alert error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@whatsapp_bp.route('/hospital-directions', methods=['POST'])
def send_hospital_directions():
    """Send hospital directions via WhatsApp"""
    try:
        data = request.json
        to_number = data.get('to_number')
        hospital_name = data.get('hospital_name')
        address = data.get('address')
        maps_link = data.get('google_maps_link')
        distance = data.get('distance', 'N/A')
        eta = data.get('eta', 'N/A')
        
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        result = whatsapp_service.send_hospital_directions(
            to_number, hospital_name, address, maps_link, distance, eta
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Directions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@whatsapp_bp.route('/ayushman-info', methods=['POST'])
def send_ayushman_info():
    """Send Ayushman card facility information"""
    try:
        data = request.json
        to_number = data.get('to_number')
        hospital_name = data.get('hospital_name')
        services = data.get('services', [])
        
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        result = whatsapp_service.send_ayushman_card_info(
            to_number, hospital_name, services
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ayushman info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@whatsapp_bp.route('/broadcast', methods=['POST'])
def broadcast_alert():
    """Broadcast alert to multiple users"""
    try:
        data = request.json
        phone_numbers = data.get('phone_numbers', [])
        message = data.get('message')
        
        if not phone_numbers or not message:
            return jsonify({
                'success': False,
                'error': 'Phone numbers and message required'
            }), 400
        
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        result = whatsapp_service.broadcast_alert(phone_numbers, message)
        
        return jsonify({
            'success': True,
            'broadcast_result': result
        })
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@whatsapp_bp.route('/session-status/<phone_number>', methods=['GET'])
def get_session_status(phone_number):
    """Check WhatsApp session status for a number"""
    try:
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        status = whatsapp_service.get_session_status(phone_number)
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Session status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
EOFWA
cat > backend/routes/webhook_routes.py << 'EOFWH'
"""
Webhook Routes for LIFEXIA WhatsApp Integration
Handles incoming messages from WhatsApp users
"""

from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)
whatsapp_service_ref = None

VERIFY_TOKEN = "lifexia_webhook_verify_2024"

def init_webhook_service(service):
    """Initialize WhatsApp service reference"""
    global whatsapp_service_ref
    whatsapp_service_ref = service
    logger.info("Webhook service initialized")

@webhook_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify webhook with Meta"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully")
            return challenge, 200
        else:
            logger.warning("❌ Webhook verification failed")
            return "Forbidden", 403
    
    return "Not Found", 404

@webhook_bp.route('/webhook', methods=['POST'])
def handle_incoming_message():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.json
        logger.info(f"📨 Webhook received: {data}")
        
        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    if 'messages' in value:
                        for message in value['messages']:
                            from_number = message.get('from')
                            message_type = message.get('type')
                            
                            # Record user message (opens 24h window)
                            if whatsapp_service_ref and from_number:
                                whatsapp_service_ref.record_user_message(from_number)
                            
                            # Extract message content
                            content = None
                            if message_type == 'text':
                                content = message.get('text', {}).get('body')
                            
                            if content:
                                logger.info(f"📝 Message from {from_number}: {content}")
                                
                                # Process with chatbot
                                response = process_user_query(content, from_number)
                                
                                # Send response
                                if whatsapp_service_ref and response:
                                    whatsapp_service_ref.send_text_message(from_number, response)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({'status': 'error'}), 500

def process_user_query(query: str, phone_number: str) -> str:
    """Process user query and generate response"""
    try:
        # Get RAG service for drug information
        rag_service = current_app.config.get('RAG_SERVICE')
        
        if rag_service:
            response = rag_service.query(query, user_type='patient')
            return response
        else:
            return """Hello! I'm LIFEXIA, your healthcare assistant.

I can help you with:
• Medication information
• Nearby hospitals & pharmacies
• Emergency assistance

How can I help you today?"""
            
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try again or contact emergency services if urgent."
EOFWH
cat > backend/routes/auth_routes.py << 'EOFAU'
"""
Authentication Routes for LIFEXIA
Simple session-based authentication
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Simple in-memory user storage (use database in production)
users_db = {}

@auth_bp.route('/login', methods=['POST'])
def login():
    """Simple login/session creation"""
    try:
        data = request.json
        phone_number = data.get('phone_number')
        name = data.get('name', 'User')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number required'
            }), 400
        
        # Create or get user
        user_id = phone_number
        if user_id not in users_db:
            users_db[user_id] = {
                'id': user_id,
                'name': name,
                'phone': phone_number,
                'created_at': datetime.now().isoformat(),
                'preferences': {
                    'user_type': 'patient'
                }
            }
        
        # Create session
        session['user_id'] = user_id
        session['logged_in'] = True
        session['user_name'] = users_db[user_id]['name']
        
        return jsonify({
            'success': True,
            'user': users_db[user_id],
            'session_id': request.cookies.get('session')
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@auth_bp.route('/session', methods=['GET'])
def get_session():
    """Get current session info"""
    if session.get('logged_in'):
        user_id = session.get('user_id')
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': users_db.get(user_id, {})
        })
    else:
        return jsonify({
            'success': True,
            'logged_in': False
        })

@auth_bp.route('/preferences', methods=['POST'])
def update_preferences():
    """Update user preferences"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'error': 'Not logged in'
            }), 401
        
        data = request.json
        user_id = session.get('user_id')
        
        if user_id in users_db:
            users_db[user_id]['preferences'].update(data)
            
            return jsonify({
                'success': True,
                'preferences': users_db[user_id]['preferences']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Preferences update error: {e}")
        return jsonify({
            'success': False,
            'error': 'Update failed'
        }), 500