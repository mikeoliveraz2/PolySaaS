#!/usr/bin/env python
"""
Check if SocialApp was saved correctly with sites
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

print("=" * 60)
print("Checking SocialApp Configuration")
print("=" * 60)

# Check olient schema
print("\n=== Olient Schema ===")
with connection.cursor() as cursor:
    cursor.execute("SET LOCAL search_path TO olient,public;")
    app = SocialApp.objects.filter(provider='google').first()
    if app:
        print(f"✅ SocialApp found:")
        print(f"   ID: {app.id}")
        print(f"   Provider: {app.provider}")
        print(f"   Provider ID: {app.provider_id}")
        print(f"   Name: {app.name}")
        print(f"   Sites count: {app.sites.count()}")
        sites = list(app.sites.all())
        if sites:
            print(f"   ✅ Sites: {[s.domain for s in sites]}")
            print(f"   Site IDs: {[s.id for s in sites]}")
        else:
            print(f"   ⚠️  No sites associated")
    else:
        print("❌ No SocialApp found in olient schema")

# Check public schema
print("\n=== Public Schema ===")
with connection.cursor() as cursor:
    cursor.execute("SELECT id, provider, name FROM public.socialaccount_socialapp WHERE provider = %s;", ['google'])
    row = cursor.fetchone()
    if row:
        print(f"✅ SocialApp found: ID {row[0]}, Name: {row[1]}")
    else:
        print("❌ No SocialApp found in public schema")

# Check sites relationship table
print("\n=== Sites Relationship Table (olient) ===")
with connection.cursor() as cursor:
    cursor.execute("SELECT socialapp_id, site_id FROM olient.socialaccount_socialapp_sites;")
    rows = cursor.fetchall()
    if rows:
        print(f"✅ Found {len(rows)} site relationship(s):")
        for row in rows:
            print(f"   SocialApp {row[0]} -> Site {row[1]}")
        # Get site details
        site_ids = [str(row[1]) for row in rows]
        placeholders = ','.join(site_ids)
        cursor.execute(f"SELECT id, domain FROM public.django_site WHERE id IN ({placeholders});")
        sites = cursor.fetchall()
        print(f"\n   Site details:")
        for site in sites:
            print(f"     Site {site[0]}: {site[1]}")
    else:
        print("⚠️  No site relationships found in olient.socialaccount_socialapp_sites")

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
if app and app.sites.count() > 0:
    print("✅ SocialApp is configured correctly with sites!")
    print("   You can try logging in now.")
else:
    print("⚠️  SocialApp exists but has no sites associated.")
    print("   The get_app method should still find it (checks for apps with no sites).")

