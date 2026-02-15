"""
WhatsApp Business API Service for LIFEXIA
Handles medication alerts, emergency notifications, and patient queries

FIXES APPLIED:
- Updated API version to v22.0 (matching Meta Developer Dashboard)
- Improved error handling with detailed error extraction
- Better template message support with components
- Added broadcast_template method for template-based broadcasts
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class WhatsAppService:
    """WhatsApp Business Cloud API Integration"""

    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = "v22.0"  # Updated to match Meta Developer Dashboard
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # In-memory user session tracking (use Redis in production)
        self.user_sessions = {}

        logger.info(f"✅ WhatsApp Service initialized (API {self.api_version}, Phone ID: {self.phone_number_id})")

    def _extract_error(self, exception):
        """Extract detailed error info from API response"""
        error_details = {"success": False, "error": str(exception)}

        if hasattr(exception, 'response') and exception.response is not None:
            try:
                error_data = exception.response.json()
                meta_error = error_data.get('error', {})
                error_details.update({
                    "error_code": meta_error.get('code'),
                    "error_subcode": meta_error.get('error_subcode'),
                    "error_message": meta_error.get('message'),
                    "error_type": meta_error.get('type'),
                    "fbtrace_id": meta_error.get('fbtrace_id'),
                    "meta_error": error_data
                })
            except Exception:
                error_details["response_text"] = exception.response.text[:500]

        return error_details

    def send_template_message(self, to_number: str, template_name: str,
                              language_code: str = "en_US",
                              components: Optional[List] = None) -> Dict[str, Any]:
        """
        Send WhatsApp template message
        Templates must be pre-approved in Meta Business Manager

        Args:
            to_number: Recipient phone number (format: 919876543210)
            template_name: Approved template name (e.g., 'hello_world')
            language_code: Language code (e.g., 'en_US', 'en')
            components: Template variables/components list
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": str(to_number).strip(),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }

        if components:
            payload["template"]["components"] = components

        try:
            logger.info(f"📤 Sending template '{template_name}' to {to_number}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()

            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')
            logger.info(f"✅ Template '{template_name}' sent to {to_number} (msg_id: {message_id})")

            return {
                "success": True,
                "message_id": message_id,
                "data": result
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Template send failed to {to_number}: {e}")
            return self._extract_error(e)

    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send plain text message
        Only works within 24-hour window after user's last message
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": str(to_number).strip(),
            "type": "text",
            "text": {"body": message[:4096]}  # WhatsApp max text length
        }

        try:
            logger.info(f"📤 Sending text message to {to_number} ({len(message)} chars)")

            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()

            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')
            logger.info(f"✅ Text message sent to {to_number} (msg_id: {message_id})")

            return {
                "success": True,
                "message_id": message_id,
                "data": result
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Text message failed to {to_number}: {e}")
            return self._extract_error(e)

    def send_medication_reminder(self, to_number: str, medication_name: str,
                                 dosage: str = '', time: str = '') -> Dict[str, Any]:
        """Send medication reminder via WhatsApp"""
        message = f"""🔔 *MEDICATION REMINDER*

💊 Medicine: {medication_name}
📋 Dosage: {dosage or 'As prescribed'}
⏰ Time: {time or 'Now'}

⚠️ Remember to take your medication as prescribed.

If you have any concerns, consult your doctor.

- LIFEXIA Health Assistant"""

        return self.send_text_message(to_number, message)

    def send_emergency_alert(self, to_number: str, alert_type: str = 'Health',
                              details: str = '', location: Optional[str] = None) -> Dict[str, Any]:
        """Send emergency health alert"""
        location_text = f"\n📍 Nearest Hospital: {location}" if location else ""

        message = f"""🚨 *EMERGENCY HEALTH ALERT*

Type: {alert_type}

{details}
{location_text}

⚠️ IMMEDIATE ACTION REQUIRED
📞 Call Emergency: 108 (India)

Stay calm and follow emergency protocols.

- LIFEXIA Emergency Alert System"""

        return self.send_text_message(to_number, message)

    def send_drug_safety_alert(self, to_number: str, drug_name: str,
                                safety_info: str) -> Dict[str, Any]:
        """Send drug safety alert notification"""
        message = f"""⚠️ *DRUG SAFETY ALERT*

Drug: {drug_name}

{safety_info}

🔴 IMPORTANT ACTIONS:
1. Consult your doctor immediately
2. Do NOT stop medication without medical advice
3. Report any adverse effects

For urgent concerns, call emergency services.

- LIFEXIA Safety Team"""

        return self.send_text_message(to_number, message)

    def send_hospital_directions(self, to_number: str, hospital_name: str,
                                  address: str, google_maps_link: str,
                                  distance: str = 'N/A', eta: str = 'N/A') -> Dict[str, Any]:
        """Send hospital directions"""
        message = f"""🗺️ *DIRECTIONS TO HOSPITAL*

🏥 {hospital_name}

📍 Address:
{address}

📏 Distance: {distance}
⏱️ Estimated Time: {eta}

🔗 Get Directions:
{google_maps_link}

For emergencies, call 108 for ambulance service.

- LIFEXIA Navigation"""

        return self.send_text_message(to_number, message)

    def send_ayushman_card_info(self, to_number: str, hospital_name: str,
                                 services: List[str] = None) -> Dict[str, Any]:
        """Send Ayushman Bharat card accepted hospital information"""
        services_list = "\n".join([f"• {service}" for service in (services or [])]) or "• General services available"

        message = f"""🏥 *AYUSHMAN BHARAT CARD ACCEPTED*

Hospital: {hospital_name}

This hospital accepts Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) cards for cashless treatment.

Available Services:
{services_list}

📋 Required Documents:
• Ayushman Bharat Card
• Valid ID proof
• Family member ID (if applicable)

For enrollment or card issues, visit nearest Common Service Centre.

- LIFEXIA Hospital Network"""

        return self.send_text_message(to_number, message)

    def send_maa_card_info(self, to_number: str, hospital_name: str) -> Dict[str, Any]:
        """Send MAA (Maternity Assistance) card information"""
        message = f"""👶 *MAA VATSALYA CARD ACCEPTED*

Hospital: {hospital_name}

This hospital accepts MAA Vatsalya cards for maternity and childcare services.

Covered Services:
• Prenatal care
• Delivery (normal & C-section)
• Postnatal care
• Newborn care

📋 Bring your MAA card and ID for cashless treatment.

- LIFEXIA Maternal Health Network"""

        return self.send_text_message(to_number, message)

    def broadcast_alert(self, phone_numbers: List[str], message: str) -> Dict[str, Any]:
        """
        Broadcast text alert to multiple users
        Note: Only works within 24h window for each recipient
        """
        results = {
            "total": len(phone_numbers),
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for number in phone_numbers:
            try:
                response = self.send_text_message(number, message)
                if response.get('success'):
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        "number": number,
                        "error": response.get('error'),
                        "error_code": response.get('error_code')
                    })
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    "number": number,
                    "error": str(e)
                })

        logger.info(f"Broadcast complete: {results['sent']}/{results['total']} sent")
        return results

    def record_user_message(self, from_number: str):
        """Record that user sent a message (opens 24-hour window)"""
        self.user_sessions[from_number] = {
            "last_message": datetime.now(),
            "window_open": True
        }
        logger.info(f"✅ 24-hour window opened for {from_number}")

    def can_send_message(self, to_number: str) -> bool:
        """Check if we can send a text message (within 24-hour window)"""
        if to_number not in self.user_sessions:
            return False

        user_session = self.user_sessions[to_number]
        time_since = datetime.now() - user_session['last_message']
        return time_since < timedelta(hours=24)

    def send_interactive_button_message(self, to_number: str, body_text: str,
                                         buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """Send interactive button message (max 3 buttons)"""
        payload = {
            "messaging_product": "whatsapp",
            "to": str(to_number).strip(),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn["id"],
                                "title": btn["title"][:20]  # Max 20 chars
                            }
                        } for btn in buttons[:3]
                    ]
                }
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Interactive message failed: {e}")
            return self._extract_error(e)

    def send_location_message(self, to_number: str, latitude: float,
                               longitude: float, name: str = '', address: str = '') -> Dict[str, Any]:
        """Send location pin"""
        payload = {
            "messaging_product": "whatsapp",
            "to": str(to_number).strip(),
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Location message failed: {e}")
            return self._extract_error(e)

    def get_session_status(self, phone_number: str) -> Dict[str, Any]:
        """Get current session status for a phone number"""
        if phone_number in self.user_sessions:
            user_session = self.user_sessions[phone_number]
            time_remaining = timedelta(hours=24) - (datetime.now() - user_session['last_message'])

            return {
                "window_open": time_remaining.total_seconds() > 0,
                "last_message": user_session['last_message'].isoformat(),
                "time_remaining": str(time_remaining) if time_remaining.total_seconds() > 0 else "0"
            }

        return {
            "window_open": False,
            "message": "No active session"
        }
