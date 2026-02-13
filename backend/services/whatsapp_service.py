"""
WhatsApp Business API Service for LIFEXIA
Handles medication alerts, emergency notifications, and patient queries
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
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # In-memory user session tracking (use Redis in production)
        self.user_sessions = {}
        
        logger.info("✅ WhatsApp Service initialized")
    
    def send_template_message(self, to_number: str, template_name: str, 
                            language_code: str = "en", 
                            components: Optional[List] = None) -> Dict[str, Any]:
        """
        Send WhatsApp template message
        Templates must be pre-approved in Meta Business Manager
        
        Args:
            to_number: Recipient phone number (format: 919876543210)
            template_name: Approved template name
            language_code: Language code (e.g., 'en', 'en_US')
            components: Template variables/components
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Template '{template_name}' sent to {to_number}")
            
            return {
                "success": True,
                "message_id": result.get('messages', [{}])[0].get('id'),
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Template send failed: {e}")
            error_details = {"success": False, "error": str(e)}
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_details.update({
                        "error_code": error_data.get('error', {}).get('code'),
                        "error_message": error_data.get('error', {}).get('message'),
                        "meta_error": error_data
                    })
                except:
                    error_details["response_text"] = e.response.text
            
            return error_details
    
    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send plain text message
        Only works within 24-hour window after user message
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Text message sent to {to_number}")
            
            return {
                "success": True,
                "message_id": result.get('messages', [{}])[0].get('id'),
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Text message failed: {e}")
            return {"success": False, "error": str(e)}
    
    def send_medication_reminder(self, to_number: str, medication_name: str, 
                                dosage: str, time: str) -> Dict[str, Any]:
        """Send medication reminder via WhatsApp"""
        
        message = f"""🔔 **MEDICATION REMINDER**

💊 Medicine: {medication_name}
📋 Dosage: {dosage}
⏰ Time: {time}

⚠️ Remember to take your medication as prescribed.

If you have any concerns, consult your doctor.

- LIFEXIA Health Assistant"""
        
        return self.send_text_message(to_number, message)
    
    def send_emergency_alert(self, to_number: str, alert_type: str, 
                           details: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Send emergency health alert"""
        
        location_text = f"\n📍 Nearest Hospital: {location}" if location else ""
        
        message = f"""🚨 **EMERGENCY HEALTH ALERT**

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
        
        message = f"""⚠️ **DRUG SAFETY ALERT**

Drug: {drug_name}

{safety_info}

🔴 IMPORTANT ACTIONS:
1. Consult your doctor immediately
2. Do NOT stop medication without medical advice
3. Report any adverse effects

For urgent concerns, call emergency services.

- LIFEXIA Safety Team"""
        
        return self.send_text_message(to_number, message)
    
    def send_prescription_ready(self, to_number: str, pharmacy_name: str, 
                              prescription_id: str, ready_time: str) -> Dict[str, Any]:
        """Notify patient their prescription is ready"""
        
        message = f"""✅ **PRESCRIPTION READY FOR PICKUP**

Prescription ID: #{prescription_id}

📍 Pharmacy: {pharmacy_name}
⏰ Ready Time: {ready_time}

Please bring:
- Prescription (if not already submitted)
- Valid ID
- Payment method

📞 Questions? Contact the pharmacy directly.

- LIFEXIA Prescription Service"""
        
        return self.send_text_message(to_number, message)
    
    def send_ayushman_card_info(self, to_number: str, hospital_name: str, 
                               services: List[str]) -> Dict[str, Any]:
        """Send Ayushman Bharat card accepted hospital information"""
        
        services_list = "\n".join([f"• {service}" for service in services])
        
        message = f"""🏥 **AYUSHMAN BHARAT CARD ACCEPTED**

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
        
        message = f"""👶 **MAA VATSALYA CARD ACCEPTED**

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
    
    def send_hospital_directions(self, to_number: str, hospital_name: str, 
                                address: str, google_maps_link: str, 
                                distance: str, eta: str) -> Dict[str, Any]:
        """Send hospital directions"""
        
        message = f"""🗺️ **DIRECTIONS TO HOSPITAL**

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
    
    def broadcast_alert(self, phone_numbers: List[str], message: str) -> Dict[str, Any]:
        """
        Broadcast alert to multiple users
        
        Note: Use sparingly to avoid spam flags
        Returns: Summary of sent/failed messages
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
                        "error": response.get('error')
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
        """
        Record that user sent a message (opens 24-hour window)
        """
        self.user_sessions[from_number] = {
            "last_message": datetime.now(),
            "window_open": True
        }
        logger.info(f"✅ 24-hour window opened for {from_number}")
    
    def can_send_message(self, to_number: str) -> bool:
        """
        Check if we can send a text message (within 24-hour window)
        """
        if to_number not in self.user_sessions:
            return False
        
        session = self.user_sessions[to_number]
        time_since = datetime.now() - session['last_message']
        
        return time_since < timedelta(hours=24)
    
    def send_interactive_button_message(self, to_number: str, body_text: str, 
                                       buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Send interactive button message
        
        Args:
            to_number: Recipient number
            body_text: Main message text
            buttons: List of buttons [{"id": "1", "title": "Button Text"}]
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
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
                                "title": btn["title"]
                            }
                        } for btn in buttons[:3]  # Max 3 buttons
                    ]
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Interactive message failed: {e}")
            return {"success": False, "error": str(e)}
    
    def send_location_message(self, to_number: str, latitude: float, 
                            longitude: float, name: str, address: str) -> Dict[str, Any]:
        """Send location pin"""
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
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
                timeout=10
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Location message failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_session_status(self, phone_number: str) -> Dict[str, Any]:
        """Get current session status for a phone number"""
        if phone_number in self.user_sessions:
            session = self.user_sessions[phone_number]
            time_remaining = timedelta(hours=24) - (datetime.now() - session['last_message'])
            
            return {
                "window_open": time_remaining.total_seconds() > 0,
                "last_message": session['last_message'].isoformat(),
                "time_remaining": str(time_remaining) if time_remaining.total_seconds() > 0 else "0"
            }
        
        return {
            "window_open": False,
            "message": "No active session"
        }