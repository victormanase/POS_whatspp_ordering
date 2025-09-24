#!/usr/bin/env python3
"""
Debug login process step by step
"""
from app import create_app
from app.models import db, User
from flask import url_for

def debug_login():
    """Debug login process"""
    app = create_app()
    
    with app.app_context():
        print("=== Login Debug Test ===")
        
        # Test 1: Find user
        username = "admin"
        password = "admin123"
        
        print(f"1. Looking for user: {username}")
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"✅ User found: {user.username} (ID: {user.id})")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Active: {user.is_active}")
        else:
            print(f"❌ User '{username}' not found!")
            return
        
        # Test 2: Check password
        print(f"\n2. Testing password: {password}")
        if user.check_password(password):
            print("✅ Password is correct!")
        else:
            print("❌ Password is incorrect!")
            return
        
        # Test 3: Check if user is active
        print(f"\n3. Checking if user is active")
        if user.is_active:
            print("✅ User is active!")
        else:
            print("❌ User is not active!")
            return
        
        print("\n✅ All login checks passed!")
        print("\nLogin credentials are working correctly.")
        print("The issue might be with:")
        print("- CSRF token")
        print("- Form validation")
        print("- Session management")
        print("- Template rendering")

if __name__ == '__main__':
    debug_login()