#!/bin/bash

# LifeXia WhatsApp Direct API Test
# This script directly calls the WhatsApp API without going through Flask

echo "=================================================="
echo "LifeXia - WhatsApp Direct API Test"
echo "=================================================="
echo ""

# Configuration
ACCESS_TOKEN="EAAK0LZBFV6HcBQhBTa7rPws6TQK2ZCuCnc1Ylsawxn7mvZAO7N7dmxlqsSMYUozKOxsIxnj7sn1uGTh1j2GkqY7S3ZCUZAZAOD7QCtkqcFjY7EhJE6ZCU3VXLCOb28x9cqhc3wjiXXKIsZCkUZBnZCEQp2lMZCQOeOUEaeBZC2qKfAyRyPAE7Ht1TQSmTTAAKzVRWmDJ57Naf8XFx7oJIHcEkpOeUZCT5eMqy2Rb4MZCpiYIfKvE3qzrTB04qDe7Sd9GBAp3XsObatJjpoVDC8wOZBB3TVCHpoqrgZDZD"
PHONE_NUMBER_ID="1026265500564720"
TO_NUMBER="919824794027"

echo "📱 Configuration:"
echo "   Phone Number ID: $PHONE_NUMBER_ID"
echo "   Sending to: +$TO_NUMBER"
echo ""

echo "=================================================="
echo "Test 1: Sending Template Message (hello_world)"
echo "=================================================="
echo ""

curl -i -X POST \
  "https://graph.facebook.com/v22.0/$PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"messaging_product\": \"whatsapp\",
    \"to\": \"$TO_NUMBER\",
    \"type\": \"template\",
    \"template\": {
      \"name\": \"hello_world\",
      \"language\": {
        \"code\": \"en_US\"
      }
    }
  }"

echo ""
echo ""
echo "=================================================="
echo "✅ Test Complete!"
echo "=================================================="
echo ""
echo "Check your WhatsApp (+$TO_NUMBER) for the message."
echo ""
echo "If you see errors:"
echo "  - Error 100: Invalid parameters"
echo "  - Error 131026: Template not found (needs approval)"
echo "  - Error 131047: Re-engagement message (user needs to message you first)"
echo "  - Error 131051: Unsupported message type"
echo ""
