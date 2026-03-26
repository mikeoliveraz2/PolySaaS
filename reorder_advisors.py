"""Reorder advisor cards on About Us page.
New order: Feyzi Fatehi, John Shackleton, Francis Uy, Scott Chate
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

print("=== Fetching About Us page ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "about-us", "context": "edit", "_fields": "id,content"},
          timeout=30)
about = r.json()[0]
raw = about['content']['raw']
page_id = about['id']
print(f"  Page ID: {page_id}, length: {len(raw)} chars")

NAMES = ['Scott Chate', 'Feyzi Fatehi', 'Francis Uy', 'John Shackleton']

def extract_card(content, name):
    """Extract a full advisor card (comment + div) by name."""
    comment = f'<!-- {name} -->'
    comment_idx = content.find(comment)
    if comment_idx < 0:
        print(f"  ERROR: {name} comment not found")
        return None, None, None

    comment_tag_start = content.rfind('<p>', max(0, comment_idx - 20), comment_idx)
    if comment_tag_start < 0:
        comment_tag_start = comment_idx
    comment_tag_end = content.find('</p>', comment_idx) + 4

    card_div_start = content.find('<div style="flex:1 1 280px', comment_tag_end)
    if card_div_start < 0 or card_div_start > comment_tag_end + 50:
        print(f"  ERROR: {name} card div not found near comment")
        return None, None, None

    depth = 0
    i = card_div_start
    card_div_end = None
    while i < len(content):
        if content[i:i+4] == '<div':
            depth += 1
            i += 4
        elif content[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                card_div_end = i + 6
                break
            i += 6
        else:
            i += 1

    if not card_div_end:
        print(f"  ERROR: Could not find end of {name} card")
        return None, None, None

    card_html = content[comment_tag_start:card_div_end]
    print(f"  {name}: extracted {len(card_html)} chars ({comment_tag_start}:{card_div_end})")
    return card_html, comment_tag_start, card_div_end

print("\n=== Extracting advisor cards ===")
cards = {}
positions = []
for name in NAMES:
    html, start, end = extract_card(raw, name)
    if html:
        cards[name] = html
        positions.append((start, end, name))

if len(cards) != 4:
    print(f"\n  ERROR: Only found {len(cards)}/4 cards. Aborting.")
    sys.exit(1)

positions.sort(key=lambda x: x[0])
print(f"\n  Current order: {[p[2] for p in positions]}")

DESIRED_ORDER = ['Feyzi Fatehi', 'John Shackleton', 'Francis Uy', 'Scott Chate']
print(f"  Desired order: {DESIRED_ORDER}")

first_start = positions[0][0]
last_end = positions[-1][1]

old_section = raw[first_start:last_end]
new_section = "\n".join(cards[name] for name in DESIRED_ORDER)

raw = raw[:first_start] + new_section + raw[last_end:]

print(f"\n=== Updating page (new length: {len(raw)} chars) ===")
r2 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
    json={"content": raw},
    timeout=30,
)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("\n  SUCCESS! Advisor order updated:")
    for i, name in enumerate(DESIRED_ORDER, 1):
        print(f"    {i}. {name}")
else:
    print(f"  ERROR: {r2.text[:500]}")
