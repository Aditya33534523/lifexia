# LifeXia WhatsApp Integration Guide

## 🚀 Quick Start

Your WhatsApp Business API is now integrated into LifeXia! Here's everything you need to know.

## 📋 Configuration

Your WhatsApp credentials are configured in `.env`:

```env
WHATSAPP_ACCESS_TOKEN=EAAK0LZBFV6HcBQ...
WHATSAPP_PHONE_NUMBER_ID=1026265500564720
WHATSAPP_ACCOUNT_ID=1646555163363020
ADMIN_WHATSAPP_NUMBER=+919824794027
```

## 🔧 Installation

1. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Start the Flask application:
```bash
python backend/app.py
```

The app will run on `http://localhost:5000`

## 📡 API Endpoints

### 1. Test Configuration
```bash
GET /api/whatsapp/test
```
Verifies that WhatsApp service is properly configured.

### 2. Send Template Message
```bash
POST /api/whatsapp/send-template
Content-Type: application/json

{
  "to_number": "919824794027",
  "template_name": "hello_world",
  "language_code": "en_US"
}
```

### 3. Send Text Message
```bash
POST /api/whatsapp/send-message
Content-Type: application/json

{
  "to_number": "919824794027",
  "message": "Your message here"
}
```

### 4. Send Medication Reminder
```bash
POST /api/whatsapp/send-reminder
Content-Type: application/json

{
  "to_number": "919824794027",
  "medication_name": "Aspirin",
  "dosage": "100mg",
  "time": "8:00 AM"
}
```

### 5. Quick Send (Test)
```bash
POST /api/whatsapp/quick-send
```
Sends a hello_world template to your configured test number.

### 6. Webhook (for receiving messages)
```bash
GET /api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=CHALLENGE
POST /api/whatsapp/webhook
```

## 🧪 Testing

Run the test script:
```bash
python test_whatsapp.py
```

Or use curl to test directly:

### Send Template Message
```bash
curl -X POST http://localhost:5000/api/whatsapp/send-template \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "919824794027",
    "template_name": "hello_world",
    "language_code": "en_US"
  }'
```

### Send Text Message
```bash
curl -X POST http://localhost:5000/api/whatsapp/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "919824794027",
    "message": "Hello from LifeXia!"
  }'
```

### Quick Send
```bash
curl -X POST http://localhost:5000/api/whatsapp/quick-send
```

## 🔐 Webhook Setup

To receive messages from WhatsApp:

1. Deploy your app to a public server (e.g., Heroku, AWS, DigitalOcean)
2. In Meta Developer Console:
   - Go to WhatsApp > Configuration
   - Set Webhook URL: `https://your-domain.com/api/whatsapp/webhook`
   - Set Verify Token: `lifexia_webhook_verify_token_2024`
   - Subscribe to `messages` webhook field

## 📱 Phone Number Format

- Use international format without `+` sign
- Example: `919824794027` (India)
- Your configured number: `919824794027`

## ⚠️ Important Notes

### Template Messages
- Only **approved templates** can be sent
- `hello_world` is pre-approved by Meta
- Custom templates need approval (24-48 hours)
- Template format must match exactly

### Text Messages  
- Can only be sent within 24 hours of user initiating conversation
- For proactive messages, use approved templates

### Rate Limits
- Free tier: 1,000 conversations/month
- Rate limit: ~60 messages/second
- Business tier: Higher limits available

## 🎯 Use Cases in LifeXia

### 1. Medication Reminders
```python
POST /api/whatsapp/send-reminder
{
  "to_number": "919824794027",
  "medication_name": "Metformin",
  "dosage": "500mg twice daily",
  "time": "9:00 AM & 9:00 PM"
}
```

### 2. Prescription Ready Notification
```python
POST /api/whatsapp/send-message
{
  "to_number": "919824794027",
  "message": "Your prescription is ready for pickup at MedPlus Pharmacy, Location: Ahmedabad"
}
```

### 3. Drug Interaction Alerts
```python
POST /api/whatsapp/send-message
{
  "to_number": "919824794027",
  "message": "⚠️ Drug Interaction Alert\n\nThe medications you're taking may interact. Please consult your doctor.\n\n- LifeXia Assistant"
}
```

## 🔍 Troubleshooting

### Error: "Invalid phone number"
- Ensure number is in international format without `+`
- Example: `919824794027` not `+91 98247 94027`

### Error: "Template not found"
- Template must be approved in Meta Business Suite
- Use exact template name and language code

### Error: "Token expired"
- Access tokens expire after 60 days
- Generate new token in Meta Developer Console

### Error: "Webhook verification failed"
- Check verify token matches in code and Meta console
- Ensure endpoint is publicly accessible

## 📚 File Structure

```
lifexia/
├── backend/
│   ├── app.py                          # Main Flask app with WhatsApp routes
│   ├── config.py                       # Configuration (includes WhatsApp)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── whatsapp_routes.py         # WhatsApp API endpoints
│   └── services/
│       ├── __init__.py
│       └── whatsapp_service.py        # WhatsApp Business API logic
├── .env                                # Environment variables
└── test_whatsapp.py                   # Test script
```

## 🔄 Next Steps

1. **Start the server**: `python backend/app.py`
2. **Test the integration**: `python test_whatsapp.py`
3. **Create custom templates** in Meta Business Suite
4. **Set up webhook** for receiving messages
5. **Integrate into your UI** using the API endpoints

## 💡 Tips

- **Test with hello_world first** - it's pre-approved
- **Keep access token secure** - never commit to Git
- **Monitor API usage** in Meta Business Manager
- **Use templates for marketing** - text messages are for conversations
- **Handle errors gracefully** - check response.success before proceeding

## 📞 Support

For WhatsApp Business API issues:
- [Meta Developer Docs](https://developers.facebook.com/docs/whatsapp)
- [WhatsApp Business API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api)
