"""Configure WP Mail SMTP with Google Workspace SMTP credentials."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# WP Mail SMTP stores settings in wp_options under 'wp_mail_smtp'
# We need to use the options API or the plugin's own API

# Try the WP Mail SMTP settings endpoint
r = s.get(f"{AZURE}/wp-json/", timeout=15)
api = r.json()
namespaces = api.get('namespaces', [])
smtp_ns = [n for n in namespaces if 'smtp' in n.lower() or 'mail' in n.lower()]
print(f"SMTP namespaces: {smtp_ns}")

# Check available routes
routes = api.get('routes', {})
smtp_routes = {k: v for k, v in routes.items() if 'smtp' in k.lower() or 'mail-smtp' in k.lower()}
print(f"SMTP routes: {list(smtp_routes.keys())}")

# WP Mail SMTP typically uses wp_mail_smtp option
# Let's try to update via the settings API or direct option update
# First, let's check if there's a way via the plugin's admin ajax

# The most reliable way is to use WordPress options API
# WP Mail SMTP stores config in 'wp_mail_smtp' option as serialized array
# We can try updating it via a custom approach

# Let's try the plugin's own settings page via POST
# First check current SMTP settings
for route in smtp_routes:
    r2 = s.get(f"{AZURE}{route}", timeout=15)
    print(f"\n{route}: {r2.status_code}")
    if r2.status_code == 200:
        print(f"  {json.dumps(r2.json(), indent=2)[:500]}")

# Try wp-mail-smtp settings endpoints
for ep in [
    '/wp-json/wp-mail-smtp/v1/settings',
    '/wp-json/wp-mail-smtp/v1/options',
]:
    r3 = s.get(f"{AZURE}{ep}", timeout=15)
    print(f"\n{ep}: {r3.status_code}")
    if r3.status_code == 200:
        print(f"  {json.dumps(r3.json(), indent=2)[:1000]}")
