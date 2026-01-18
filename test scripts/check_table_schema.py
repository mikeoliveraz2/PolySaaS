#!/usr/bin/env python3
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name='dose_passthroughendpoint'
        ORDER BY ordinal_position
    """)
    for name, nullable, default in cursor.fetchall():
        nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
        default_str = f" DEFAULT {default}" if default else ""
        print(f"{name:40} {nullable_str:10} {default_str}")
