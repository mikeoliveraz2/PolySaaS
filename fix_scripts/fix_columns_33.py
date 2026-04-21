"""Find and fix the 33% max-width rule that's breaking feature card centering."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1313?context=edit&_fields=content",
                 auth=AUTH, timeout=30)
content = r.json()['content']['raw']

# Find the 33% rule and its full context
pos = content.find('max-width: 33%')
if pos >= 0:
    # Find the surrounding style block
    style_start = content.rfind('<style', 0, pos)
    style_end = content.find('</style>', pos)
    if style_start >= 0 and style_end >= 0:
        style_block = content[style_start:style_end + len('</style>')]
        print(f"Style block containing 33% rule (position {style_start} to {style_end}):")
        print(style_block[:2000])
        print("\n...")

# The problematic CSS block - find the exact rule
# It's: .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; ... }
# This was meant for the 8-app grid but also hits the 2-column feature cards

# Strategy: Replace the blanket 33% rule with one that doesn't apply to feature section
# Better: Just change 33% to something that works for both (like 48%)
# Actually best: remove the max-width:33% entirely, or make it only apply to the apps grid

old_rule = """.wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 30% !important;
    min-width: 250px !important;
    max-width: 33% !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}"""

# Replace with a rule that allows columns to size naturally
# flex: 1 1 auto lets them grow/shrink based on content
new_rule = """.wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 auto !important;
    min-width: 200px !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}"""

if old_rule in content:
    new_content = content.replace(old_rule, new_rule)
    r2 = requests.post(
        f"{BASE}/wp-json/wp/v2/pages/1313",
        auth=AUTH,
        json={"content": new_content},
        timeout=30
    )
    print(f"\nUpdate: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Removed max-width:33% restriction. Columns now size naturally.")
else:
    print("Exact rule not found - trying flexible match...")
    # Try a more flexible match
    pattern = r'\.wp-block-columns\.is-layout-flex\s*>\s*\.wp-block-column\s*\{[^}]*max-width:\s*33%[^}]*\}'
    match = re.search(pattern, content)
    if match:
        old_block = match.group(0)
        print(f"Found via regex:\n{old_block}")
        new_content = content.replace(old_block, new_rule)
        r2 = requests.post(
            f"{BASE}/wp-json/wp/v2/pages/1313",
            auth=AUTH,
            json={"content": new_content},
            timeout=30
        )
        print(f"\nUpdate: {r2.status_code}")
    else:
        print("Could not find the rule even with regex!")
        # Show context around the 33% occurrence
        print(f"\nContext around max-width: 33%:")
        print(content[max(0,pos-300):pos+300])
