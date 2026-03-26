"""Check Kadence theme settings to find layout/centering options."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check theme mods
r = s.get(f"{AZURE}/wp-json/wp/v2/settings", timeout=30)
if r.status_code == 200:
    settings = r.json()
    print("=== Site Settings ===")
    for k, v in settings.items():
        if any(term in k.lower() for term in ['layout', 'width', 'content', 'kadence', 'theme']):
            print(f"  {k}: {v}")

# Check customizer settings via theme mods
r2 = s.get(f"{AZURE}/wp-json/", timeout=30)
if r2.status_code == 200:
    api = r2.json()
    namespaces = api.get('namespaces', [])
    kadence_ns = [n for n in namespaces if 'kadence' in n.lower()]
    print(f"\nKadence namespaces: {kadence_ns}")

# Try Kadence-specific API endpoints
for endpoint in [
    '/wp-json/kadence/v1/settings',
    '/wp-json/wp/v2/global-styles',
    '/wp-json/wp/v2/global-styles/themes/flavor',
]:
    r3 = s.get(f"{AZURE}{endpoint}", timeout=15)
    print(f"\n{endpoint}: {r3.status_code}")
    if r3.status_code == 200:
        data = r3.json()
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and len(str(v)) < 200:
                    if any(term in k.lower() for term in ['layout', 'width', 'content', 'align', 'center', 'max']):
                        print(f"  {k}: {v}")

# Check the home page meta for layout settings
r4 = s.get(f"{AZURE}/wp-json/wp/v2/pages",
           params={"slug": "home", "context": "edit", "_fields": "id,meta,template"},
           timeout=30)
if r4.status_code == 200:
    page = r4.json()[0]
    print(f"\n=== Home page meta ===")
    print(f"  Template: {page.get('template', 'none')}")
    meta = page.get('meta', {})
    for k, v in meta.items():
        if v and str(v) != '' and str(v) != '0':
            print(f"  {k}: {v}")
