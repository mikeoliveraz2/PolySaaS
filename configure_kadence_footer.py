"""Try to configure Kadence footer builder via WordPress options API."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Kadence stores footer settings in theme_mods_kadence option.
# The REST API doesn't expose theme_mods directly, but we can try
# using the settings endpoint or a custom approach.

# Method 1: Try the Kadence-specific settings endpoint
print("=== Trying Kadence endpoints ===")
for endpoint in [
    '/wp-json/kadence-starter-templates/v1/settings',
    '/wp-json/kadence/v1/settings', 
    '/wp-json/kadence/v1/footer',
    '/wp-json/kadence_starter_templates/v1/get',
]:
    r = s.get(f"{AZURE}{endpoint}")
    print(f"  {endpoint}: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, dict):
            footer_keys = [k for k in data.keys() if 'footer' in k.lower()]
            if footer_keys:
                print(f"    Footer keys: {footer_keys}")
                for fk in footer_keys[:10]:
                    print(f"      {fk}: {json.dumps(data[fk])[:100]}")

# Method 2: Try reading theme_mods via a custom REST call
# WordPress has no built-in endpoint for this, but let's check
# if any plugin added one
print("\n=== Checking all available routes ===")
r = s.get(f"{AZURE}/wp-json/")
if r.status_code == 200:
    routes = r.json().get('routes', {})
    for route in sorted(routes.keys()):
        if any(kw in route.lower() for kw in ['option', 'theme', 'mod', 'customiz']):
            print(f"  {route}")

# Method 3: Try wp-admin AJAX 
print("\n=== Trying wp-admin AJAX for customizer settings ===")
# First try getting a nonce via REST
r = s.get(f"{AZURE}/wp-json/wp/v2/users/me")
if r.status_code == 200:
    user = r.json()
    print(f"  Authenticated as: {user.get('name', 'unknown')} (ID: {user.get('id', 'N/A')})")
    print(f"  Capabilities include admin: {'administrator' in str(user.get('roles', []))}")
else:
    print(f"  Auth check failed: {r.status_code}")
