"""Replace the Gallery Videos 'Coming Soon' placeholder with three YouTube embeds."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

VIDEOS = [
    ("_80grF-ht_w", "PolySaaS Platform Overview"),
    ("6-xhFRc54sg", "PolySaaS Demo"),
    ("XkjQXOTtLFc", "PolySaaS Walkthrough"),
]

print("=== Fetching Gallery Videos page ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "gallery-videos", "context": "edit", "_fields": "id,content"},
          timeout=30)
pages = r.json()
if not pages:
    print("  ERROR: Gallery Videos page not found")
    sys.exit(1)

page = pages[0]
raw = page['content']['raw']
page_id = page['id']
print(f"  Page ID: {page_id}, length: {len(raw)} chars")

video_cards = ""
for vid_id, title in VIDEOS:
    video_cards += f'''
<div style="background:var(--ps-card-bg,#fff);border-radius:12px;overflow:hidden;box-shadow:0 2px 12px var(--ps-card-shadow,rgba(0,0,0,0.08));margin-bottom:28px;">
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
<iframe src="https://www.youtube.com/embed/{vid_id}" title="{title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
</div>
<div style="padding:16px 20px;">
<h3 style="margin:0;font-size:1.1rem;font-weight:600;color:var(--ps-text,#1F2937)">{title}</h3>
</div>
</div>'''

new_video_section = f'''<!-- wp:html -->
<h2 style="text-align:center;padding:10px 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Video Gallery</h2>
<p style="text-align:center;color:var(--ps-text-muted,#6B7280);font-size:1.05rem;margin:0 0 32px;">Demos, walkthroughs, and presentations from the PolySaaS team.</p>

<div style="max-width:800px;margin:0 auto;padding:0 20px;">
{video_cards}
</div>
<!-- /wp:html -->'''

old_video_section_pattern = (
    r'<!-- wp:html -->\s*'
    r'<h2[^>]*>Video Gallery</h2>.*?'
    r'<!-- /wp:html -->'
)
match = re.search(old_video_section_pattern, raw, re.DOTALL)

if match:
    print(f"\n=== Replacing existing video section ({match.start()}:{match.end()}) ===")
    raw = raw[:match.start()] + new_video_section + raw[match.end():]
else:
    coming_soon_idx = raw.find('Coming Soon')
    if coming_soon_idx > 0:
        block_start = raw.rfind('<!-- wp:html -->', max(0, coming_soon_idx - 500), coming_soon_idx)
        block_end = raw.find('<!-- /wp:html -->', coming_soon_idx)
        if block_start >= 0 and block_end >= 0:
            block_end += len('<!-- /wp:html -->')
            print(f"\n=== Replacing Coming Soon block ({block_start}:{block_end}) ===")
            raw = raw[:block_start] + new_video_section + raw[block_end:]
        else:
            print("  ERROR: Could not find block boundaries around Coming Soon")
            sys.exit(1)
    else:
        print("  ERROR: Could not find video section or Coming Soon placeholder")
        sys.exit(1)

print(f"\n=== Updating page (new length: {len(raw)} chars) ===")
r2 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
    json={"content": raw},
    timeout=30,
)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("\n  SUCCESS! Gallery Videos page updated with 3 YouTube embeds:")
    for vid_id, title in VIDEOS:
        print(f"    - {title}: https://youtu.be/{vid_id}")
else:
    print(f"  ERROR: {r2.text[:500]}")
