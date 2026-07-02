"""
Fire a mock HubSpot contact creation webhook at the local PolySaaS server.
Simulates what HubSpot sends when a new contact is created.

URL: POST http://localhost:8000/dose/webhook/hubspot/olient/
"""
import json
import requests

WEBHOOK_URL = "http://localhost:8000/dose/webhook/hubspot/olient/"

# HubSpot v3 flat payload (most common shape)
payload = {
    "properties": {
        "firstname": "July",
        "lastname": "TestContact",
        "email": "july.testcontact.2026@polysaas-test.com",
        "phone": "+61 2 5550 1234",
        "company": "PolySaaS Test Co",
        "jobtitle": "Test Manager",
        "city": "Sydney",
        "country": "Australia",
        "website": "https://polysaas-test.com",
    }
}

print(f"Firing webhook at: {WEBHOOK_URL}")
print(f"Payload:\n{json.dumps(payload, indent=2)}\n")

resp = requests.post(
    WEBHOOK_URL,
    json=payload,
    headers={
        "Content-Type": "application/json",
        "X-HubSpot-Signature": "test-signature",   # not validated in dev
    },
    timeout=60,
)

print(f"HTTP Status: {resp.status_code}")
try:
    result = resp.json()
    print(f"Response:\n{json.dumps(result, indent=2)}")
except Exception:
    print(f"Response text: {resp.text[:500]}")
