#!/usr/bin/env python3
"""
Setup script for AI Prompt Generator Platform
This script automates the initial setup process.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_env_file():
    """Create .env file from template."""
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            shutil.copy('env.example', '.env')
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your configuration")
        else:
            print("❌ env.example not found")
            return False
    else:
        print("ℹ️  .env file already exists")
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up AI Prompt Generator Platform")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create virtual environment
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            sys.exit(1)
    else:
        print("ℹ️  Virtual environment already exists")
    
    # Determine activation command
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate'
        pip_cmd = 'venv\\Scripts\\pip'
        python_cmd = 'venv\\Scripts\\python'
    else:  # Unix/Linux/macOS
        activate_cmd = 'source venv/bin/activate'
        pip_cmd = 'venv/bin/pip'
        python_cmd = 'venv/bin/python'
    
    # Install dependencies
    if not run_command(f'{pip_cmd} install -r requirements.txt', 'Installing dependencies'):
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Run migrations
    if not run_command(f'{python_cmd} manage.py makemigrations', 'Creating database migrations'):
        sys.exit(1)
    
    if not run_command(f'{python_cmd} manage.py migrate', 'Running database migrations'):
        sys.exit(1)
    
    # Set up initial data
    if not run_command(f'{python_cmd} manage.py setup_initial_data', 'Setting up initial data'):
        print("⚠️  Initial data setup failed, but you can continue")
    
    # Collect static files
    if not run_command(f'{python_cmd} manage.py collectstatic --noinput', 'Collecting static files'):
        print("⚠️  Static files collection failed, but you can continue")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Create a superuser: python manage.py createsuperuser")
    print("3. Run the development server: python manage.py runserver")
    print("4. Visit http://localhost:8000")
    print("\n📚 For more information, see README.md")
    print("=" * 50)


if __name__ == '__main__':
    main() 