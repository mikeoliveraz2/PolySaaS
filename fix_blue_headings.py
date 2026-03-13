"""
Make "The Problem We Solve" and "Our Approach" bright blue in both light and dark modes.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

s = requests.Session()
s.auth = (USER, APP_PASS)

BRIGHT_BLUE = "#2563EB"

GRID_CSS = """
.wp-block-columns.is-layout-flex { display: flex !important; flex-wrap: wrap !important; flex-direction: row !important; gap: 20px; }
.wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
@media (max-width: 900px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 45% !important; max-width: 48% !important; } }
@media (max-width: 600px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 100% !important; max-width: 100% !important; } }
.wp-block-column p, .wp-block-column h3 { word-wrap: break-word !important; overflow-wrap: break-word !important; white-space: normal !important; }
"""

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# ── Fix headings with simple string replacement ──

# "The Problem We Solve" is in an h1 with style attribute
OLD_PROBLEM = 'style="margin-top:30px;margin-bottom:16px;font-size:2.2rem;font-weight:700">The Problem We Solve</h1>'
NEW_PROBLEM = f'style="margin-top:30px;margin-bottom:16px;font-size:2.2rem;font-weight:700;color:{BRIGHT_BLUE} !important">The Problem We Solve</h1>'

if OLD_PROBLEM in content:
    content = content.replace(OLD_PROBLEM, NEW_PROBLEM)
    print(f"  Fixed 'The Problem We Solve' -> bright blue")
elif f'color:{BRIGHT_BLUE}' in content and 'The Problem We Solve' in content:
    print(f"  'The Problem We Solve' already has blue color")
else:
    # Broader search
    idx = content.find('The Problem We Solve')
    if idx > 0:
        snippet = content[max(0,idx-200):idx+50]
        print(f"  Problem heading context: ...{snippet[-150:]}")

# "Our Approach" is in an h2
OLD_APPROACH = 'style="margin-top:20px;margin-bottom:16px;font-size:1.8rem;font-weight:600">Our Approach</h2>'
NEW_APPROACH = f'style="margin-top:20px;margin-bottom:16px;font-size:1.8rem;font-weight:600;color:{BRIGHT_BLUE} !important">Our Approach</h2>'

if OLD_APPROACH in content:
    content = content.replace(OLD_APPROACH, NEW_APPROACH)
    print(f"  Fixed 'Our Approach' -> bright blue")
elif f'color:{BRIGHT_BLUE}' in content and 'Our Approach' in content:
    print(f"  'Our Approach' already has blue color")
else:
    idx = content.find('Our Approach')
    if idx > 0:
        snippet = content[max(0,idx-200):idx+50]
        print(f"  Approach heading context: ...{snippet[-150:]}")

# Also add CSS to override dark mode for these specific headings
BLUE_CSS = f"""
h1:has(~ *), h2:has(~ *) {{ }}
body.dark-mode h1.has-primary-color,
body.dark-mode h2.has-primary-color {{
    color: {BRIGHT_BLUE} !important;
}}
"""

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("  Grid CSS re-added")

# Save
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"  Homepage update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")

# Verify
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
final = r3.json()['content']['rendered']

# Check
for label in ['The Problem We Solve', 'Our Approach']:
    idx = final.find(label)
    if idx > 0:
        tag_start = final.rfind('<h', 0, idx)
        tag_end = final.find('>', idx) + 1
        tag = final[tag_start:tag_end]
        has_blue = BRIGHT_BLUE in tag
        print(f"  '{label}': blue={has_blue} | {tag[:120]}")

print("\nDone!")
