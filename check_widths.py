"""Check actual content widths and theme styles to debug centering issue."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "XF8j E5IE VpHD N3rx WSkO TaMc")

# 1. Get global styles for the theme
r = requests.get(f"{BASE}/wp-json/wp/v2/themes", auth=AUTH, timeout=15)
if r.status_code == 200:
    themes = r.json()
    for t in themes:
        if t.get('status') == 'active':
            print(f"Active theme: {t.get('stylesheet')}")
            print(f"Theme name: {t.get('name', {}).get('rendered', 'N/A')}")
            
            # Get global styles for this theme
            stylesheet = t.get('stylesheet')
            r2 = requests.get(
                f"{BASE}/wp-json/wp/v2/global-styles/themes/{stylesheet}",
                auth=AUTH, timeout=15
            )
            print(f"\nGlobal styles status: {r2.status_code}")
            if r2.status_code == 200:
                gs = r2.json()
                settings = gs.get('settings', {})
                layout = settings.get('layout', {})
                print(f"Layout settings: {layout}")
                styles = gs.get('styles', {})
                print(f"Style spacing: {styles.get('spacing', {})}")
                print(f"Style layout: {styles.get('layout', {})}")
                # Check for any width-related settings
                for key in ['contentSize', 'wideSize', 'layout']:
                    if key in settings:
                        print(f"  {key}: {settings[key]}")

# 2. Get the rendered page and extract ALL style tags
print("\n\n--- Checking rendered page CSS ---")
r = requests.get(BASE, timeout=30)
html = r.text

# Find all stylesheets linked
css_links = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', html)
print(f"\nFound {len(css_links)} CSS stylesheets")

# Find inline styles related to content width
for pattern in ['global-content-width', 'content-width', 'contentSize', 'wideSize', 'entry-content']:
    matches = re.findall(f'[^\\n]{{0,100}}{pattern}[^\\n]{{0,100}}', html)
    if matches:
        print(f"\n--- Matches for '{pattern}' ---")
        for m in matches[:5]:
            print(f"  {m.strip()[:200]}")

# 3. Check the entry-content-wrap computed layout
# Find the site-main and entry-content-wrap structure
entry_pos = html.find('entry-content-wrap')
if entry_pos > 0:
    snippet = html[max(0, entry_pos-300):entry_pos+200]
    print(f"\n--- entry-content-wrap context ---")
    print(snippet[:500])

# 4. Check what Kadence sets for page layout
pf_pos = html.find('platform-features')
if pf_pos > 0:
    # Check for any parent containers with width styles
    start = max(0, pf_pos - 2000)
    chunk = html[start:pf_pos]
    # Find all div openings near the features heading
    divs = re.findall(r'<div[^>]*class="[^"]*(?:entry|content|site-main|inner-wrap)[^"]*"[^>]*>', chunk)
    print(f"\n--- Container divs near features ---")
    for d in divs:
        print(f"  {d[:200]}")
