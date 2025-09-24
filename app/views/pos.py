from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from app.models import db, Product, Sale, SaleItem, WhatsAppOrder
from decimal import Decimal
import json
from datetime import datetime

pos_bp = Blueprint('pos', __name__)

class SaleForm(FlaskForm):
    customer_name = StringField('Customer Name')
    customer_phone = StringField('Customer Phone')
    payment_method = SelectField('Payment Method', 
                                choices=[('cash', 'Cash'), ('card', 'Card'), ('mobile', 'Mobile Money')],
                                default='cash')
    discount_amount = DecimalField('Discount Amount', default=0, validators=[NumberRange(min=0)])
    notes = TextAreaField('Notes')
    cart_data = HiddenField()
    submit = SubmitField('Complete Sale')

@pos_bp.route('/')
@login_required
def index():
    """Main POS interface"""
    form = SaleForm()
    tax_rate = current_app.config.get('DEFAULT_TAX_RATE', 0.16)
    
    # Get pending WhatsApp orders for quick access
    pending_orders = WhatsAppOrder.query.filter_by(status='pending').limit(5).all()
    
    return render_template('pos/index.html', 
                         title='Point of Sale',
                         form=form,
                         tax_rate=tax_rate,
                         pending_orders=pending_orders)

@pos_bp.route('/search_products')
@login_required
def search_products():
    """Search products for POS"""
    query = request.args.get('q', '')
    barcode = request.args.get('barcode', '')
    
    if barcode:
        # Search by barcode (exact match)
        product = Product.query.filter_by(barcode=barcode, is_active=True).first()
        if product:
            return jsonify([{
                'id': product.id,
                'name': product.name,
                'barcode': product.barcode,
                'price': float(product.selling_price),
                'stock': product.stock_quantity,
                'tax_inclusive': product.tax_inclusive
            }])
        else:
            return jsonify([])
    
    if query:
        # Search by name or barcode (partial match)
        products = Product.query.filter(
            Product.is_active == True,
            (Product.name.contains(query) | Product.barcode.contains(query))
        ).limit(20).all()
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'name': product.name,
                'barcode': product.barcode,
                'price': float(product.selling_price),
                'stock': product.stock_quantity,
                'tax_inclusive': product.tax_inclusive
            })
        
        return jsonify(results)
    
    return jsonify([])

@pos_bp.route('/complete_sale', methods=['POST'])
@login_required
def complete_sale():
    """Complete a sale transaction"""
    try:
        form = SaleForm()
        if not form.validate_on_submit():
            return jsonify({'success': False, 'message': 'Invalid form data'})
        
        # Parse cart data
        cart_data = json.loads(form.cart_data.data)
        if not cart_data or len(cart_data) == 0:
            return jsonify({'success': False, 'message': 'Cart is empty'})
        
        # Calculate totals
        subtotal = Decimal('0.00')
        tax_amount = Decimal('0.00')
        tax_rate = Decimal(str(current_app.config.get('DEFAULT_TAX_RATE', 0.16)))
        
        for item in cart_data:
            item_total = Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            subtotal += item_total
            
            # Calculate tax if price is not tax inclusive
            product = Product.query.get(item['product_id'])
            if product and not product.tax_inclusive:
                tax_amount += item_total * tax_rate
        
        discount_amount = Decimal(str(form.discount_amount.data or 0))
        total_amount = subtotal + tax_amount - discount_amount
        
        # Create sale record
        sale = Sale(
            customer_name=form.customer_name.data,
            customer_phone=form.customer_phone.data,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_method=form.payment_method.data,
            notes=form.notes.data,
            cashier_id=current_user.id
        )
        
        # Generate sale number
        sale.sale_number = sale.generate_sale_number()
        
        db.session.add(sale)
        db.session.flush()  # Get the sale ID
        
        # Create sale items and update stock
        for item in cart_data:
            product = Product.query.get(item['product_id'])
            if not product:
                return jsonify({'success': False, 'message': f'Product not found: {item["name"]}'})
            
            # Check stock availability
            if product.stock_quantity < item['quantity']:
                return jsonify({'success': False, 'message': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'})
            
            # Create sale item
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item['quantity'],
                unit_price=Decimal(str(item['price'])),
                total_price=Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            )
            db.session.add(sale_item)
            
            # Update stock
            product.stock_quantity -= item['quantity']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sale completed successfully!',
            'sale_id': sale.id,
            'sale_number': sale.sale_number,
            'total': float(total_amount)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error completing sale: {str(e)}'})

@pos_bp.route('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    """Display receipt for a sale"""
    sale = Sale.query.get_or_404(sale_id)
    
    # Check if current user is authorized to view this receipt
    if not current_user.is_admin and sale.cashier_id != current_user.id:
        flash('You are not authorized to view this receipt.', 'error')
        return redirect(url_for('pos.index'))
    
    return render_template('pos/receipt.html', title='Receipt', sale=sale)

@pos_bp.route('/print_receipt/<int:sale_id>')
@login_required
def print_receipt(sale_id):
    """Print-friendly receipt view"""
    sale = Sale.query.get_or_404(sale_id)
    
    # Check if current user is authorized to view this receipt
    if not current_user.is_admin and sale.cashier_id != current_user.id:
        flash('You are not authorized to view this receipt.', 'error')
        return redirect(url_for('pos.index'))
    
    business_info = {
        'name': current_app.config.get('BUSINESS_NAME', 'POS System'),
        'address': current_app.config.get('BUSINESS_ADDRESS', ''),
        'phone': current_app.config.get('BUSINESS_PHONE', '')
    }
    
    return render_template('pos/print_receipt.html', 
                         title='Print Receipt', 
                         sale=sale,
                         business_info=business_info)

@pos_bp.route('/whatsapp_orders')
@login_required
def whatsapp_orders():
    """View pending WhatsApp orders"""
    orders = WhatsAppOrder.query.filter_by(status='pending').order_by(WhatsAppOrder.created_at.desc()).all()
    return render_template('pos/whatsapp_orders.html', 
                         title='WhatsApp Orders', 
                         orders=orders)

@pos_bp.route('/convert_whatsapp_order/<int:order_id>')
@login_required
def convert_whatsapp_order(order_id):
    """Convert WhatsApp order to POS sale"""
    order = WhatsAppOrder.query.get_or_404(order_id)
    
    # Pre-fill form with WhatsApp order data
    form = SaleForm()
    form.customer_name.data = order.customer_name
    form.customer_phone.data = order.customer_phone
    
    # Prepare cart data
    cart_data = [{
        'product_id': order.product.id,
        'name': order.product.name,
        'price': float(order.product.selling_price),
        'quantity': order.quantity,
        'barcode': order.product.barcode
    }]
    
    tax_rate = current_app.config.get('DEFAULT_TAX_RATE', 0.16)
    
    return render_template('pos/index.html', 
                         title='Convert WhatsApp Order',
                         form=form,
                         tax_rate=tax_rate,
                         initial_cart=cart_data,
                         whatsapp_order=order)

@pos_bp.route('/confirm_whatsapp_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_whatsapp_order(order_id):
    """Mark WhatsApp order as confirmed and link to sale"""
    try:
        order = WhatsAppOrder.query.get_or_404(order_id)
        data = request.get_json()
        
        # Update order status and link to sale
        order.status = 'completed'
        order.sale_id = data.get('sale_id')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'WhatsApp order confirmed and linked to sale'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@pos_bp.route('/cancel_whatsapp_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_whatsapp_order(order_id):
    """Cancel a WhatsApp order"""
    try:
        order = WhatsAppOrder.query.get_or_404(order_id)
        order.status = 'cancelled'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'WhatsApp order cancelled'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@pos_bp.route('/sales')
@login_required
def sales():
    """View recent sales"""
    page = request.args.get('page', 1, type=int)
    
    query = Sale.query
    
    # If not admin, only show sales made by current user
    if not current_user.is_admin:
        query = query.filter_by(cashier_id=current_user.id)
    
    sales = query.order_by(Sale.sale_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('pos/sales.html', title='Sales History', sales=sales)

@pos_bp.route('/sale/<int:sale_id>')
@login_required
def view_sale(sale_id):
    """View sale details"""
    sale = Sale.query.get_or_404(sale_id)
    
    # Check if current user is authorized to view this sale
    if not current_user.is_admin and sale.cashier_id != current_user.id:
        flash('You are not authorized to view this sale.', 'error')
        return redirect(url_for('pos.sales'))
    
    return render_template('pos/view_sale.html', title=f'Sale {sale.sale_number}', sale=sale)