from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from werkzeug.utils import secure_filename
from app.models import db, Product, Category, Supplier, Purchase, PurchaseItem
from app.views.auth import admin_required
import os
import uuid
from PIL import Image

products_bp = Blueprint('products', __name__)

# Forms
class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Category')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    barcode = StringField('Barcode')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    buying_price = DecimalField('Buying Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = DecimalField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    tax_inclusive = BooleanField('Price includes tax')
    stock_quantity = IntegerField('Initial Stock', validators=[NumberRange(min=0)], default=0)
    reorder_level = IntegerField('Reorder Level', validators=[NumberRange(min=0)], default=10)
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Product')
    
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired()])
    contact_person = StringField('Contact Person')
    phone = StringField('Phone')
    email = StringField('Email')
    address = TextAreaField('Address')
    submit = SubmitField('Save Supplier')

class PurchaseForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    invoice_number = StringField('Invoice Number')
    notes = TextAreaField('Notes')
    submit = SubmitField('Record Purchase')
    
    def __init__(self, *args, **kwargs):
        super(PurchaseForm, self).__init__(*args, **kwargs)
        self.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.all()]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_picture(form_picture):
    """Save uploaded picture and return filename"""
    random_hex = str(uuid.uuid4())
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', 'uploads', picture_fn)
    
    # Resize image
    output_size = (400, 400)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)
    
    return picture_fn

# Category routes
@products_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('products/categories.html', title='Categories', categories=categories)

@products_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{category.name}" added successfully!', 'success')
        return redirect(url_for('products.categories'))
    
    return render_template('products/add_category.html', title='Add Category', form=form)

@products_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        flash(f'Category "{category.name}" updated successfully!', 'success')
        return redirect(url_for('products.categories'))
    
    return render_template('products/edit_category.html', title='Edit Category', form=form, category=category)

@products_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    try:
        category = Category.query.get_or_404(id)
        if category.products:
            return jsonify({'success': False, 'message': f'Cannot delete category with {len(category.products)} existing products!'})
        
        category_name = category.name
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Category "{category_name}" deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Product routes
@products_bp.route('/')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category_id = request.args.get('category', 0, type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            Product.name.contains(search) | Product.barcode.contains(search)
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.all()
    
    return render_template('products/products.html', 
                         title='Products', 
                         products=products, 
                         categories=categories,
                         search=search,
                         current_category=category_id)

@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Handle image upload
        image_filename = None
        if form.image.data:
            image_filename = save_picture(form.image.data)
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            barcode=form.barcode.data,
            category_id=form.category_id.data,
            buying_price=form.buying_price.data,
            selling_price=form.selling_price.data,
            tax_inclusive=form.tax_inclusive.data,
            stock_quantity=form.stock_quantity.data,
            reorder_level=form.reorder_level.data,
            image_filename=image_filename
        )
        
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" added successfully!', 'success')
        return redirect(url_for('products.products'))
    
    return render_template('products/add_product.html', title='Add Product', form=form)

@products_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            image_filename = save_picture(form.image.data)
            # Delete old image if exists
            if product.image_filename:
                old_path = os.path.join(current_app.root_path, 'static', 'uploads', product.image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            product.image_filename = image_filename
        
        product.name = form.name.data
        product.description = form.description.data
        product.barcode = form.barcode.data
        product.category_id = form.category_id.data
        product.buying_price = form.buying_price.data
        product.selling_price = form.selling_price.data
        product.tax_inclusive = form.tax_inclusive.data
        product.reorder_level = form.reorder_level.data
        
        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('products.products'))
    
    return render_template('products/edit_product.html', title='Edit Product', form=form, product=product)

@products_bp.route('/view/<int:id>')
@login_required
def view_product(id):
    product = Product.query.get_or_404(id)
    return render_template('products/view_product.html', title=product.name, product=product)

@products_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_product(id):
    try:
        product = Product.query.get_or_404(id)
        product.is_active = not product.is_active
        db.session.commit()
        
        status = 'activated' if product.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'Product "{product.name}" has been {status}.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@products_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    try:
        product = Product.query.get_or_404(id)
        
        # Check if product has been sold
        from app.models import SaleItem
        sales_count = SaleItem.query.filter_by(product_id=id).count()
        if sales_count > 0:
            return jsonify({'success': False, 'message': f'Cannot delete product. It has {sales_count} sale records. Consider deactivating instead.'})
        
        # Delete product image if exists
        if product.image_filename:
            import os
            from flask import current_app
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', product.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Product "{product_name}" has been deleted successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Stock management
@products_bp.route('/stock')
@login_required
def stock():
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    
    query = Product.query.filter_by(is_active=True)
    
    if filter_type == 'low':
        query = query.filter(Product.stock_quantity <= Product.reorder_level)
    elif filter_type == 'out':
        query = query.filter(Product.stock_quantity == 0)
    
    products = query.order_by(Product.stock_quantity.asc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('products/stock.html', 
                         title='Stock Management', 
                         products=products,
                         current_filter=filter_type)

# Supplier routes
@products_bp.route('/suppliers')
@login_required
@admin_required
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('products/suppliers.html', title='Suppliers', suppliers=suppliers)

@products_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f'Supplier "{supplier.name}" added successfully!', 'success')
        return redirect(url_for('products.suppliers'))
    
    return render_template('products/add_supplier.html', title='Add Supplier', form=form)

# Purchase routes
@products_bp.route('/purchases')
@login_required
@admin_required
def purchases():
    page = request.args.get('page', 1, type=int)
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('products/purchases.html', title='Purchases', purchases=purchases)

@products_bp.route('/purchases/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_purchase():
    form = PurchaseForm()
    if form.validate_on_submit():
        purchase = Purchase(
            supplier_id=form.supplier_id.data,
            invoice_number=form.invoice_number.data,
            notes=form.notes.data,
            total_amount=0,  # Will be updated when items are added
            created_by=current_user.id
        )
        db.session.add(purchase)
        db.session.commit()
        
        flash('Purchase record created. Now add items to the purchase.', 'info')
        return redirect(url_for('products.add_purchase_items', purchase_id=purchase.id))
    
    return render_template('products/add_purchase.html', title='Record Purchase', form=form)

@products_bp.route('/purchases/<int:purchase_id>/items', methods=['GET', 'POST'])
@login_required
@admin_required
def add_purchase_items(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Clear existing items
        PurchaseItem.query.filter_by(purchase_id=purchase.id).delete()
        
        total_amount = 0
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if product:
                # Create purchase item
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['quantity'] * item_data['unit_price']
                )
                db.session.add(purchase_item)
                
                # Update product stock and buying price
                product.stock_quantity += item_data['quantity']
                product.buying_price = item_data['unit_price']
                
                total_amount += purchase_item.total_price
        
        # Update purchase total
        purchase.total_amount = total_amount
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Purchase items saved successfully!'})
    
    products = Product.query.filter_by(is_active=True).all()
    return render_template('products/add_purchase_items.html', 
                         title='Add Purchase Items', 
                         purchase=purchase,
                         products=products)

# API endpoints
@products_bp.route('/api/search')
@login_required
def api_search_products():
    query = request.args.get('q', '')
    products = Product.query.filter(
        Product.is_active == True,
        Product.name.contains(query) | Product.barcode.contains(query)
    ).limit(10).all()
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'price': float(product.selling_price),
            'stock': product.stock_quantity
        })
    
    return jsonify(results)

@products_bp.route('/api/product/<int:product_id>')
@login_required
def api_get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'barcode': product.barcode,
        'price': float(product.selling_price),
        'stock': product.stock_quantity,
        'category': product.category.name,
        'description': product.description
    })