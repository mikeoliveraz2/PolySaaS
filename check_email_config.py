"""Check WordPress email configuration and WPForms entries."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# 1. Check admin email
r = s.get(f"{AZURE}/wp-json/wp/v2/settings",
          params={"_fields": "email,admin_email"},
          timeout=30)
if r.status_code == 200:
    settings = r.json()
    print(f"Admin email: {settings.get('email', 'not found')}")
else:
    print(f"Settings error: {r.status_code}")

# 2. Check all settings for email-related keys
r2 = s.get(f"{AZURE}/wp-json/wp/v2/settings", timeout=30)
if r2.status_code == 200:
    for k, v in r2.json().items():
        if 'email' in k.lower() or 'mail' in k.lower() or 'smtp' in k.lower():
            print(f"  {k}: {v}")

# 3. Check installed plugins for SMTP/email plugins
r3 = s.get(f"{AZURE}/wp-json/wp/v2/plugins",
           params={"per_page": 100},
           timeout=30)
if r3.status_code == 200:
    plugins = r3.json()
    print(f"\n=== Installed Plugins ({len(plugins)}) ===")
    for p in plugins:
        name = p.get('name', 'N/A')
        status = p.get('status', 'N/A')
        slug = p.get('plugin', 'N/A')
        # Show all plugins, highlight email/smtp related
        marker = " *** EMAIL/SMTP ***" if any(t in name.lower() for t in ['mail', 'smtp', 'email', 'post']) else ""
        print(f"  [{status}] {name} ({slug}){marker}")
else:
    print(f"\nPlugins error: {r3.status_code}")

# 4. Check if the test submission was actually recorded in WPForms
r4 = s.get(f"{AZURE}/wp-json/wpforms/v1/forms/1543/entries",
           timeout=30)
print(f"\n=== WPForms Entries ===")
print(f"  Entries endpoint: {r4.status_code}")
if r4.status_code == 200:
    entries = r4.json()
    print(f"  Total entries: {len(entries)}")
    for entry in entries[-5:]:
        print(f"  Entry: {json.dumps(entry, indent=2)[:500]}")

# Also try the general entries endpoint
r5 = s.get(f"{AZURE}/wp-json/wpforms/v1/entries",
           params={"form_id": 1543},
           timeout=30)
print(f"  General entries: {r5.status_code}")
if r5.status_code == 200 and r5.json():
    for entry in r5.json()[-3:]:
        print(f"  {json.dumps(entry, indent=2)[:300]}")
