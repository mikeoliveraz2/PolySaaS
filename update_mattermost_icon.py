"""
Upload Mattermost icon and update it on:
1. Homepage bundled apps grid
2. Mattermost detail page
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Upload the icon
icon_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_MatterMost_Icon-739fcb70-4db5-4ad7-a974-ab3c048951d1.png"
with open(icon_path, 'rb') as f:
    data = f.read()
r = s.post(f"{AZURE}/wp-json/wp/v2/media",
    headers={"Content-Disposition": 'attachment; filename="mattermost-icon.png"', "Content-Type": "image/png"},
    data=data)
if r.status_code == 201:
    new_url = r.json()['source_url']
    print(f"Uploaded: {new_url}")
else:
    print(f"Upload failed: {r.status_code} - {r.text[:200]}")
    sys.exit(1)

# Get all pages
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

# 1. Update homepage
home = [p for p in pages if p['slug'] == 'home'][0]
raw = home['content']['raw']

# Find existing Mattermost image references
mm_imgs = list(re.finditer(r'<img[^>]*(?:mattermost|Mattermost)[^>]*>', raw, re.IGNORECASE))
print(f"\nHomepage: found {len(mm_imgs)} Mattermost img tags")
for m in mm_imgs:
    print(f"  {m.group()[:150]}")

# Replace the src in any Mattermost-related img tags on homepage
# Also check for the app grid icon which might reference a different image
old_mm_patterns = re.findall(r'src="([^"]*)"[^>]*alt="[^"]*[Mm]attermost[^"]*"', raw)
if not old_mm_patterns:
    old_mm_patterns = re.findall(r'alt="[^"]*[Mm]attermost[^"]*"[^>]*src="([^"]*)"', raw)
    
# Also check for img tags near "Mattermost" text
mm_text_idx = raw.find('>Mattermost<')
if mm_text_idx > 0:
    nearby = raw[max(0,mm_text_idx-500):mm_text_idx]
    nearby_img = re.findall(r'src="([^"]*)"', nearby)
    if nearby_img:
        old_mm_patterns.extend(nearby_img[-1:])

print(f"Found Mattermost image URLs: {old_mm_patterns}")

changes = 0
for old_url in set(old_mm_patterns):
    if old_url and 'mattermost' not in old_url.lower():
        # This might be a generic placeholder - check context
        pass
    if old_url:
        count = raw.count(old_url)
        raw = raw.replace(old_url, new_url)
        print(f"  Replaced '{old_url}' ({count} occurrences)")
        changes += count

if changes > 0:
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{home['id']}", json={"content": raw})
    print(f"Homepage update: {r.status_code}")
else:
    print("No Mattermost images found on homepage to replace - searching broader")
    # Search for any img near Mattermost in the bundled apps grid
    mm_idx = raw.find('Mattermost')
    while mm_idx >= 0:
        area = raw[max(0,mm_idx-400):mm_idx+100]
        imgs = re.findall(r'src="([^"]*)"', area)
        print(f"  Near Mattermost at {mm_idx}: imgs={imgs}")
        mm_idx = raw.find('Mattermost', mm_idx+1)

# 2. Update Mattermost detail page
mm_page = [p for p in pages if p['slug'] == 'mattermost'][0]
mm_raw = mm_page['content']['raw']

# Find image tags on the detail page
mm_page_imgs = re.findall(r'src="([^"]*)"', mm_raw)
print(f"\nMattermost page images: {mm_page_imgs[:5]}")

# Replace any existing Mattermost logo/icon
mm_replaced = False
for old_url in mm_page_imgs:
    if 'mattermost' in old_url.lower() or 'logo' in old_url.lower():
        mm_raw = mm_raw.replace(old_url, new_url)
        print(f"  Replaced on detail page: {old_url}")
        mm_replaced = True

if not mm_replaced:
    # Check if there's an icon/logo area at the top of the page
    print("  No existing Mattermost image found on detail page - checking structure")
    first_500 = mm_raw[:2000]
    # Look for any image that could be the app icon
    for old_url in mm_page_imgs[:3]:
        if 'logo' in old_url.lower() or 'icon' in old_url.lower():
            mm_raw = mm_raw.replace(old_url, new_url)
            print(f"  Replaced generic icon: {old_url}")
            mm_replaced = True
            break

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{mm_page['id']}", json={"content": mm_raw})
print(f"Mattermost page update: {r2.status_code}")
