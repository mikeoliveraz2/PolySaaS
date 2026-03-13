"""
Update the 8 bundled app blurbs on the homepage with Shela's revised one-liners.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

GRID_CSS = """
.wp-block-columns.is-layout-flex { display: flex !important; flex-wrap: wrap !important; flex-direction: row !important; gap: 20px; }
.wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
@media (max-width: 900px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 45% !important; max-width: 48% !important; } }
@media (max-width: 600px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 100% !important; max-width: 100% !important; } }
.wp-block-column p, .wp-block-column h3 { word-wrap: break-word !important; overflow-wrap: break-word !important; white-space: normal !important; }
"""

BLURBS = {
    "Odoo": "Comprehensive ERP &amp; CRM for streamlined operations, sales, and project management at enterprise scale.",
    "Nextcloud": "Secure file storage and collaboration tools with full control over sharing and data privacy.",
    "Mattermost": "Real-time team messaging enhanced with AI peers for secure, productive workflows.",
    "WordPress": "Flexible content management for blogs, websites, and dynamic publishing integrated effortlessly.",
    "Liferay": "Robust enterprise portal delivering personalized content and seamless user experiences.",
    "Dolibarr": "Modular ERP and invoicing system for efficient inventory and customer relationship handling.",
    "Monitor Logger": "Advanced logging and monitoring to detect issues and gain actionable system insights.",
    "PolySysMon": "Continuous performance and health tracking ensuring reliability across your entire stack.",
}

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# For each app, find its h3 heading, then the <p> immediately after, and replace the text
for app_name, new_blurb in BLURBS.items():
    idx = content.find(f'>{app_name}</h3>')
    if idx < 0:
        print(f"  WARNING: '{app_name}' heading not found")
        continue
    
    # Find the next <p> after the h3
    h3_end = content.find('</h3>', idx) + 5
    next_p_start = content.find('<p', h3_end)
    
    # Make sure this <p> is close to the h3 (within 200 chars) and not in next section
    if next_p_start < 0 or next_p_start - h3_end > 200:
        print(f"  WARNING: No paragraph found near '{app_name}' heading")
        continue
    
    p_tag_end = content.find('>', next_p_start) + 1
    p_close = content.find('</p>', p_tag_end)
    
    old_text = content[p_tag_end:p_close]
    p_tag = content[next_p_start:p_tag_end]
    
    old_full = content[next_p_start:p_close+4]
    new_full = f'{p_tag}{new_blurb}</p>'
    
    content = content.replace(old_full, new_full, 1)
    print(f"  {app_name}: \"{old_text[:60]}...\" -> \"{new_blurb[:60]}...\"")

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("  Grid CSS re-added")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"\nHomepage update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")
print("Done!")
