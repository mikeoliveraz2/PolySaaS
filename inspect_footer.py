import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# Search for footer indicators
for marker in ['footer', 'Footer', '© 2026', 'copyright', 'Applications</h4>', 'Features</h4>', 'Gallery</h4>']:
    idx = content.find(marker)
    if idx >= 0:
        print(f"'{marker}' at pos {idx}:")
        # Go back to find the parent container
        area = content[max(0, idx-300):idx+100]
        print(f"  ...{area[-200:]}\n")

# Show last 2000 chars of the page
print("=== LAST 2000 chars ===")
print(content[-2000:])
