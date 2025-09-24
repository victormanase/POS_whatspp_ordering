#!/usr/bin/env python3
"""
Initialize default system settings
"""
from app import create_app
from app.models import db, SystemSettings

def init_default_settings():
    """Initialize default system settings"""
    app = create_app()
    
    with app.app_context():
        # Check if default currency setting exists
        currency_setting = SystemSettings.query.filter_by(key='default_currency').first()
        
        if not currency_setting:
            # Create default currency setting
            default_currency = SystemSettings(
                key='default_currency',
                value='TSH',
                description='Default system currency - Tanzanian Shilling'
            )
            db.session.add(default_currency)
            print("Added default currency setting: TSH")
        else:
            print(f"Currency setting already exists: {currency_setting.value}")
        
        # Add other default settings
        default_settings = [
            ('company_name', '', 'Company name for receipts and reports'),
            ('company_address', '', 'Company address for receipts'),
            ('company_phone', '', 'Company phone number'),
            ('company_email', '', 'Company email address'),
            ('receipt_footer', 'Thank you for your business!', 'Footer message for receipts'),
        ]
        
        for key, value, description in default_settings:
            existing = SystemSettings.query.filter_by(key=key).first()
            if not existing:
                setting = SystemSettings(key=key, value=value, description=description)
                db.session.add(setting)
                print(f"Added setting: {key}")
            else:
                print(f"Setting already exists: {key}")
        
        try:
            db.session.commit()
            print("Default settings initialized successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing settings: {e}")

if __name__ == '__main__':
    init_default_settings()