"""
Fix homepage:
1. Logo centering
2. "The Problem We Solve" and "Our Approach" headings bright blue in both modes
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

s = requests.Session()
s.auth = (USER, APP_PASS)

GRID_CSS = """
.wp-block-columns.is-layout-flex { display: flex !important; flex-wrap: wrap !important; flex-direction: row !important; gap: 20px; }
.wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
@media (max-width: 900px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 45% !important; max-width: 48% !important; } }
@media (max-width: 600px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 100% !important; max-width: 100% !important; } }
.wp-block-column p, .wp-block-column h3 { word-wrap: break-word !important; overflow-wrap: break-word !important; white-space: normal !important; }
"""

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# ── 1. Find and inspect the logo area ──
logo_img_match = re.search(r'<figure[^>]*aligncenter[^>]*>.*?<img[^>]*Industrial[^>]*/>', content, re.DOTALL)
if logo_img_match:
    print(f"Logo figure: {logo_img_match.group()[:300]}")
    # Check parent
    fig_start = logo_img_match.start()
    parent_area = content[max(0, fig_start-300):fig_start]
    print(f"\nBefore figure: ...{parent_area[-200:]}")
else:
    print("Logo figure not found by regex, searching by text...")
    idx = content.find('Industrial')
    if idx > 0:
        print(f"  Found at {idx}: {content[max(0,idx-200):idx+200]}")

# ── 2. Find "The Problem We Solve" heading ──
prob_match = re.search(r'<h\d[^>]*>.*?The Problem We Solve.*?</h\d>', content, re.DOTALL)
if prob_match:
    print(f"\nProblem heading: {prob_match.group()}")
else:
    idx = content.find('The Problem We Solve')
    if idx > 0:
        print(f"\nProblem context: {content[max(0,idx-100):idx+150]}")

# ── 3. Find "Our Approach" heading ──
app_match = re.search(r'<h\d[^>]*>.*?Our Approach.*?</h\d>', content, re.DOTALL)
if app_match:
    print(f"\nApproach heading: {app_match.group()}")
else:
    idx = content.find('Our Approach')
    if idx > 0:
        print(f"\nApproach context: {content[max(0,idx-100):idx+150]}")

print("\n=== Applying fixes ===")

# Fix: Make "The Problem We Solve" bright blue
BRIGHT_BLUE = "#2563EB"

# Replace the heading tags to include inline color
# Pattern: find h2 containing "The Problem We Solve" and ensure it has blue color
content = re.sub(
    r'(<h2[^>]*)(>)(.*?The Problem We Solve.*?)(</h2>)',
    lambda m: m.group(1).replace('style="', f'style="color:{BRIGHT_BLUE} !important;') 
              if 'style="' in m.group(1) 
              else m.group(1) + f' style="color:{BRIGHT_BLUE} !important"' + m.group(2) + m.group(3) + m.group(4),
    content,
    flags=re.DOTALL
)

# Same for "Our Approach"
content = re.sub(
    r'(<h2[^>]*)(>)(.*?Our Approach.*?)(</h2>)',
    lambda m: m.group(1).replace('style="', f'style="color:{BRIGHT_BLUE} !important;') 
              if 'style="' in m.group(1) 
              else m.group(1) + f' style="color:{BRIGHT_BLUE} !important"' + m.group(2) + m.group(3) + m.group(4),
    content,
    flags=re.DOTALL
)

# Also add CSS rule to ensure dark mode doesn't override
HEADING_CSS = f"""
h2 {{ color: inherit; }}
.ps-section-title {{ color: {BRIGHT_BLUE} !important; }}
body.dark-mode .ps-section-title {{ color: {BRIGHT_BLUE} !important; }}
"""

# Check if it's an h2 or h3 - also handle h3 variants
for tag in ['h3']:
    content = re.sub(
        rf'(<{tag}[^>]*)(>)(.*?The Problem We Solve.*?)(</{tag}>)',
        lambda m: m.group(1).replace('style="', f'style="color:{BRIGHT_BLUE} !important;') 
                  if 'style="' in m.group(1) 
                  else m.group(1) + f' style="color:{BRIGHT_BLUE} !important"' + m.group(2) + m.group(3) + m.group(4),
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        rf'(<{tag}[^>]*)(>)(.*?Our Approach.*?)(</{tag}>)',
        lambda m: m.group(1).replace('style="', f'style="color:{BRIGHT_BLUE} !important;') 
                  if 'style="' in m.group(1) 
                  else m.group(1) + f' style="color:{BRIGHT_BLUE} !important"' + m.group(2) + m.group(3) + m.group(4),
        content,
        flags=re.DOTALL
    )

# ── Fix logo centering ──
# Add text-align:center to the logo's parent wrapper
content = re.sub(
    r'(<div class="wp-block-image">\s*<figure class="aligncenter)',
    r'<div class="wp-block-image" style="text-align:center"><figure class="aligncenter',
    content
)

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("  Grid CSS re-added")

# Insert heading CSS
if 'ps-section-title' not in content:
    content = content.replace('</style>', HEADING_CSS + '\n</style>', 1)
    print("  Heading CSS added")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"  Homepage update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")

# Verify
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
final = r3.json()['content']['rendered']
prob_check = re.search(r'<h\d[^>]*>.*?The Problem We Solve.*?</h\d>', final, re.DOTALL)
app_check = re.search(r'<h\d[^>]*>.*?Our Approach.*?</h\d>', final, re.DOTALL)
print(f"\n  Problem heading now: {prob_check.group()[:150] if prob_check else 'NOT FOUND'}")
print(f"  Approach heading now: {app_check.group()[:150] if app_check else 'NOT FOUND'}")

logo_check = 'text-align:center' in final and 'aligncenter' in final
print(f"  Logo centered: {logo_check}")

print("\nDone!")
