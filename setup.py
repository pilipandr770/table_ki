#!/usr/bin/env python3
"""
Setup script for Excel Chat Assistant Flask Application
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a system command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'uploads',
        'app/translations',
        'logs',
        'instance'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_environment():
    """Set up the development environment"""
    print("=== Excel Chat Assistant Setup ===\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    
    print(f"✓ Python {sys.version} detected")
    
    # Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Install dependencies
    print("\n2. Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Initialize database
    print("\n3. Setting up database...")
    if not run_command("flask db init", "Initializing database"):
        print("Database might already be initialized, continuing...")
    
    if not run_command("flask db migrate -m 'Initial migration'", "Creating migration"):
        print("Migration might already exist, continuing...")
    
    if not run_command("flask db upgrade", "Applying migrations"):
        return False
    
    # Set up translations
    print("\n4. Setting up translations...")
    if not run_command("pybabel extract -F babel.cfg -k _l -o messages.pot .", "Extracting messages"):
        print("Translation extraction failed, but continuing...")
    
    # Initialize German translations
    if not run_command("pybabel init -i messages.pot -d app/translations -l de", "Initializing German translations"):
        print("German translations might already exist, continuing...")
    
    # Initialize Russian translations
    if not run_command("pybabel init -i messages.pot -d app/translations -l ru", "Initializing Russian translations"):
        print("Russian translations might already exist, continuing...")
    
    # Create admin user
    print("\n5. Setting up admin user...")
    if not run_command("flask deploy", "Creating admin user"):
        print("Admin user creation failed, you may need to create one manually")
    
    print("\n=== Setup Complete! ===")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your environment variables")
    print("2. Set up your OpenAI API key in .env")
    print("3. Set up your Stripe keys in .env")
    print("4. Run 'python run.py' to start the development server")
    print("5. Visit http://localhost:5000 to access the application")
    print("6. Default admin login: admin@example.com / admin123")
    
    return True

if __name__ == "__main__":
    # Set Flask environment variables
    os.environ['FLASK_APP'] = 'run.py'
    os.environ['FLASK_ENV'] = 'development'
    
    success = setup_environment()
    sys.exit(0 if success else 1)
