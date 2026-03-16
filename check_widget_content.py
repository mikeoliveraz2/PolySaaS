"""Check current widget content and sidebar assignments."""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check widgets
r = s.get(f"{AZURE}/wp-json/wp/v2/widgets", timeout=30)
print(f"Widgets: {r.status_code}")
if r.status_code == 200:
    widgets = r.json()
    for w in widgets:
        sidebar = w.get('sidebar', 'none')
        wid = w.get('id', 'unknown')
        instance = w.get('instance', {})
        raw = instance.get('raw', {})
        content = raw.get('content', '')
        print(f"\n--- Widget: {wid} | Sidebar: {sidebar} ---")
        print(f"  Content preview: {content[:200]}...")
        print(f"  Content length: {len(content)} chars")

# Check sidebars
print("\n\n=== SIDEBARS ===")
r2 = s.get(f"{AZURE}/wp-json/wp/v2/sidebars", timeout=30)
if r2.status_code == 200:
    sidebars = r2.json()
    for sb in sidebars:
        sid = sb.get('id', 'unknown')
        name = sb.get('name', 'unknown')
        widgets = sb.get('widgets', [])
        if widgets or 'footer' in sid.lower():
            print(f"\n  Sidebar: {sid} ({name})")
            print(f"    Widgets: {widgets}")
