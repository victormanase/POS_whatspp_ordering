from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os

db = SQLAlchemy()

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='cashier')  # 'admin' or 'cashier'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property 
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

# Product Category model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Supplier model
class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    barcode = db.Column(db.String(100), unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    buying_price = db.Column(db.Numeric(10, 2), nullable=False)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_inclusive = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    purchase_items = db.relationship('PurchaseItem', backref='product', lazy=True)
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level
    
    @property
    def profit_margin(self):
        if self.buying_price > 0:
            return ((self.selling_price - self.buying_price) / self.buying_price) * 100
        return 0
    
    def __repr__(self):
        return f'<Product {self.name}>'

# Purchase model (for stock management)
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    invoice_number = db.Column(db.String(100))
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Purchase {self.invoice_number}>'

# Purchase Item model
class PurchaseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        return f'<PurchaseItem {self.product.name}>'

# Sale model
class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(20), unique=True, nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), default='cash')  # cash, card, mobile
    payment_status = db.Column(db.String(20), default='completed')  # completed, pending
    notes = db.Column(db.Text)
    cashier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_whatsapp_order = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    cashier = db.relationship('User', backref='sales')
    
    def generate_sale_number(self):
        """Generate unique sale number"""
        from datetime import datetime
        today = datetime.now()
        count = Sale.query.filter(
            db.func.date(Sale.sale_date) == today.date()
        ).count()
        return f"POS{today.strftime('%Y%m%d')}{count + 1:04d}"
    
    def __repr__(self):
        return f'<Sale {self.sale_number}>'

# Sale Item model
class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        return f'<SaleItem {self.product.name}>'

# WhatsApp Order model (for orders from WhatsApp)
class WhatsAppOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_name = db.Column(db.String(100))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)  # linked when converted to sale
    
    product = db.relationship('Product', backref='whatsapp_orders')
    
    def __repr__(self):
        return f'<WhatsAppOrder {self.customer_phone}>'

# System Settings model
class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.key}>'