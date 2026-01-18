#!/usr/bin/env python
"""
Check OAuth tokens in both public and tenant schemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

user = User.objects.filter(username='admin').first()
if not user:
    print("ERROR: User 'admin' not found")
    exit(1)

print("="*60)
print(f"Checking OAuth tokens for user: {user.username} (ID: {user.id})")
print("="*60)
print()

# Check olient schema
print("=== Olient Schema ===")
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO olient,public;")
    c.execute("""
        SELECT id, provider, uid
        FROM socialaccount_socialaccount
        WHERE user_id = %s;
    """, [user.id])
    accounts = c.fetchall()
    print(f"SocialAccount records: {len(accounts)}")
    for acc in accounts:
        print(f"  ID: {acc[0]}, Provider: {acc[1]}, UID: {acc[2]}")

    if accounts:
        account_ids = [acc[0] for acc in accounts]
        c.execute("""
            SELECT id, account_id, token, expires_at
            FROM socialaccount_socialtoken
            WHERE account_id = ANY(%s);
        """, [account_ids])
        tokens = c.fetchall()
        print(f"SocialToken records: {len(tokens)}")
        for tok in tokens:
            print(f"  ID: {tok[0]}, Account ID: {tok[1]}, Token: {tok[2][:20]}..., Expires: {tok[3]}")

print()
print("=== Public Schema ===")
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO public;")
    c.execute("""
        SELECT id, provider, uid
        FROM socialaccount_socialaccount
        WHERE user_id = %s;
    """, [user.id])
    accounts = c.fetchall()
    print(f"SocialAccount records: {len(accounts)}")
    for acc in accounts:
        print(f"  ID: {acc[0]}, Provider: {acc[1]}, UID: {acc[2]}")

    if accounts:
        account_ids = [acc[0] for acc in accounts]
        c.execute("""
            SELECT id, account_id, token, expires_at
            FROM socialaccount_socialtoken
            WHERE account_id = ANY(%s);
        """, [account_ids])
        tokens = c.fetchall()
        print(f"SocialToken records: {len(tokens)}")
        for tok in tokens:
            print(f"  ID: {tok[0]}, Account ID: {tok[1]}, Token: {tok[2][:20]}..., Expires: {tok[3]}")

print()
print("="*60)
print("Recommendation:")
print("="*60)
if not accounts:
    print("❌ No OAuth tokens found. The OAuth login may not have completed properly.")
    print("   Please try logging in with Google again:")
    print("   http://localhost:8000/accounts/google/login/?process=connect&next=/dose/gmail-inbox/")
else:
    print("✅ OAuth tokens found. The issue may be with token lookup in the Gmail view.")
