"""Install a server-side page view counter plugin."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Try installing "Post Views Counter" plugin
r = requests.post(f"{BASE}/wp-json/wp/v2/plugins",
                  auth=AUTH,
                  json={"slug": "post-views-counter", "status": "active"},
                  timeout=60)
print(f"Install Post Views Counter: {r.status_code}")
if r.status_code == 201:
    print("SUCCESS - Plugin installed and activated")
    plugin = r.json()
    print(f"  Name: {plugin.get('name')}")
    print(f"  Version: {plugin.get('version')}")
elif r.status_code == 200:
    print("Plugin already installed")
else:
    print(f"  Response: {r.text[:300]}")
    
    # Try alternative plugin
    print("\nTrying 'page-views-count' instead...")
    r2 = requests.post(f"{BASE}/wp-json/wp/v2/plugins",
                       auth=AUTH,
                       json={"slug": "page-views-count", "status": "active"},
                       timeout=60)
    print(f"Install Page Views Count: {r2.status_code}")
    if r2.status_code == 201:
        print("SUCCESS")
    else:
        print(f"  Response: {r2.text[:300]}")
