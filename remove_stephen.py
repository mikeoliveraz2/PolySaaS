"""
Remove Stephen Bird from the Board of Advisors on the About Us page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,content"
}).json()
about = pages[0]
raw = about['content']['raw']

# Find Stephen Bird's advisor card
stephen_idx = raw.find('Stephen Bird')
if stephen_idx < 0:
    stephen_idx = raw.find('Stephen')
if stephen_idx < 0:
    print("Stephen Bird not found on page!")
    sys.exit(1)

print(f"Found 'Stephen Bird' at position {stephen_idx}")

# Show context
area = raw[max(0,stephen_idx-400):stephen_idx+400]
print(f"Context:\n{area}\n")

# Find the card div containing Stephen - it should be a flex item like the other advisor cards
# Pattern: <div style="flex:1 1 280px;max-width:380px;...">...<h3>Stephen Bird</h3>...</div>
# Need to find the start of this card div and its end

# Go back to find the opening div of Stephen's card
search_back = raw[:stephen_idx]
# Find the last card-style div before Stephen
card_start = search_back.rfind('<div style="flex:1 1 280px')
if card_start < 0:
    card_start = search_back.rfind('<div style="flex:')
    
if card_start < 0:
    print("Could not find Stephen's card start")
    sys.exit(1)

# Verify this card actually contains Stephen
if 'Stephen' not in raw[card_start:stephen_idx+50]:
    print("Card doesn't seem right - checking further back")
    # Try previous occurrence
    card_start = search_back[:card_start].rfind('<div style="flex:1 1 280px')

print(f"Card starts at: {card_start}")
print(f"Card start text: {raw[card_start:card_start+80]}")

# Find the end of this card div by counting div depth
depth = 0
i = card_start
card_end = None
while i < len(raw):
    if raw[i:i+4] == '<div':
        depth += 1
        i += 4
    elif raw[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            card_end = i + 6
            break
        i += 6
    else:
        i += 1

if card_end is None:
    print("Could not find card end")
    sys.exit(1)

old_card = raw[card_start:card_end]
print(f"\nRemoving card ({len(old_card)} chars):")
text = re.sub(r'<[^>]+>', ' ', old_card)
text = re.sub(r'\s+', ' ', text).strip()
print(f"  Text: {text}")

new_raw = raw[:card_start] + raw[card_end:]
print(f"\nOld length: {len(raw)}, New length: {len(new_raw)}")

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": new_raw})
print(f"Update: {r.status_code}")
if r.status_code == 200:
    print("Stephen Bird removed from Board of Advisors")
