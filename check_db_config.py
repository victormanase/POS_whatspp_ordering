#!/usr/bin/env python3
"""
Check database configuration and connection
"""
from app import create_app
from app.models import db, User
import os

def check_db_config():
    """Check database configuration"""
    app = create_app()
    
    with app.app_context():
        print("=== Database Configuration Check ===")
        
        # Check environment variables
        print(f"DATABASE_URL from env: {os.environ.get('DATABASE_URL', 'Not set')}")
        print(f"DEV_DATABASE_URL from env: {os.environ.get('DEV_DATABASE_URL', 'Not set')}")
        print(f"FLASK_CONFIG from env: {os.environ.get('FLASK_CONFIG', 'Not set')}")
        
        # Check Flask config
        print(f"\nFlask config:")
        print(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"DEBUG: {app.config.get('DEBUG')}")
        print(f"SQLALCHEMY_TRACK_MODIFICATIONS: {app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS')}")
        
        # Test database connection
        try:
            print(f"\n=== Database Connection Test ===")
            
            # Try to query users
            users = User.query.all()
            print(f"Total users found: {len(users)}")
            
            for user in users:
                print(f"  - {user.username} ({user.email}) - Role: {user.role} - Active: {user.is_active}")
            
            # Test specific user lookup like in login
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f"\n✅ Admin user found via query: {admin_user.username}")
                print(f"   ID: {admin_user.id}")
                print(f"   Email: {admin_user.email}")
                print(f"   Role: {admin_user.role}")
                if admin_user.check_password('admin123'):
                    print(f"   ✅ Password 'admin123' works")
                else:
                    print(f"   ❌ Password 'admin123' failed")
            else:
                print(f"\n❌ Admin user NOT found via query")
                
        except Exception as e:
            print(f"\n❌ Database connection failed: {e}")

if __name__ == '__main__':
    check_db_config()