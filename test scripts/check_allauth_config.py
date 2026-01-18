import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("=== Checking Allauth Database Tables ===\n")

with connection.cursor() as cursor:
    # Check if socialaccount tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'socialaccount%'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print(f"Found {len(tables)} socialaccount tables:")
    for table in tables:
        print(f"  - {table[0]}")

print("\n=== Checking SOCIALACCOUNT_STORE_TOKENS Setting ===")

from django.conf import settings
print(f"SOCIALACCOUNT_STORE_TOKENS = {getattr(settings, 'SOCIALACCOUNT_STORE_TOKENS', 'NOT SET')}")

print("\n=== Checking allauth version ===")
import allauth
print(f"django-allauth version: {allauth.__version__}")

print("\n=== Diagnosis ===")
if not tables:
    print("❌ ERROR: socialaccount tables don't exist!")
    print("   Run: python manage.py migrate")
elif len(tables) < 3:
    print("⚠️  WARNING: Missing some socialaccount tables")
    print("   Expected: socialaccount_socialaccount, socialaccount_socialtoken, socialaccount_socialapp")
else:
    print("✓ Tables exist")

if not getattr(settings, 'SOCIALACCOUNT_STORE_TOKENS', False):
    print("❌ ERROR: SOCIALACCOUNT_STORE_TOKENS is False or not set!")
else:
    print("✓ SOCIALACCOUNT_STORE_TOKENS is True")
