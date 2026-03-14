"""
Combined About Us fixes:
1. Upload Scott Chate's headshot
2. Check timeline structure and update to corrected Q1-Q4 sequence
"""
import requests, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Upload Scott's headshot
scott_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_ScottHeadshot-e2eaf9f7-d82e-4379-9f37-dddf5b522b31.png"
with open(scott_path, 'rb') as f:
    data = f.read()
r = s.post(f"{AZURE}/wp-json/wp/v2/media",
    headers={"Content-Disposition": 'attachment; filename="scott-chate-headshot.png"', "Content-Type": "image/png"},
    data=data)
if r.status_code == 201:
    scott_url = r.json()['source_url']
    scott_id = r.json()['id']
    print(f"Uploaded Scott headshot: id={scott_id} url={scott_url}")
else:
    scott_url = None
    print(f"Scott upload: {r.status_code} - {r.text[:200]}")

# Get About Us page
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,slug,content"
}).json()
about = pages[0]
raw = about['content']['raw']
print(f"\nAbout Us: {len(raw)} chars")

# Find timeline-related keywords
for kw in ['Timeline', 'Futures', 'Q1 2025', 'Q1 2026', 'Foundation', 'Roadmap', 'roadmap']:
    idx = raw.find(kw)
    if idx >= 0:
        snippet = raw[max(0,idx-40):idx+80].replace('\n',' ')
        print(f"  Found '{kw}' at {idx}: ...{snippet}...")

# Find all wp:html blocks
blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
print(f"\n{len(blocks)} wp:html blocks")
for i, b in enumerate(blocks):
    has_tl = 'imeline' in b or 'Q1' in b or 'oadmap' in b
    print(f"  Block {i}: {len(b)} chars, timeline-related: {has_tl}")

# The old timeline was in a wp:html block with "Futures Timeline"
# If not found there, check if the timeline HTML is loose (not in wp:html)
timeline_start = raw.find('Futures Timeline')
if timeline_start < 0:
    timeline_start = raw.find('futures-timeline')
if timeline_start < 0:
    timeline_start = raw.find('Platform Foundation')

print(f"\nTimeline content start: {timeline_start}")
if timeline_start > 0:
    print(f"  Around it: {raw[timeline_start:timeline_start+200]}")

# Find the roadmap image block
roadmap_img_start = raw.find('polysaas-roadmap-timeline')
print(f"Roadmap image at: {roadmap_img_start}")

# Strategy: find the timeline section boundaries
# The timeline was inserted by replace_features_with_timeline.py
# Look for the div containing the vertical timeline
vertical_line_idx = raw.find('linear-gradient(to bottom, #2B6CB0')
if vertical_line_idx < 0:
    vertical_line_idx = raw.find('linear-gradient(to bottom,')
print(f"Vertical gradient line at: {vertical_line_idx}")

# Let's find the wp:html block that contains the bulk of the about us content
# and locate the timeline within it
main_block_idx = None
for i, b in enumerate(blocks):
    if len(b) > 1500:
        print(f"\n  Large block {i} first 300 chars:")
        print(f"  {b[:300]}")
        if 'About' in b or 'team' in b.lower() or 'advisor' in b.lower():
            main_block_idx = i

print(f"\nMain content block index: {main_block_idx}")

# Check if timeline content exists outside wp:html blocks
# by looking at content between blocks
all_blocks_text = ''.join(blocks)
outside = raw
for b in blocks:
    outside = outside.replace(b, '|||BLOCK|||')
outside_parts = [p.strip() for p in outside.split('|||BLOCK|||') if p.strip()]
print(f"\nContent outside wp:html blocks: {len(outside_parts)} parts")
for i, part in enumerate(outside_parts):
    if len(part) > 50:
        has_tl = 'imeline' in part or 'Q1' in part
        print(f"  Part {i}: {len(part)} chars, timeline: {has_tl}")
        print(f"    Start: {part[:150]}")
