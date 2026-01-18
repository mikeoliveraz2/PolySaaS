#!/usr/bin/env python
"""
Copy SocialApp from public schema to olient (tenant) schema
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
import json

def copy_socialapp_to_tenant():
    print("=" * 60)
    print("Copying SocialApp from public to olient schema")
    print("=" * 60)

    with connection.cursor() as cursor:
        # Check if SocialApp exists in public
        cursor.execute(
            "SELECT id, provider, provider_id, name, client_id, secret, key, settings FROM public.socialaccount_socialapp WHERE provider = %s;",
            ['google']
        )
        row = cursor.fetchone()

        if not row:
            print("❌ No Google SocialApp found in public schema!")
            return

        app_id, provider, provider_id, name, client_id, secret, key, settings = row
        print(f"✅ Found SocialApp in public schema:")
        print(f"   ID: {app_id}")
        print(f"   Provider: {provider}")
        print(f"   Name: {name}")
        print(f"   Client ID: {client_id[:20]}...")

        # Convert settings to JSON string if it's a dict
        if isinstance(settings, dict):
            settings_json = json.dumps(settings)
        else:
            settings_json = settings or '{}'

        # Copy to olient schema
        try:
            cursor.execute("""
                INSERT INTO olient.socialaccount_socialapp
                (id, provider, provider_id, name, client_id, secret, key, settings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    provider = EXCLUDED.provider,
                    provider_id = EXCLUDED.provider_id,
                    name = EXCLUDED.name,
                    client_id = EXCLUDED.client_id,
                    secret = EXCLUDED.secret,
                    key = EXCLUDED.key,
                    settings = EXCLUDED.settings;
            """, [app_id, provider, provider_id, name, client_id, secret, key, settings_json])

            print(f"\n✅ Copied SocialApp to olient schema!")

            # Verify
            cursor.execute(
                "SELECT COUNT(*) FROM olient.socialaccount_socialapp WHERE provider = %s;",
                ['google']
            )
            count = cursor.fetchone()[0]
            print(f"✅ Verified: {count} Google app(s) in olient schema")

        except Exception as e:
            print(f"❌ Error copying to olient schema: {e}")
            import traceback
            traceback.print_exc()
            return

    print("\n" + "=" * 60)
    print("Done! You can now save the SocialApp in the admin.")
    print("=" * 60)

if __name__ == '__main__':
    copy_socialapp_to_tenant()

