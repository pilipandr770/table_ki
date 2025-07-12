#!/usr/bin/env python3
"""
Script to create an admin user
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Role

def create_admin_user(email, password="admin123", first_name="Admin", last_name="User"):
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            # Make existing user admin
            existing_user.role = Role.ADMIN
            existing_user.is_approved = True
            db.session.commit()
            print(f"✅ User {email} is now an admin!")
            return existing_user
        
        # Create new admin user
        admin_user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            role=Role.ADMIN,
            is_approved=True,
            language_preference='ru'  # Set Russian as default
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"✅ Admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"👤 Name: {first_name} {last_name}")
        print(f"🔐 Role: Administrator")
        
        return admin_user

if __name__ == "__main__":
    email = "pilipandr79@icloud.com"
    admin_user = create_admin_user(email)
    print("\n🎉 Admin user setup complete!")
    print("You can now log in at: http://127.0.0.1:5000/auth/login")
