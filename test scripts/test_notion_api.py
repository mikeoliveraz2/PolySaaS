#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Notion Integration directly via API
Bypass the UI loading issue and verify everything works
"""
import requests
import json
import sys
import io

# Fix Unicode output for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*100)
print("NOTION API TEST - Bypass UI Issues")
print("="*100)

# Your credentials (replace with actual values)
NOTION_API_KEY = input("Enter your Notion Integration Token (ntn_...): ").strip()
NOTION_DATABASE_ID = input("Enter your Notion Database ID: ").strip()

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    print("ERROR: Missing credentials")
    sys.exit(1)

headers = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

# Test 1: Verify Integration Connection
print("\n[TEST 1] Verify Notion Integration")
print("-"*100)

try:
    response = requests.get(
        'https://api.notion.com/v1/users/me',
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        user_data = response.json()
        print(f"✓ Connected! User: {user_data.get('name')}")
    else:
        print(f"✗ Connection failed: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 2: Get Database Info
print("\n[TEST 2] Get Database Information")
print("-"*100)

try:
    response = requests.get(
        f'https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}',
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        db_data = response.json()
        print(f"✓ Database found!")
        print(f"  Title: {db_data.get('title', [{}])[0].get('plain_text', 'Unnamed')}")
        print(f"  ID: {db_data['id']}")

        # Show properties
        print(f"\n  Properties (fields):")
        for prop_name, prop_data in db_data.get('properties', {}).items():
            prop_type = prop_data.get('type')
            print(f"    - {prop_name} ({prop_type})")
    else:
        print(f"✗ Database not found: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 3: Query Database
print("\n[TEST 3] Query Database for Existing Records")
print("-"*100)

try:
    response = requests.post(
        f'https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query',
        headers=headers,
        json={},
        timeout=10
    )

    if response.status_code == 200:
        query_data = response.json()
        records = query_data.get('results', [])
        print(f"✓ Query successful! Found {len(records)} records")

        if records:
            print("\n  Existing records:")
            for record in records[:5]:  # Show first 5
                props = record.get('properties', {})
                print(f"    - {record['id'][:8]}... ({len(props)} fields)")
    else:
        print(f"✗ Query failed: {response.status_code}")
        print(f"  Response: {response.text}")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Create Test Record
print("\n[TEST 4] Create Test Contact Record")
print("-"*100)

try:
    # Build payload - this depends on your database schema
    payload = {
        'parent': {'database_id': NOTION_DATABASE_ID},
        'properties': {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': 'Test Contact - PolySaaS Demo'
                        }
                    }
                ]
            },
            'Email': {
                'email': 'test@dosev3.com'
            }
        }
    }

    response = requests.post(
        'https://api.notion.com/v1/pages',
        headers=headers,
        json=payload,
        timeout=10
    )

    if response.status_code == 200:
        page_data = response.json()
        page_id = page_data['id']
        print(f"✓ Test record created!")
        print(f"  Page ID: {page_id}")
        print(f"  URL: https://notion.so/{page_id.replace('-', '')}")
    else:
        print(f"✗ Creation failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        print("\n  Tip: Make sure your database has 'Name' and 'Email' fields")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Summary
print("\n" + "="*100)
print("SUMMARY")
print("="*100)

print("""
If all tests passed, your Notion integration is working!

Next steps:
1. Go back to Notion web UI (F5 to refresh)
2. You should now see your "Test Contact - PolySaaS Demo" record
3. Add more test records to trigger the PolySaaS automation
4. Check osTicket to see synced contacts
5. Check Gmail for notification emails

If tests failed:
- Double-check your integration token (must start with 'ntn_')
- Verify integration is connected to your database (Share button)
- Make sure database has 'Name' and 'Email' fields
- Check that your database ID is correct

Ready to run the full pipeline!
""")

print("="*100)
