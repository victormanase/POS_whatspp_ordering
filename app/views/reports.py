from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import DataRequired
from app.models import db, Product, Sale, SaleItem, Purchase, PurchaseItem, Category, User
from app.views.auth import admin_required
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc, and_
import pandas as pd
from io import BytesIO
import json

reports_bp = Blueprint('reports', __name__)

class DateRangeForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()], default=lambda: date.today() - timedelta(days=30))
    end_date = DateField('End Date', validators=[DataRequired()], default=date.today)
    report_type = SelectField('Report Type', 
                             choices=[('sales', 'Sales Report'), 
                                    ('profit', 'Profit Report'),
                                    ('stock', 'Stock Report'),
                                    ('products', 'Product Performance')],
                             default='sales')
    submit = SubmitField('Generate Report')

@reports_bp.route('/')
@login_required
@admin_required
def index():
    """Reports dashboard"""
    form = DateRangeForm()
    
    # Quick stats
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'today_sales': Sale.query.filter(func.date(Sale.sale_date) == today).count(),
        'week_sales': Sale.query.filter(func.date(Sale.sale_date) >= week_ago).count(),
        'month_sales': Sale.query.filter(func.date(Sale.sale_date) >= month_ago).count(),
        'total_sales': Sale.query.count()
    }
    
    # Calculate revenue
    today_sales = Sale.query.filter(func.date(Sale.sale_date) == today).all()
    stats['today_revenue'] = sum([sale.total_amount for sale in today_sales])
    
    week_sales = Sale.query.filter(func.date(Sale.sale_date) >= week_ago).all()
    stats['week_revenue'] = sum([sale.total_amount for sale in week_sales])
    
    month_sales = Sale.query.filter(func.date(Sale.sale_date) >= month_ago).all()
    stats['month_revenue'] = sum([sale.total_amount for sale in month_sales])
    
    # Low stock count
    stats['low_stock_count'] = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.reorder_level
    ).count()
    
    return render_template('reports/index.html', 
                         title='Reports Dashboard', 
                         form=form,
                         stats=stats)

@reports_bp.route('/sales')
@login_required
@admin_required
def sales_report():
    """Sales report"""
    form = DateRangeForm()
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('reports.sales_report'))
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    
    # Get sales data
    sales = Sale.query.filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).order_by(Sale.sale_date.desc()).all()
    
    # Calculate totals
    total_sales = len(sales)
    total_revenue = sum([sale.total_amount for sale in sales])
    total_discount = sum([sale.discount_amount for sale in sales])
    total_tax = sum([sale.tax_amount for sale in sales])
    
    # Daily sales data for chart
    daily_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).group_by(func.date(Sale.sale_date)).order_by('date').all()
    
    # Payment method breakdown
    payment_methods = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).group_by(Sale.payment_method).all()
    
    # Top selling cashiers
    top_cashiers = db.session.query(
        User.username,
        func.count(Sale.id).label('sales_count'),
        func.sum(Sale.total_amount).label('total_amount')
    ).join(Sale).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).group_by(User.id).order_by(desc('total_amount')).limit(10).all()
    
    return render_template('reports/sales_report.html',
                         title='Sales Report',
                         sales=sales,
                         form=form,
                         start_date=start_date,
                         end_date=end_date,
                         total_sales=total_sales,
                         total_revenue=total_revenue,
                         total_discount=total_discount,
                         total_tax=total_tax,
                         daily_sales=daily_sales,
                         payment_methods=payment_methods,
                         top_cashiers=top_cashiers)

@reports_bp.route('/profit')
@login_required
@admin_required
def profit_report():
    """Profit analysis report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('reports.profit_report'))
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    
    # Get sales items with profit calculation
    sales_items = db.session.query(
        Product.name,
        Product.buying_price,
        Product.selling_price,
        SaleItem.quantity,
        SaleItem.unit_price,
        SaleItem.total_price,
        Sale.sale_date
    ).join(SaleItem).join(Sale).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).all()
    
    # Calculate profit data
    profit_data = []
    total_revenue = 0
    total_cost = 0
    total_profit = 0
    
    product_profits = {}
    
    for item in sales_items:
        cost = float(item.buying_price) * item.quantity
        revenue = float(item.total_price)
        profit = revenue - cost
        
        total_revenue += revenue
        total_cost += cost
        total_profit += profit
        
        # Track per product
        if item.name not in product_profits:
            product_profits[item.name] = {
                'revenue': 0,
                'cost': 0,
                'profit': 0,
                'quantity': 0,
                'margin': 0
            }
        
        product_profits[item.name]['revenue'] += revenue
        product_profits[item.name]['cost'] += cost
        product_profits[item.name]['profit'] += profit
        product_profits[item.name]['quantity'] += item.quantity
        
        if product_profits[item.name]['cost'] > 0:
            product_profits[item.name]['margin'] = (
                product_profits[item.name]['profit'] / product_profits[item.name]['revenue']
            ) * 100
    
    # Sort products by profit
    sorted_products = sorted(product_profits.items(), 
                           key=lambda x: x[1]['profit'], 
                           reverse=True)
    
    # Calculate overall margin
    overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    form = DateRangeForm()
    
    return render_template('reports/profit_report.html',
                         title='Profit Report',
                         form=form,
                         start_date=start_date,
                         end_date=end_date,
                         total_revenue=total_revenue,
                         total_cost=total_cost,
                         total_profit=total_profit,
                         overall_margin=overall_margin,
                         product_profits=sorted_products)

@reports_bp.route('/stock')
@login_required
@admin_required
def stock_report():
    """Stock analysis report"""
    # Current stock levels
    products = Product.query.filter_by(is_active=True).all()
    
    # Low stock items
    low_stock = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.reorder_level
    ).all()
    
    # Out of stock items
    out_of_stock = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity == 0
    ).all()
    
    # Stock value calculation
    total_stock_value = 0
    for product in products:
        total_stock_value += float(product.buying_price) * product.stock_quantity
    
    # Recent stock movements (purchases in last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_purchases = Purchase.query.filter(
        func.date(Purchase.purchase_date) >= thirty_days_ago
    ).order_by(Purchase.purchase_date.desc()).all()
    
    return render_template('reports/stock_report.html',
                         title='Stock Report',
                         products=products,
                         low_stock=low_stock,
                         out_of_stock=out_of_stock,
                         total_stock_value=total_stock_value,
                         recent_purchases=recent_purchases)

@reports_bp.route('/products')
@login_required
@admin_required
def product_performance():
    """Product performance report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('reports.product_performance'))
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    
    # Top selling products
    top_products = db.session.query(
        Product.name,
        Product.selling_price,
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.total_price).label('total_revenue')
    ).join(SaleItem).join(Sale).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).group_by(Product.id).order_by(desc('total_sold')).limit(20).all()
    
    # Category performance
    category_performance = db.session.query(
        Category.name,
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.total_price).label('total_revenue')
    ).join(Product).join(SaleItem).join(Sale).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).group_by(Category.id).order_by(desc('total_revenue')).all()
    
    # Slow moving products (products with no sales in period)
    sold_product_ids = db.session.query(SaleItem.product_id).join(Sale).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).distinct().subquery()
    
    slow_moving = Product.query.filter(
        Product.is_active == True,
        ~Product.id.in_(sold_product_ids)
    ).all()
    
    form = DateRangeForm()
    
    return render_template('reports/product_performance.html',
                         title='Product Performance',
                         form=form,
                         start_date=start_date,
                         end_date=end_date,
                         top_products=top_products,
                         category_performance=category_performance,
                         slow_moving=slow_moving)

@reports_bp.route('/export/<report_type>')
@login_required
@admin_required
def export_report(report_type):
    """Export reports to Excel"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('reports.index'))
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    
    output = BytesIO()
    
    if report_type == 'sales':
        # Export sales report
        sales = Sale.query.filter(
            func.date(Sale.sale_date) >= start_date,
            func.date(Sale.sale_date) <= end_date
        ).order_by(Sale.sale_date.desc()).all()
        
        data = []
        for sale in sales:
            data.append({
                'Sale Number': sale.sale_number,
                'Date': sale.sale_date.strftime('%Y-%m-%d %H:%M'),
                'Customer': sale.customer_name or 'Walk-in',
                'Subtotal': float(sale.subtotal),
                'Tax': float(sale.tax_amount),
                'Discount': float(sale.discount_amount),
                'Total': float(sale.total_amount),
                'Payment Method': sale.payment_method,
                'Cashier': sale.cashier.username
            })
        
        df = pd.DataFrame(data)
        df.to_excel(output, index=False)
        filename = f'sales_report_{start_date}_{end_date}.xlsx'
        
    elif report_type == 'products':
        # Export product performance
        top_products = db.session.query(
            Product.name,
            Product.selling_price,
            Product.stock_quantity,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            func.date(Sale.sale_date) >= start_date,
            func.date(Sale.sale_date) <= end_date
        ).group_by(Product.id).order_by(desc('total_sold')).all()
        
        data = []
        for product in top_products:
            data.append({
                'Product Name': product.name,
                'Selling Price': float(product.selling_price),
                'Current Stock': product.stock_quantity,
                'Total Sold': product.total_sold,
                'Total Revenue': float(product.total_revenue)
            })
        
        df = pd.DataFrame(data)
        df.to_excel(output, index=False)
        filename = f'products_report_{start_date}_{end_date}.xlsx'
        
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('reports.index'))
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@reports_bp.route('/api/chart-data/<chart_type>')
@login_required
@admin_required
def chart_data(chart_type):
    """API endpoint for chart data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    
    if chart_type == 'daily_sales':
        # Daily sales data
        daily_sales = db.session.query(
            func.date(Sale.sale_date).label('date'),
            func.count(Sale.id).label('count'),
            func.sum(Sale.total_amount).label('total')
        ).filter(
            func.date(Sale.sale_date) >= start_date,
            func.date(Sale.sale_date) <= end_date
        ).group_by(func.date(Sale.sale_date)).order_by('date').all()
        
        data = {
            'labels': [sale.date.strftime('%Y-%m-%d') for sale in daily_sales],
            'sales_count': [sale.count for sale in daily_sales],
            'revenue': [float(sale.total) for sale in daily_sales]
        }
        
    elif chart_type == 'top_products':
        # Top products
        top_products = db.session.query(
            Product.name,
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).join(Sale).filter(
            func.date(Sale.sale_date) >= start_date,
            func.date(Sale.sale_date) <= end_date
        ).group_by(Product.id).order_by(desc('total_sold')).limit(10).all()
        
        data = {
            'labels': [product.name for product in top_products],
            'values': [product.total_sold for product in top_products]
        }
        
    elif chart_type == 'category_performance':
        # Category performance
        category_perf = db.session.query(
            Category.name,
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(Product).join(SaleItem).join(Sale).filter(
            func.date(Sale.sale_date) >= start_date,
            func.date(Sale.sale_date) <= end_date
        ).group_by(Category.id).order_by(desc('total_revenue')).all()
        
        data = {
            'labels': [cat.name for cat in category_perf],
            'values': [float(cat.total_revenue) for cat in category_perf]
        }
        
    else:
        return jsonify({'error': 'Invalid chart type'}), 400
    
    return jsonify(data)