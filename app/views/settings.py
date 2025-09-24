"""
Settings management views
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import SystemSettings, db, User
from app.utils.currency import CurrencyManager

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Settings dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get current settings
    current_currency = CurrencyManager.get_current_currency()
    currency_list = CurrencyManager.get_currency_list()
    
    # Get other system settings
    settings = SystemSettings.query.all()
    settings_dict = {setting.key: setting.value for setting in settings}
    
    return render_template('settings/index.html', 
                         current_currency=current_currency,
                         currency_list=currency_list,
                         settings=settings_dict)

@settings_bp.route('/currency', methods=['GET', 'POST'])
@login_required
def currency_settings():
    """Currency settings management"""
    if not current_user.is_admin:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'}), 403
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            currency_code = request.form.get('currency_code')
            if not currency_code:
                return jsonify({'success': False, 'message': 'Currency code is required'}), 400
            
            # Set the new currency
            CurrencyManager.set_currency(currency_code)
            
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'success': True, 
                    'message': f'Currency updated to {currency_code}',
                    'currency': CurrencyManager.get_current_currency()
                })
            else:
                flash(f'Currency updated to {currency_code} successfully!', 'success')
                return redirect(url_for('settings.index'))
                
        except ValueError as e:
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'message': str(e)}), 400
            flash(str(e), 'error')
            return redirect(url_for('settings.index'))
        except Exception as e:
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'message': 'Failed to update currency'}), 500
            flash('Failed to update currency. Please try again.', 'error')
            return redirect(url_for('settings.index'))
    
    # GET request - return currency info
    return jsonify({
        'current_currency': CurrencyManager.get_current_currency(),
        'available_currencies': CurrencyManager.get_currency_list()
    })

@settings_bp.route('/general', methods=['POST'])
@login_required
def update_general_settings():
    """Update general system settings"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'}), 403
    
    try:
        # Get form data
        company_name = request.form.get('company_name')
        company_address = request.form.get('company_address')
        company_phone = request.form.get('company_phone')
        company_email = request.form.get('company_email')
        receipt_footer = request.form.get('receipt_footer')
        
        # Update or create settings
        settings_to_update = [
            ('company_name', company_name, 'Company name'),
            ('company_address', company_address, 'Company address'),
            ('company_phone', company_phone, 'Company phone number'),
            ('company_email', company_email, 'Company email address'),
            ('receipt_footer', receipt_footer, 'Receipt footer message')
        ]
        
        for key, value, description in settings_to_update:
            if value is not None:
                setting = SystemSettings.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = SystemSettings(key=key, value=value, description=description)
                    db.session.add(setting)
        
        db.session.commit()
        
        flash('General settings updated successfully!', 'success')
        return redirect(url_for('settings.index'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update settings. Please try again.', 'error')
        return redirect(url_for('settings.index'))

@settings_bp.route('/users')
@login_required
def user_management():
    """User management page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('settings/users.html', users=users)

@settings_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow disabling self
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot disable your own account'}), 400
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({
            'success': True, 
            'message': f'User {user.username} has been {status}',
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update user status'}), 500

@settings_bp.route('/users/admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin_status(user_id):
    """Toggle user admin status"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow removing admin from self if it's the only admin
    if user.id == current_user.id:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            return jsonify({'success': False, 'message': 'Cannot remove admin privileges from the last admin'}), 400
    
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        
        status = 'granted' if user.is_admin else 'revoked'
        return jsonify({
            'success': True, 
            'message': f'Admin privileges {status} for user {user.username}',
            'is_admin': user.is_admin
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update admin status'}), 500