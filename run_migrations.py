#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


import argparse

def main():
    parser = argparse.ArgumentParser(description="Run shared and tenant migrations for all schemas, with optional skip.")
    parser.add_argument('--skip', type=str, help='Schema name to skip during tenant migrations.')
    args = parser.parse_args()

    try:
        print("Running migrations for all schemas (shared and tenant)...")
        execute_from_command_line(['manage.py', 'migrate_all_schemas'])
        print("All migrations completed successfully.")

    except Exception as e:
        print(f"Error during migrations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
