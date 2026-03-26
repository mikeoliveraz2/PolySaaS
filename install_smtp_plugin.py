"""Install and activate WP Mail SMTP plugin."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Install WP Mail SMTP from wordpress.org
print("Installing WP Mail SMTP...")
r = s.post(
    f"{AZURE}/wp-json/wp/v2/plugins",
    json={"slug": "wp-mail-smtp", "status": "active"},
    timeout=120
)
print(f"Status: {r.status_code}")
if r.status_code in [200, 201]:
    plugin = r.json()
    print(f"Plugin: {plugin.get('name', 'N/A')}")
    print(f"Status: {plugin.get('status', 'N/A')}")
    print(f"Version: {plugin.get('version', 'N/A')}")
    print("SUCCESS: WP Mail SMTP installed and activated!")
else:
    print(f"Response: {r.text[:500]}")
    # Maybe it's already installed but inactive
    if 'already' in r.text.lower() or 'exists' in r.text.lower():
        print("\nPlugin may already be installed. Trying to activate...")
        r2 = s.post(
            f"{AZURE}/wp-json/wp/v2/plugins/wp-mail-smtp/wp_mail_smtp",
            json={"status": "active"},
            timeout=60
        )
        print(f"Activation: {r2.status_code}")
        if r2.status_code == 200:
            print("Activated successfully!")
        else:
            print(f"Activation response: {r2.text[:300]}")

# Verify
print("\n=== Verifying installed plugins ===")
r3 = s.get(f"{AZURE}/wp-json/wp/v2/plugins", timeout=30)
if r3.status_code == 200:
    for p in r3.json():
        name = p.get('name', 'N/A')
        status = p.get('status', 'N/A')
        print(f"  [{status}] {name}")
