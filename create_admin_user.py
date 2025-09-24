#!/usr/bin/env python3
"""
Create initial admin user for the POS system
"""
from app import create_app
from app.models import db, User

def create_admin_user():
    """Create the initial admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print(f"Admin user already exists: {admin_user.username}")
            # Let's check the count to see if there are actually users
            user_count = User.query.count()
            print(f"Total users in database: {user_count}")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@possystem.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')  # Change this password after first login
        
        db.session.add(admin)
        
        try:
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("IMPORTANT: Please change the password after first login!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    create_admin_user()