#!/usr/bin/env python3
import os
from app import create_app, db
from app.models import User, Category, Product, Sale, Purchase, Supplier, WhatsAppOrder
from flask_migrate import upgrade
from flask.cli import with_appcontext
import click

app = create_app()

@app.cli.command()
@with_appcontext
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized.")

@app.cli.command()
@with_appcontext
def create_admin():
    """Create an admin user."""
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print("User already exists!")
        return
    
    admin = User(username=username, email=email, role='admin')
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin user '{username}' created successfully!")

@app.cli.command()
@with_appcontext
def seed_data():
    """Seed the database with sample data."""
    # Create categories
    categories = [
        Category(name='Electronics', description='Electronic devices and accessories'),
        Category(name='Clothing', description='Clothes and fashion items'),
        Category(name='Food & Beverages', description='Food and drink items'),
        Category(name='Home & Garden', description='Home and garden products'),
        Category(name='Books', description='Books and educational materials')
    ]
    
    for category in categories:
        if not Category.query.filter_by(name=category.name).first():
            db.session.add(category)
    
    db.session.commit()
    print("Sample categories created.")
    
    # Create suppliers
    suppliers = [
        Supplier(name='Tech Distributors Ltd', contact_person='John Doe', 
                phone='+254700123456', email='john@techdist.com'),
        Supplier(name='Fashion World Wholesale', contact_person='Jane Smith',
                phone='+254711234567', email='jane@fashionworld.com')
    ]
    
    for supplier in suppliers:
        if not Supplier.query.filter_by(name=supplier.name).first():
            db.session.add(supplier)
    
    db.session.commit()
    print("Sample suppliers created.")
    
    # Create sample products
    electronics_cat = Category.query.filter_by(name='Electronics').first()
    clothing_cat = Category.query.filter_by(name='Clothing').first()
    
    products = [
        Product(name='Smartphone X1', description='Latest smartphone model',
               barcode='1234567890123', category=electronics_cat,
               buying_price=15000, selling_price=20000, stock_quantity=50,
               reorder_level=5),
        Product(name='Wireless Earbuds', description='Bluetooth wireless earbuds',
               barcode='2345678901234', category=electronics_cat,
               buying_price=2000, selling_price=3500, stock_quantity=100,
               reorder_level=10),
        Product(name='Cotton T-Shirt', description='100% cotton t-shirt',
               barcode='3456789012345', category=clothing_cat,
               buying_price=500, selling_price=1200, stock_quantity=200,
               reorder_level=20)
    ]
    
    for product in products:
        if not Product.query.filter_by(barcode=product.barcode).first():
            db.session.add(product)
    
    db.session.commit()
    print("Sample products created.")
    print("Database seeded successfully!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
