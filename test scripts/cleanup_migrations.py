#!/usr/bin/env python
"""
Migration cleanup and fresh start script for session-based tenant system
This script helps transition from django-tenants to session-based tenancy
"""
import os
import sys
import shutil
from pathlib import Path

def cleanup_migrations():
    """Remove existing migration files to start fresh"""
    
    # List of app directories to clean
    apps_to_clean = ['dose', 'parameters']
    
    print("🧹 Cleaning up existing migrations...")
    
    for app_name in apps_to_clean:
        migrations_dir = Path(f"{app_name}/migrations")
        
        if migrations_dir.exists():
            # Keep __init__.py but remove everything else
            for file in migrations_dir.glob("*.py"):
                if file.name != "__init__.py":
                    print(f"  Removing {file}")
                    file.unlink()
            
            # Remove __pycache__ directory
            pycache_dir = migrations_dir / "__pycache__"
            if pycache_dir.exists():
                print(f"  Removing {pycache_dir}")
                shutil.rmtree(pycache_dir)
        else:
            print(f"  Creating migrations directory for {app_name}")
            migrations_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py
            init_file = migrations_dir / "__init__.py"
            init_file.write_text("")
    
    print("✅ Migration cleanup complete!")
    print("\nNext steps:")
    print("1. Run: python manage.py makemigrations")
    print("2. Run: python manage.py migrate")
    print("3. Run: python manage.py createsuperuser (if needed)")
    print("4. Visit: http://localhost:8000/dose/setup-demo/")

if __name__ == "__main__":
    cleanup_migrations()
