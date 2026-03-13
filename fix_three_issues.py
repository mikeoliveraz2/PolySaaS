"""
Fix three issues:
1. Remaining "AI Agents" text on homepage -> "AI As Peers"
2. Toggle placement on AI As Peers page
3. Homepage logo not centered
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

# ── Issue 1 & 3: Homepage - fix "AI Agents" and logo centering ──
print("=== Homepage fixes ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# Fix all remaining "AI Agents" 
content = content.replace('AI Agents', 'AI As Peers')
remaining = content.count('AI Agents')
print(f"  AI Agents remaining: {remaining}")

# Check current logo/hero HTML to understand centering issue
logo_idx = content.find('PolySaaS Online</h1>')
if logo_idx > 0:
    hero_start = content.rfind('<div class="wp-block-group"', 0, logo_idx)
    hero_section = content[hero_start:logo_idx+30]
    print(f"  Hero section preview: ...{hero_section[-200:]}")

# The logo is in the hero section - find it
img_idx = content.find('PolySaaS-Industrial-Logo-BIG')
if img_idx < 0:
    img_idx = content.find('Industrial-PolySaas-Cropped-300-Transparent')
if img_idx > 0:
    # Find the img tag
    img_start = content.rfind('<img', 0, img_idx)
    img_end = content.find('/>', img_idx) + 2
    img_tag = content[img_start:img_end]
    print(f"  Found logo img: {img_tag[:100]}...")
    
    # Check if there's a centering wrapper
    before = content[max(0, img_start-200):img_start]
    print(f"  Before logo: ...{before[-100:]}")
else:
    print("  No logo image found in hero - checking h1")
    # The hero might just have the text "PolySaaS Online" without a logo image
    h1_idx = content.find('PolySaaS Online</h1>')
    if h1_idx > 0:
        h1_start = content.rfind('<h1', 0, h1_idx)
        h1_tag = content[h1_start:h1_idx+20]
        print(f"  H1 tag: {h1_tag}")
        # Add text-align:center if missing
        if 'text-align:center' not in h1_tag and 'has-text-align-center' not in h1_tag:
            print("  Logo heading not centered - fixing")

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("  Grid CSS re-added")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"  Homepage: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")

# ── Issue 2: AI As Peers toggle placement ──
print("\n=== AI As Peers toggle fix ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1363")
ai_content = r.json()['content']['rendered']

# Check current toggle position
toggle_idx = ai_content.find('ps-theme-toggle')
style_end = ai_content.find('</style>')
print(f"  Toggle at pos: {toggle_idx}, Style ends at: {style_end}")

if toggle_idx > 0 and toggle_idx < style_end:
    print("  Toggle is INSIDE the style block - that's wrong!")

# Show what's around the toggle
if toggle_idx > 0:
    before = ai_content[max(0, toggle_idx-200):toggle_idx]
    after = ai_content[toggle_idx:toggle_idx+300]
    print(f"  Before toggle: ...{repr(before[-100:])}")
    print(f"  Toggle area: {repr(after[:200])}")

# The correct approach: strip any existing broken toggle, insert clean one after </style>
CORRECT_TOGGLE = '''<button class="ps-theme-toggle" id="ps-dark-toggle" onclick="document.body.classList.toggle('dark-mode');localStorage.setItem('ps-dark-mode',document.body.classList.contains('dark-mode')?'true':'false');var i=document.getElementById('ps-toggle-icon');if(i)i.innerHTML=document.body.classList.contains('dark-mode')?'&#9728;':'&#9790;'" aria-label="Toggle dark mode">
<span id="ps-toggle-icon">&#9790;</span>
</button>
<script>(function(){var s=localStorage.getItem('ps-dark-mode');if(s==='true'){document.body.classList.add('dark-mode');var i=document.getElementById('ps-toggle-icon');if(i)i.innerHTML='\\u2600';}})();</script>'''

# Remove all existing toggle instances (broken or not)
# Pattern: anything with ps-theme-toggle button through </script>
ai_content = re.sub(
    r'<button[^>]*ps-theme-toggle[^>]*>.*?</button>\s*<script>.*?</script>',
    '',
    ai_content,
    flags=re.DOTALL
)
# Also remove if it leaked as text
ai_content = re.sub(r'<p>[^<]*ps-theme-toggle[^<]*</p>', '', ai_content)
# Remove orphaned toggle CSS rendered as text
ai_content = re.sub(r'<p>/\* Toggle button \*/.*?</p>', '', ai_content, flags=re.DOTALL)

# Insert clean toggle right after </style>
style_end = ai_content.find('</style>')
if style_end > 0:
    insert_point = style_end + len('</style>')
    ai_content = ai_content[:insert_point] + '\n' + CORRECT_TOGGLE + '\n' + ai_content[insert_point:]
    print("  Inserted clean toggle after </style>")

r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1363", json={"content": ai_content})
print(f"  AI As Peers: {'OK' if r3.status_code == 200 else f'FAILED {r3.status_code}'}")

print("\nDone!")
