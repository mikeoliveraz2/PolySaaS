#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

## Removed django-tenants dependency
from django.db import connection

# Create auth_user table manually in demo schema
with schema_context('demo'):
    with connection.cursor() as cursor:
        print("Creating auth_user table manually in demo schema...")
        
        # Create auth_user table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_user (
                id SERIAL PRIMARY KEY,
                password VARCHAR(128) NOT NULL,
                last_login TIMESTAMP WITH TIME ZONE,
                is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                username VARCHAR(150) NOT NULL UNIQUE,
                first_name VARCHAR(150) NOT NULL DEFAULT '',
                last_name VARCHAR(150) NOT NULL DEFAULT '',
                email VARCHAR(254) NOT NULL DEFAULT '',
                is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """)
        
        # Create content types table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS django_content_type (
                id SERIAL PRIMARY KEY,
                app_label VARCHAR(100) NOT NULL,
                model VARCHAR(100) NOT NULL,
                UNIQUE(app_label, model)
            )
        """)
        
        # Create permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_permission (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                content_type_id INTEGER REFERENCES django_content_type(id),
                codename VARCHAR(100) NOT NULL,
                UNIQUE(content_type_id, codename)
            )
        """)
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS django_session (
                session_key VARCHAR(40) PRIMARY KEY,
                session_data TEXT NOT NULL,
                expire_date TIMESTAMP WITH TIME ZONE NOT NULL
            )
        """)
        
        # Create user groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_group (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL UNIQUE
            )
        """)
        
        # Create user-group relationship table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_user_groups (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES auth_user(id),
                group_id INTEGER REFERENCES auth_group(id),
                UNIQUE(user_id, group_id)
            )
        """)
        
        # Create user permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_user_user_permissions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES auth_user(id),
                permission_id INTEGER REFERENCES auth_permission(id),
                UNIQUE(user_id, permission_id)
            )
        """)
        
        print("✓ All auth tables created successfully!")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'demo' 
            AND table_name LIKE 'auth_%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"Auth tables in demo schema: {[t[0] for t in tables]}")
        
        # Create a test superuser
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                email='admin@demo.com',
                password='admin123'
            )
            print(f"✓ Created superuser: {user.username}")
        else:
            print("✓ Superuser 'admin' already exists")
            
        user_count = User.objects.count()
        print(f"✓ Demo tenant now has {user_count} users")

print("SUCCESS: Demo tenant auth tables created!")
print("You can now login at http://localhost:8000/tenant/demo/admin/ with:")
print("Username: admin")
print("Password: admin123")