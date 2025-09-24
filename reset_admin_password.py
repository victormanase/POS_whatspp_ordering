#!/usr/bin/env python3
"""
Reset admin password to a known value
"""
from app import create_app
from app.models import db, User

def reset_admin_password():
    """Reset admin password"""
    app = create_app()
    
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            # Set a known password
            admin_user.set_password('admin123')
            db.session.commit()
            
            print("Admin password has been reset!")
            print("Username: admin")
            print("Password: admin123")
            print(f"Email: {admin_user.email}")
            print(f"Role: {admin_user.role}")
        else:
            print("Admin user not found!")

if __name__ == '__main__':
    reset_admin_password()