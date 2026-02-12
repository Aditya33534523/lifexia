import requests
import json
import logging
from backend.config import Config

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.access_token = Config.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = Config.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v22.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

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
            logger.info(f"Successfully sent template {template_name} to {to_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp template: {e}")
            if response := getattr(e, 'response', None):
                logger.error(f"Response from Meta: {response.text}")
            return {"error": str(e), "success": False}

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
            logger.info(f"Successfully sent text message to {to_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp text message: {e}")
            return {"error": str(e), "success": False}

    def send_broadcast(self, to_numbers, template_name="hello_world", components=None, message_text=None):
        """Sends a message to multiple recipients. Uses templates with components by default."""
        results = []
        for number in to_numbers:
            if message_text:
                # Text only works within 24h window
                result = self.send_text_message(number, message_text)
            else:
                # Template works anytime, now supports dynamic components
                result = self.send_template_message(number, template_name, components=components)
            
            results.append({
                "number": number,
                "result": result
            })
        return results

    def test_config(self):
        """Checks if the service is properly configured."""
        if not self.access_token or not self.phone_number_id:
            return {"status": "unconfigured", "missing": ["access_token" if not self.access_token else "phone_number_id"]}
        return {"status": "configured", "api_url": self.base_url}
