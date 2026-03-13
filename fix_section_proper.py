"""
Fix the Problem/Approach section properly:
- h1 "The Problem We Solve" (bright blue)
- Paragraph: original problem description  
- h2 "Our Approach" (bright blue)
- Paragraph: new user-provided text
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

PROBLEM_TEXT = (
    "Most Software as a Service applications are difficult to customize, if at all. "
    "Even when they are customizable, it is limited to a small set of APIs or Software Development Kits. "
    "This is usually very expensive and difficult to maintain. PolySaaS solves this by providing a unified "
    "platform that orchestrates multiple SaaS applications with dynamic customization \u2014 no code changes required."
)

APPROACH_TEXT = (
    "One interface, with all your SaaS fully customizable \u2014 no code changes to the SaaS applications "
    "you are accessing. Stop wrestling with silos, manual syncs, and rigid tools. PolySaaS unifies your "
    "SaaS stack, automates data flow between apps, and lets you customize everything dynamically."
)

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# Find the section: from "The Problem We Solve" to "Who Benefits Most"
prob_idx = content.find('The Problem We Solve')
who_idx = content.find('Who Benefits Most')

section = content[prob_idx:who_idx]
print(f"Current section ({len(section)} chars):")
print(repr(section[:500]))
print("...")
print(repr(section[500:1200]))

# The section currently has:
# 1) ...The Problem We Solve</h1>
# 2) <p ...>One interface, with all your SaaS...</p>  (wrongly replaced)
# 3) <h2 ...> (empty text) </h2>  
# 4) <p ...>One Interface. All Your SaaS. Fully Customizable...</p>

# Strategy: Replace the entire block from </h1> through to the second </p> (before Who Benefits)
# with the correct structure

h1_end = section.find('</h1>') + 5
# Find where the "Who Benefits" section begins - go back from who_idx to find the parent div
# Actually, let's find the content between the h1 close and the Who Benefits section

after_h1 = section[h1_end:]
print(f"\n\nAfter h1:\n{repr(after_h1[:800])}")

# Build the replacement block
NEW_BLOCK = f'''{section[:h1_end]}
<p class="has-text-align-center has-contrast-color has-text-color" style="margin-bottom:30px;font-size:1.1rem;line-height:1.8">{PROBLEM_TEXT}</p>
<h2 class="wp-block-heading has-text-align-center" style="margin-top:20px;margin-bottom:16px;font-size:1.8rem;font-weight:600;color:{BRIGHT_BLUE} !important">Our Approach</h2>
<p class="has-text-align-center has-contrast-color has-text-color" style="margin-bottom:20px;font-size:1.1rem;line-height:1.8">{APPROACH_TEXT}</p>'''

# Find what to replace: from "The Problem We Solve" up to (but not including) the closing divs before "Who Benefits"
# The section ends with several closing </div> tags before the next wp-block-group
# Find the last </p> before the closing divs
last_p_end = after_h1.rfind('</p>') + 4
replace_end = prob_idx + h1_end + last_p_end

old_block = content[prob_idx:replace_end]
print(f"\n\nWill replace ({len(old_block)} chars):\n{repr(old_block[:300])}...")

content = content[:prob_idx] + NEW_BLOCK + content[replace_end:]

# Also ensure "The Problem We Solve" is bright blue
if f'color:{BRIGHT_BLUE}' not in content[:content.find('The Problem We Solve')+50]:
    # Find h1 tag and add color
    h1_start = content.find('<h1', content.find('The Problem We Solve') - 200)
    h1_tag_end = content.find('>', h1_start)
    tag = content[h1_start:h1_tag_end+1]
    if 'style="' in tag:
        new_tag = tag.replace('style="', f'style="color:{BRIGHT_BLUE} !important;')
    else:
        new_tag = tag[:-1] + f' style="color:{BRIGHT_BLUE} !important">'
    content = content.replace(tag, new_tag, 1)
    print("Applied blue to Problem heading")

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("Grid CSS re-added")

# Save
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"\nHomepage update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")

# Verify
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
final = r3.json()['content']['rendered']

prob_section = final[final.find('The Problem We Solve'):final.find('Who Benefits Most')]
print(f"\n=== Final section ===\n{prob_section[:1500]}")

print("\nDone!")
