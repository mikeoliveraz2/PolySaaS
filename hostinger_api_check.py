"""Explore Hostinger API to find WordPress management endpoints."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

API_TOKEN = "FVz0JMyjaxdHZ7tEaH9kpd9sTq4p3VacGFF9xXQda6447e3a"
BASE = "https://api.hostinger.com"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

# Try common Hostinger API endpoints
endpoints = [
    "/api/v1/wordpress",
    "/api/v1/wordpress/sites",
    "/api/v1/hosting",
    "/api/v1/hosting/websites",
    "/api/v1/domains",
    "/api/v1/account",
    "/v1/wordpress",
    "/v1/hosting",
]

for ep in endpoints:
    try:
        r = requests.get(f"{BASE}{ep}", headers=headers, timeout=10)
        print(f"{ep}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Response: {json.dumps(data)[:300]}")
        elif r.status_code != 404:
            print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"{ep}: ERROR - {e}")
