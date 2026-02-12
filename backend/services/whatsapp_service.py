import requests
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, access_token, phone_number_id):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = "v22.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        # Track last user interaction for 24h window (in-memory, use Redis in production)
        self.user_sessions = {}

    def send_template_message(self, to_number, template_name, components=None, language_code="en_US"):
        """Sends a WhatsApp template message with optional components (variables)."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(f"{self.base_url}/messages", headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Successfully sent template {template_name} to {to_number}")
            return {"success": True, "data": response.json(), "method": "template"}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error sending WhatsApp template: {e}")
            error_details = {"error": str(e), "success": False, "method": "template"}
            if response := getattr(e, 'response', None):
                try:
                    error_data = response.json()
                    logger.error(f"Response from Meta: {error_data}")
                    error_details["meta_error"] = error_data
                    error_details["error_code"] = error_data.get('error', {}).get('code')
                    error_details["error_message"] = error_data.get('error', {}).get('message')
                except:
                    logger.error(f"Response from Meta: {response.text}")
                    error_details["meta_error"] = response.text
            return error_details

    def send_text_message(self, to_number, message_text):
        """Sends a plain text message (only works within 24h window)."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/messages", headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Successfully sent text message to {to_number}")
            # Update session window since message was successful
            self.user_sessions[to_number] = datetime.now()
            return {"success": True, "data": response.json(), "method": "text"}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error sending WhatsApp text message: {e}")
            error_details = {"error": str(e), "success": False, "method": "text"}
            if response := getattr(e, 'response', None):
                try:
                    error_data = response.json()
                    logger.error(f"Response from Meta: {error_data}")
                    error_details["meta_error"] = error_data
                    error_code = error_data.get('error', {}).get('code')
                    error_details["error_code"] = error_code
                    error_details["error_message"] = error_data.get('error', {}).get('message')
                    
                    # Check for 24-hour window error (code 131047 or 131026)
                    if error_code in [131047, 131026, 131051]:
                        error_details["requires_template"] = True
                        error_details["user_friendly_message"] = "Cannot send text message. User needs to message first, or use an approved template."
                except:
                    logger.error(f"Response from Meta: {response.text}")
                    error_details["meta_error"] = response.text
            return error_details
    
    def send_chat_response(self, to_number, message_text, fallback_template="hello_world"):
        """
        Smart send: Tries text message first, falls back to template if outside 24h window.
        This is the PRIMARY method to use for chatbot responses.
        
        Args:
            to_number: WhatsApp number (format: 919824794027)
            message_text: The message content
            fallback_template: Template to use if text fails (default: hello_world)
        """
        # First, try sending as text message
        logger.info(f"📤 Attempting to send chat response to {to_number}")
        result = self.send_text_message(to_number, message_text)
        
        # If it failed due to 24h window, send a template instead
        if not result.get("success") and result.get("requires_template"):
            logger.info(f"🔄 Text message failed for {to_number}, falling back to template '{fallback_template}'")
            
            fallback_result = self.send_template_message(
                to_number, 
                fallback_template,
                language_code="en_US"
            )
            
            # Add context about why we used template
            if fallback_result.get("success"):
                fallback_result["fallback_used"] = True
                fallback_result["original_message"] = message_text
                fallback_result["reason"] = "User hasn't messaged in 24 hours"
            
            return fallback_result
        
        return result

    def record_user_message(self, from_number):
        """
        Record when user sends a message (opens 24h window).
        Call this from your webhook when you receive a message from user.
        """
        self.user_sessions[from_number] = datetime.now()
        logger.info(f"✅ Recorded message from {from_number}, 24h window opened")
        return {"success": True, "window_opened": True, "expires_at": datetime.now() + timedelta(hours=24)}
    
    def is_within_24h_window(self, to_number):
        """Check if we can send text messages to this number"""
        if to_number not in self.user_sessions:
            logger.info(f"❌ No session found for {to_number}")
            return False
        
        last_message = self.user_sessions[to_number]
        is_within = datetime.now() - last_message < timedelta(hours=24)
        
        if is_within:
            remaining = timedelta(hours=24) - (datetime.now() - last_message)
            logger.info(f"✅ {to_number} is within 24h window. {remaining} remaining")
        else:
            logger.info(f"❌ {to_number} is outside 24h window")
        
        return is_within

    def send_broadcast(self, to_numbers, template_name="hello_world", components=None, message_text=None):
        """Sends a message to multiple recipients. Uses templates with components by default."""
        results = []
        for number in to_numbers:
            if message_text and not template_name:
                # Try smart send with fallback
                result = self.send_chat_response(number, message_text)
            else:
                # Template works anytime, now supports dynamic components
                result = self.send_template_message(number, template_name, components=components)
            
            results.append({
                "number": number,
                "success": result.get("success", False),
                "result": result
            })
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "total": len(to_numbers),
            "successful": success_count,
            "failed": len(to_numbers) - success_count,
            "results": results
        }

    def test_config(self):
        """Checks if the service is properly configured."""
        if not self.access_token or not self.phone_number_id:
            missing = []
            if not self.access_token:
                missing.append("access_token")
            if not self.phone_number_id:
                missing.append("phone_number_id")
            return {"status": "unconfigured", "missing": missing, "success": False}
        return {"status": "configured", "api_url": self.base_url, "success": True}