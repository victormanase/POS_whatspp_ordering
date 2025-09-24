#!/usr/bin/env python3
"""
Test login functionality and debug authentication
"""
from app import create_app
from app.models import db, User

def test_login():
    """Test login functionality"""
    app = create_app()
    
    with app.app_context():
        print("=== User Authentication Test ===")
        
        # Get all users
        users = User.query.all()
        print(f"Total users in database: {len(users)}")
        
        for user in users:
            print(f"\nUser Details:")
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Is Active: {user.is_active}")
            print(f"Password Hash: {user.password_hash[:50]}..." if user.password_hash else "No password hash")
            
            # Test password verification
            test_passwords = ['admin123', 'admin', '123456', 'password']
            
            print(f"\nTesting passwords for user '{user.username}':")
            for password in test_passwords:
                if user.check_password(password):
                    print(f"✅ Password '{password}' works!")
                    break
                else:
                    print(f"❌ Password '{password}' failed")
            
            # Let's also test if we can set a simple password
            print(f"\nSetting password 'admin123' for user '{user.username}'")
            user.set_password('admin123')
            db.session.commit()
            
            if user.check_password('admin123'):
                print(f"✅ Password 'admin123' now works for '{user.username}'!")
            else:
                print(f"❌ Still can't authenticate '{user.username}' with 'admin123'")

if __name__ == '__main__':
    test_login()