from flask import Blueprint, request, jsonify, current_app
from twilio.twiml.messaging_response import MessagingResponse
from app.models import db, Product, WhatsAppOrder, Category
import re
from sqlalchemy import or_

whatsapp_bp = Blueprint('whatsapp', __name__)

def format_product_info(product):
    """Format product information for WhatsApp message"""
    message = f"🏷️ *{product.name}*\n"
    message += f"💰 Price: KES {product.selling_price:,.2f}\n"
    message += f"📦 Category: {product.category.name}\n"
    message += f"📊 Stock: {product.stock_quantity} units\n"
    
    if product.description:
        message += f"📝 Description: {product.description}\n"
    
    if product.barcode:
        message += f"🔢 Barcode: {product.barcode}\n"
    
    return message

def process_whatsapp_message(message_body, from_number):
    """Process incoming WhatsApp message and return response"""
    message_body = message_body.strip().lower()
    
    # Help command
    if message_body in ['help', 'menu', 'commands']:
        return """🤖 *POS System Bot*

Available commands:
• *search [product name]* - Search for products
• *price [product name]* - Get product price
• *order [product name] [quantity]* - Place an order
• *categories* - List all categories
• *help* - Show this menu

Example:
search smartphone
price laptop
order t-shirt 2
"""
    
    # Categories command
    if message_body == 'categories':
        categories = Category.query.all()
        if not categories:
            return "No categories available."
        
        response = "📂 *Product Categories:*\n\n"
        for category in categories:
            product_count = Product.query.filter_by(category_id=category.id, is_active=True).count()
            response += f"• {category.name} ({product_count} products)\n"
        
        return response
    
    # Search command
    if message_body.startswith('search '):
        search_term = message_body[7:].strip()
        
        products = Product.query.filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(f'%{search_term}%'),
                Product.barcode.ilike(f'%{search_term}%')
            )
        ).limit(5).all()
        
        if not products:
            return f"❌ No products found matching '{search_term}'"
        
        response = f"🔍 *Search results for '{search_term}':*\n\n"
        for product in products:
            response += format_product_info(product) + "\n"
            response += "─" * 30 + "\n\n"
        
        response += "💡 To get more info, use: *price [product name]*\n"
        response += "💡 To order, use: *order [product name] [quantity]*"
        
        return response
    
    # Price command
    if message_body.startswith('price '):
        product_name = message_body[6:].strip()
        
        product = Product.query.filter(
            Product.is_active == True,
            Product.name.ilike(f'%{product_name}%')
        ).first()
        
        if not product:
            return f"❌ Product '{product_name}' not found"
        
        return format_product_info(product)
    
    # Order command
    order_match = re.match(r'order\s+(.+?)\s+(\d+)', message_body)
    if order_match:
        product_name = order_match.group(1).strip()
        try:
            quantity = int(order_match.group(2))
        except ValueError:
            return "❌ Invalid quantity. Please use: *order [product name] [quantity]*"
        
        if quantity <= 0:
            return "❌ Quantity must be greater than 0"
        
        if quantity > 100:
            return "❌ Maximum quantity per order is 100 units"
        
        # Find product
        product = Product.query.filter(
            Product.is_active == True,
            Product.name.ilike(f'%{product_name}%')
        ).first()
        
        if not product:
            return f"❌ Product '{product_name}' not found"
        
        # Check stock
        if product.stock_quantity < quantity:
            return f"❌ Insufficient stock for {product.name}. Available: {product.stock_quantity} units"
        
        # Create WhatsApp order
        try:
            order = WhatsAppOrder(
                customer_phone=from_number,
                product_id=product.id,
                quantity=quantity,
                message=f"Order: {quantity}x {product.name}"
            )
            
            db.session.add(order)
            db.session.commit()
            
            total_amount = product.selling_price * quantity
            
            response = f"✅ *Order placed successfully!*\n\n"
            response += f"📦 Product: {product.name}\n"
            response += f"🔢 Quantity: {quantity}\n"
            response += f"💰 Unit Price: KES {product.selling_price:,.2f}\n"
            response += f"💳 Total: KES {total_amount:,.2f}\n\n"
            response += f"📞 Order ID: #{order.id}\n"
            response += f"⏰ Status: Pending\n\n"
            response += "Our team will contact you shortly to confirm your order and arrange delivery/pickup.\n\n"
            response += "Thank you for choosing us! 🙏"
            
            return response
            
        except Exception as e:
            return "❌ Error processing your order. Please try again later."
    
    # Default response for unrecognized commands
    return """❓ I didn't understand that command.

Type *help* to see available commands.

Examples:
• search phone
• price laptop  
• order shirt 2
• categories"""

@whatsapp_bp.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        # Get message details
        from_number = request.form.get('From', '').replace('whatsapp:', '')
        message_body = request.form.get('Body', '')
        
        if not from_number or not message_body:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Process the message and get response
        response_text = process_whatsapp_message(message_body, from_number)
        
        # Create Twilio response
        response = MessagingResponse()
        response.message(response_text)
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"WhatsApp webhook error: {str(e)}")
        
        # Return error response
        response = MessagingResponse()
        response.message("❌ Sorry, I'm experiencing technical difficulties. Please try again later.")
        return str(response), 200, {'Content-Type': 'text/xml'}

@whatsapp_bp.route('/send_message', methods=['POST'])
def send_message():
    """Send WhatsApp message (for notifications, order updates, etc.)"""
    try:
        data = request.get_json()
        to_number = data.get('to')
        message = data.get('message')
        
        if not to_number or not message:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Initialize Twilio client
        from twilio.rest import Client
        
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        whatsapp_number = current_app.config.get('WHATSAPP_NUMBER')
        
        if not all([account_sid, auth_token, whatsapp_number]):
            return jsonify({'error': 'WhatsApp configuration missing'}), 500
        
        client = Client(account_sid, auth_token)
        
        # Send message
        message = client.messages.create(
            body=message,
            from_=whatsapp_number,
            to=f'whatsapp:{to_number}'
        )
        
        return jsonify({
            'success': True,
            'message_sid': message.sid,
            'status': message.status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/notify_order_update', methods=['POST'])
def notify_order_update():
    """Send order update notification to customer"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        status = data.get('status')
        message = data.get('message', '')
        
        order = WhatsAppOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Update order status
        order.status = status
        db.session.commit()
        
        # Prepare notification message
        if not message:
            if status == 'confirmed':
                message = f"✅ Your order #{order.id} has been confirmed!\n\n"
                message += f"📦 {order.quantity}x {order.product.name}\n"
                message += f"💰 Total: KES {order.product.selling_price * order.quantity:,.2f}\n\n"
                message += "We'll contact you shortly for delivery/pickup details."
            elif status == 'ready':
                message = f"🎉 Your order #{order.id} is ready for pickup!\n\n"
                message += f"📦 {order.quantity}x {order.product.name}\n"
                message += "Please visit our store or wait for delivery."
            elif status == 'delivered':
                message = f"🚚 Your order #{order.id} has been delivered!\n\n"
                message += "Thank you for your business! 🙏"
            elif status == 'cancelled':
                message = f"❌ Your order #{order.id} has been cancelled.\n\n"
                message += "If you have any questions, please contact us."
        
        # Send notification
        from twilio.rest import Client
        
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        whatsapp_number = current_app.config.get('WHATSAPP_NUMBER')
        
        if all([account_sid, auth_token, whatsapp_number]):
            client = Client(account_sid, auth_token)
            
            client.messages.create(
                body=message,
                from_=whatsapp_number,
                to=f'whatsapp:{order.customer_phone}'
            )
        
        return jsonify({'success': True, 'message': 'Notification sent'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/test_webhook', methods=['GET', 'POST'])
def test_webhook():
    """Test webhook endpoint for development"""
    if request.method == 'GET':
        # Webhook verification for Twilio
        return request.args.get('hub.challenge', 'OK')
    
    # For testing - simulate a WhatsApp message
    test_message = request.form.get('message', 'help')
    test_from = request.form.get('from', '+1234567890')
    
    response_text = process_whatsapp_message(test_message, test_from)
    
    return jsonify({
        'message': test_message,
        'from': test_from,
        'response': response_text
    })

# Utility function to format currency
def format_currency(amount):
    """Format amount as currency"""
    return f"KES {float(amount):,.2f}"