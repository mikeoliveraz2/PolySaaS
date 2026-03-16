"""Check Kadence theme footer settings and widget areas."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check current theme settings/customizer for footer config
print("=== Kadence Theme Settings ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/settings")
if r.status_code == 200:
    settings = r.json()
    for k, v in settings.items():
        if 'footer' in k.lower() or 'widget' in k.lower():
            print(f"  {k}: {v}")

# Check existing widgets
print("\n=== Widget Areas (Sidebars) ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/sidebars")
if r.status_code == 200:
    sidebars = r.json()
    for sb in sidebars:
        widget_count = len(sb.get('widgets', []))
        print(f"  {sb['id']}: {sb.get('name', 'N/A')} ({widget_count} widgets)")
else:
    print(f"  Error: {r.status_code}")

# Check existing widgets
print("\n=== Current Widgets ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/widgets")
if r.status_code == 200:
    widgets = r.json()
    for w in widgets:
        sidebar = w.get('sidebar', 'none')
        wtype = w.get('id_base', w.get('id', 'unknown'))
        rendered = w.get('rendered', '')[:100] if w.get('rendered') else ''
        print(f"  [{sidebar}] {wtype}: {rendered}")
else:
    print(f"  Error: {r.status_code}")

# Check Kadence footer customizer options
print("\n=== Kadence Customizer (footer-related) ===")
r = s.get(f"{AZURE}/wp-json/kadence/v1/settings")
if r.status_code == 200:
    ksettings = r.json()
    for k, v in ksettings.items():
        if 'footer' in k.lower():
            val_str = json.dumps(v)[:200] if not isinstance(v, str) else v[:200]
            print(f"  {k}: {val_str}")
elif r.status_code == 404:
    print("  Kadence settings API not available, trying theme mods...")
    # Try theme mods
    r2 = s.get(f"{AZURE}/wp-json/wp/v2/themes")
    if r2.status_code == 200:
        themes = r2.json()
        for t in themes:
            if t.get('status') == 'active':
                print(f"  Active theme: {t.get('name', 'unknown')}")
                print(f"  Theme URI: {t.get('theme_uri', 'N/A')}")
else:
    print(f"  Error: {r.status_code}")

# Check if Kadence has footer builder rows
print("\n=== Kadence Footer Builder Rows ===")
for endpoint in ['kadence_footer', 'footer']:
    r = s.get(f"{AZURE}/wp-json/wp/v2/{endpoint}")
    if r.status_code == 200:
        print(f"  {endpoint}: {r.json()}")
    
# Check Kadence customizer via options
print("\n=== Footer-related options ===")
r = s.get(f"{AZURE}/wp-json/")
if r.status_code == 200:
    api_index = r.json()
    namespaces = api_index.get('namespaces', [])
    kadence_ns = [n for n in namespaces if 'kadence' in n.lower()]
    print(f"  Kadence namespaces: {kadence_ns}")
