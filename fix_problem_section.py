"""
Fix the section after "The Problem We Solve":
- "Our Approach" should be a bright blue heading
- Paragraph below should be the new text
- "The Problem We Solve" should also be bright blue
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

# Find the area between "The Problem We Solve" and "Who Benefits Most"
prob_idx = content.find('The Problem We Solve')
who_idx = content.find('Who Benefits Most')

if prob_idx < 0 or who_idx < 0:
    print(f"ERROR: Problem={prob_idx}, Who={who_idx}")
    sys.exit(1)

section = content[prob_idx:who_idx]
print(f"Section between Problem and Who ({len(section)} chars):\n")
print(section[:2000])
print("\n... (truncated)" if len(section) > 2000 else "")

# Find the h1 for "The Problem We Solve" and the h2 + paragraph after it
# The h1 closes, then there's a paragraph, then h2 "One Interface..." which should become "Our Approach"
# Then another paragraph with the old text

# Let me find the exact h2 and paragraph
h2_match = re.search(r'<h2[^>]*>One Interface[^<]*</h2>', section)
para_match = re.search(r'<p[^>]*>Most Software.*?</p>', section, re.DOTALL)

if h2_match:
    print(f"\nFound h2: {h2_match.group()[:150]}")
if para_match:
    print(f"\nFound paragraph: {para_match.group()[:200]}")

# Now do the replacements

# 1. Make "The Problem We Solve" bright blue (ensure it stays)
prob_h1_start = content.rfind('<h1', 0, prob_idx)
prob_h1_end = content.find('</h1>', prob_idx) + 5
old_prob_h1 = content[prob_h1_start:prob_h1_end]
if f'color:{BRIGHT_BLUE}' not in old_prob_h1:
    if 'style="' in old_prob_h1:
        new_prob_h1 = old_prob_h1.replace('style="', f'style="color:{BRIGHT_BLUE} !important;')
    else:
        new_prob_h1 = old_prob_h1.replace('>', f' style="color:{BRIGHT_BLUE} !important">', 1)
    content = content.replace(old_prob_h1, new_prob_h1)
    print("\nApplied blue to 'The Problem We Solve'")
else:
    print("\n'The Problem We Solve' already blue")

# 2. Replace the h2 "One Interface..." with "Our Approach" in bright blue
# AND replace the paragraph text
if h2_match:
    old_h2 = h2_match.group()
    new_h2 = f'<h2 class="wp-block-heading has-text-align-center" style="margin-top:20px;margin-bottom:16px;font-size:1.8rem;font-weight:600;color:{BRIGHT_BLUE} !important">Our Approach</h2>'
    content = content.replace(old_h2, new_h2)
    print("Replaced h2 -> 'Our Approach' in bright blue")

NEW_PARA_TEXT = (
    "One interface, with all your SaaS fully customizable \u2014 no code changes to the SaaS applications "
    "you are accessing. Stop wrestling with silos, manual syncs, and rigid tools. PolySaaS unifies your "
    "SaaS stack, automates data flow between apps, and lets you customize everything dynamically."
)

if para_match:
    old_para = para_match.group()
    new_para = f'<p class="has-text-align-center has-contrast-color has-text-color" style="margin-bottom:30px;font-size:1.1rem;line-height:1.8">{NEW_PARA_TEXT}</p>'
    content = content.replace(old_para, new_para)
    print("Replaced paragraph text")
else:
    # Maybe the paragraph is different - search broader
    # Find any <p> between the h2 and "Who Benefits"
    prob_idx2 = content.find('Our Approach')
    if prob_idx2 < 0:
        prob_idx2 = content.find('The Problem We Solve')
    who_idx2 = content.find('Who Benefits Most')
    section2 = content[prob_idx2:who_idx2]
    para_all = re.findall(r'<p[^>]*>.*?</p>', section2, re.DOTALL)
    print(f"\nParagraphs in section: {len(para_all)}")
    for i, p in enumerate(para_all):
        print(f"  P{i}: {p[:120]}...")

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("Grid CSS re-added")

# Save
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"\nHomepage update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")

# Final verify
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
final = r3.json()['content']['rendered']
for label in ['The Problem We Solve', 'Our Approach']:
    idx = final.find(label)
    if idx > 0:
        ts = final.rfind('<h', 0, idx)
        te = final.find('>', final.find('</h', idx)) + 1
        print(f"  '{label}': {final[ts:te][:130]}")
    else:
        print(f"  '{label}': NOT FOUND")

# Check new paragraph
new_text_idx = final.find('One interface, with all your SaaS')
print(f"  New paragraph present: {new_text_idx > 0}")

print("\nDone!")
