"""
Alternative WhatsApp Integration Options
This file shows different ways to integrate WhatsApp without Twilio
"""

from flask import Blueprint, request, jsonify, current_app
from app.models import db, Product, WhatsAppOrder, Category
import re
import requests
import os
from sqlalchemy import or_

whatsapp_alt_bp = Blueprint('whatsapp_alt', __name__)

# Option 1: WhatsApp Business Cloud API (Facebook/Meta)
class FacebookWhatsAppAPI:
    def __init__(self, access_token, phone_number_id, verify_token):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.base_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
    
    def send_message(self, to_phone, message):
        """Send WhatsApp message via Facebook API"""
        url = f"{self.base_url}/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def send_image_message(self, to_phone, image_url, caption=""):
        """Send image with caption"""
        url = f"{self.base_url}/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            return response.json()
        except Exception as e:
            print(f"Error sending image: {e}")
            return None

# Option 2: PyWhatKit Integration (Free but limited)
def send_message_pywhatkit(phone, message, hour=None, minute=None):
    """
    Send WhatsApp message using PyWhatKit
    Note: This opens WhatsApp Web and may not be suitable for production
    """
    try:
        import pywhatkit as kit
        if hour and minute:
            kit.sendwhatmsg(phone, message, hour, minute)
        else:
            kit.sendwhatmsg_instantly(phone, message, 10)
        return True
    except ImportError:
        print("PyWhatKit not installed. Run: pip install pywhatkit")
        return False
    except Exception as e:
        print(f"Error with PyWhatKit: {e}")
        return False

# Option 3: Simple Webhook for external WhatsApp services
@whatsapp_alt_bp.route('/webhook/facebook', methods=['GET', 'POST'])
def facebook_webhook():
    """Webhook for Facebook WhatsApp Business API"""
    
    if request.method == 'GET':
        # Webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == current_app.config.get('FACEBOOK_VERIFY_TOKEN'):
            return challenge
        else:
            return 'Invalid verification token', 403
    
    elif request.method == 'POST':
        # Handle incoming messages
        try:
            data = request.get_json()
            
            # Extract message details from Facebook webhook format
            if 'entry' in data:
                for entry in data['entry']:
                    if 'changes' in entry:
                        for change in entry['changes']:
                            if change.get('field') == 'messages':
                                value = change.get('value', {})
                                if 'messages' in value:
                                    for message in value['messages']:
                                        from_number = message.get('from')
                                        message_text = message.get('text', {}).get('body', '')
                                        
                                        # Process the message
                                        response_text = process_whatsapp_message(message_text, from_number)
                                        
                                        # Send response back
                                        fb_api = FacebookWhatsAppAPI(
                                            current_app.config.get('FACEBOOK_ACCESS_TOKEN'),
                                            current_app.config.get('FACEBOOK_PHONE_NUMBER_ID'),
                                            current_app.config.get('FACEBOOK_VERIFY_TOKEN')
                                        )
                                        fb_api.send_message(from_number, response_text)
            
            return jsonify({'status': 'success'}), 200
            
        except Exception as e:
            print(f"Webhook error: {e}")
            return jsonify({'error': str(e)}), 500

# Option 4: Generic webhook for any WhatsApp service
@whatsapp_alt_bp.route('/webhook/generic', methods=['POST'])
def generic_whatsapp_webhook():
    """
    Generic webhook that can work with various WhatsApp APIs
    Expects JSON: {"from": "+1234567890", "message": "text", "api_key": "optional"}
    """
    try:
        data = request.get_json()
        
        from_number = data.get('from', '')
        message_text = data.get('message', '')
        api_key = data.get('api_key', '')
        
        # Optional API key validation
        if current_app.config.get('GENERIC_API_KEY'):
            if api_key != current_app.config.get('GENERIC_API_KEY'):
                return jsonify({'error': 'Invalid API key'}), 401
        
        if not from_number or not message_text:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Process the message using existing logic
        from app.views.whatsapp import process_whatsapp_message
        response_text = process_whatsapp_message(message_text, from_number)
        
        return jsonify({
            'status': 'success',
            'response': response_text,
            'from': from_number
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Option 5: Email-to-WhatsApp bridge
@whatsapp_alt_bp.route('/email-bridge', methods=['POST'])
def email_to_whatsapp():
    """
    Convert email messages to WhatsApp format
    Useful if you have email integration but want WhatsApp-like responses
    """
    try:
        data = request.get_json()
        email_body = data.get('body', '')
        sender_email = data.get('from', '')
        
        # Extract phone number from email or use mapping
        phone_mapping = current_app.config.get('EMAIL_PHONE_MAPPING', {})
        phone_number = phone_mapping.get(sender_email, '')
        
        if not phone_number:
            return jsonify({'error': 'Phone number not found for email'}), 400
        
        # Process as WhatsApp message
        from app.views.whatsapp import process_whatsapp_message
        response_text = process_whatsapp_message(email_body, phone_number)
        
        return jsonify({
            'status': 'success',
            'response': response_text,
            'email': sender_email,
            'phone': phone_number
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Configuration helper
def setup_whatsapp_alternative(app, provider='facebook'):
    """Setup alternative WhatsApp integration"""
    
    if provider == 'facebook':
        app.config['FACEBOOK_ACCESS_TOKEN'] = os.environ.get('FACEBOOK_ACCESS_TOKEN')
        app.config['FACEBOOK_PHONE_NUMBER_ID'] = os.environ.get('FACEBOOK_PHONE_NUMBER_ID')
        app.config['FACEBOOK_VERIFY_TOKEN'] = os.environ.get('FACEBOOK_VERIFY_TOKEN')
        
    elif provider == 'pywhatkit':
        # No special config needed for PyWhatKit
        pass
        
    elif provider == 'generic':
        app.config['GENERIC_API_KEY'] = os.environ.get('GENERIC_API_KEY')
        
    # Register the blueprint
    app.register_blueprint(whatsapp_alt_bp, url_prefix='/whatsapp-alt')