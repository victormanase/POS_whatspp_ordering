#!/usr/bin/env python3
"""
Check users in the database
"""
from app import create_app
from app.models import db, User

def check_users():
    """Check users in the database"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        print(f"Total users: {len(users)}")
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print("-" * 30)
        
        if not users:
            print("No users found. Creating admin user...")
            admin = User(
                username='admin',
                email='admin@possystem.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")
            print("Username: admin")
            print("Password: admin123")

if __name__ == '__main__':
    check_users()