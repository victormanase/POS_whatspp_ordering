from flask import Blueprint, render_template, jsonify, redirect, url_for, request
from flask_login import login_required, current_user
from app.models import db, Product, Sale, SaleItem, Purchase, WhatsAppOrder, Category
from datetime import datetime, timedelta
from sqlalchemy import func, desc

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get today's date
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Dashboard stats
    stats = {
        'total_products': Product.query.filter_by(is_active=True).count(),
        'low_stock_products': Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity <= Product.reorder_level
        ).count(),
        'total_categories': Category.query.count(),
        'pending_whatsapp_orders': WhatsAppOrder.query.filter_by(status='pending').count()
    }
    
    # Sales stats
    today_sales = Sale.query.filter(func.date(Sale.sale_date) == today)
    stats['today_sales_count'] = today_sales.count()
    stats['today_sales_total'] = sum([sale.total_amount for sale in today_sales]) or 0
    
    week_sales = Sale.query.filter(func.date(Sale.sale_date) >= week_ago)
    stats['week_sales_total'] = sum([sale.total_amount for sale in week_sales]) or 0
    
    month_sales = Sale.query.filter(func.date(Sale.sale_date) >= month_ago)
    stats['month_sales_total'] = sum([sale.total_amount for sale in month_sales]) or 0
    
    # Recent sales
    recent_sales = Sale.query.order_by(desc(Sale.sale_date)).limit(5).all()
    
    # Low stock products
    low_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.reorder_level
    ).limit(10).all()
    
    # Pending WhatsApp orders
    pending_orders = WhatsAppOrder.query.filter_by(status='pending').limit(5).all()
    
    return render_template('dashboard/index.html', 
                         title='Dashboard',
                         stats=stats,
                         recent_sales=recent_sales,
                         low_stock_products=low_stock_products,
                         pending_orders=pending_orders)

@main_bp.route('/api/dashboard/chart-data')
@login_required
def dashboard_chart_data():
    """API endpoint for dashboard charts"""
    # Sales data for the last 7 days
    sales_data = []
    for i in range(7):
        date = datetime.now().date() - timedelta(days=i)
        daily_sales = Sale.query.filter(func.date(Sale.sale_date) == date).all()
        total = sum([sale.total_amount for sale in daily_sales])
        sales_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'total': float(total)
        })
    
    # Top selling products (last 30 days)
    top_products = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).join(Sale).filter(
        func.date(Sale.sale_date) >= datetime.now().date() - timedelta(days=30)
    ).group_by(Product.id).order_by(
        desc(func.sum(SaleItem.quantity))
    ).limit(5).all()
    
    return jsonify({
        'sales_data': list(reversed(sales_data)),
        'top_products': [{'name': p[0], 'sold': p[1]} for p in top_products]
    })

@main_bp.route('/search')
@login_required
def search():
    """Global search functionality"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Search products
    products = Product.query.filter(
        Product.is_active == True,
        Product.name.contains(query) | Product.barcode.contains(query)
    ).limit(10).all()
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'type': 'product',
            'url': url_for('products.view', id=product.id),
            'extra': f'Stock: {product.stock_quantity}'
        })
    
    return jsonify(results)