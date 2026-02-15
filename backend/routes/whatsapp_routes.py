"""
WhatsApp Routes for LIFEXIA
API endpoints for sending messages, reminders, alerts, and broadcasts
"""

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
                'error': 'WhatsApp service not configured. Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env'
            }), 503

        result = whatsapp_service.send_text_message(to_number, message)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Send message error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/send-template', methods=['POST'])
def send_template():
    """Send a pre-approved WhatsApp template message"""
    try:
        data = request.json
        to_number = data.get('to_number')
        template_name = data.get('template_name')
        language = data.get('language', 'en')
        components = data.get('components')

        if not to_number or not template_name:
            return jsonify({
                'success': False,
                'error': 'Phone number and template name required'
            }), 400

        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        result = whatsapp_service.send_template_message(
            to_number, template_name, language, components
        )
        return jsonify(result)

    except Exception as e:
        logger.error(f"Template send error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/medication-reminder', methods=['POST'])
def send_medication_reminder():
    """Send medication reminder"""
    try:
        data = request.json
        to_number = data.get('to_number')
        medication = data.get('medication_name')
        dosage = data.get('dosage')
        time = data.get('time')

        if not to_number or not medication:
            return jsonify({'success': False, 'error': 'Number and medication name required'}), 400

        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        result = whatsapp_service.send_medication_reminder(to_number, medication, dosage, time)
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
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        result = whatsapp_service.send_emergency_alert(to_number, alert_type, details, location)
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
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

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
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        result = whatsapp_service.send_ayushman_card_info(to_number, hospital_name, services)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Ayushman info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/broadcast', methods=['POST'])
def broadcast_alert():
    """
    Broadcast alert to multiple users.
    Supports both template messages and custom text messages.
    
    Payload options:
    1. Template broadcast:
       { "numbers": [...], "template_name": "hello_world", "components": [...] }
    2. Custom text broadcast:
       { "numbers": [...], "message": "Your message here" }
    3. Legacy format:
       { "phone_numbers": [...], "message": "..." }
    """
    try:
        data = request.json
        # Support both 'numbers' and 'phone_numbers' keys
        phone_numbers = data.get('numbers') or data.get('phone_numbers', [])
        template_name = data.get('template_name')
        components = data.get('components')
        message = data.get('message')

        if not phone_numbers:
            return jsonify({
                'success': False,
                'error': 'Phone numbers required'
            }), 400

        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        if not whatsapp_service:
            return jsonify({
                'success': False,
                'error': 'WhatsApp service not configured. Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env'
            }), 503

        results = {
            "total": len(phone_numbers),
            "sent": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }

        for number in phone_numbers:
            try:
                if template_name and template_name != 'custom_text':
                    # Send template message (works outside 24h window)
                    result = whatsapp_service.send_template_message(
                        number, template_name, 'en', components
                    )
                elif message:
                    # Send custom text (only within 24h window)
                    result = whatsapp_service.send_text_message(number, message)
                else:
                    result = {'success': False, 'error': 'No message or template specified'}

                if result.get('success'):
                    results['sent'] += 1
                    results['details'].append({
                        'number': number,
                        'status': 'sent',
                        'message_id': result.get('message_id')
                    })
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'number': number,
                        'error': result.get('error', 'Unknown error'),
                        'error_code': result.get('error_code')
                    })
                    results['details'].append({
                        'number': number,
                        'status': 'failed',
                        'error': result.get('error')
                    })

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'number': number,
                    'error': str(e)
                })

        logger.info(f"Broadcast complete: {results['sent']}/{results['total']} sent")

        return jsonify({
            'success': results['sent'] > 0,
            'broadcast_result': results
        })

    except Exception as e:
        logger.error(f"Broadcast error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/send-location', methods=['POST'])
def send_location():
    """Send location pin via WhatsApp"""
    try:
        data = request.json
        to_number = data.get('to_number')
        lat = data.get('latitude') or data.get('lat')
        lng = data.get('longitude') or data.get('lng')
        name = data.get('name', '')
        address = data.get('address', '')

        if not to_number or not lat or not lng:
            return jsonify({'success': False, 'error': 'Number and coordinates required'}), 400

        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        result = whatsapp_service.send_location_message(to_number, lat, lng, name, address)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Send location error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/session-status/<phone_number>', methods=['GET'])
def get_session_status(phone_number):
    """Check WhatsApp session status for a number"""
    try:
        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        status = whatsapp_service.get_session_status(phone_number)
        return jsonify({
            'success': True,
            'status': status
        })

    except Exception as e:
        logger.error(f"Session status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/interactive-buttons', methods=['POST'])
def send_interactive_buttons():
    """Send interactive button message"""
    try:
        data = request.json
        to_number = data.get('to_number')
        body_text = data.get('body_text')
        buttons = data.get('buttons', [])

        if not to_number or not body_text or not buttons:
            return jsonify({'success': False, 'error': 'Number, body text, and buttons required'}), 400

        whatsapp_service = current_app.config.get('WHATSAPP_SERVICE')
        if not whatsapp_service:
            return jsonify({'success': False, 'error': 'WhatsApp service unavailable'}), 503

        result = whatsapp_service.send_interactive_button_message(to_number, body_text, buttons)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Interactive buttons error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
