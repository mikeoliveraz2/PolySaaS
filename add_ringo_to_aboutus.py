"""Add Ringo Rivera's headshot to the About Us page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

RINGO_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/ringo-rivera-headshot.jpg"

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find Ringo's section
ringo_idx = content.find('<!-- Ringo Rivera -->')
if ringo_idx < 0:
    print("Ringo Rivera section not found!")
    exit(1)

# Get the chunk around Ringo's section
ringo_section = content[ringo_idx:ringo_idx+1500]
print("Ringo's current section:")
print(ringo_section[:800])
print("---")

# Check if there's already a headshot image for Ringo
if 'ringo-rivera' in content.lower() and '<img' in content[ringo_idx:ringo_idx+500]:
    print("Ringo already has an image.")
else:
    print("No headshot image for Ringo. Adding...")

# Find the placeholder image div for Ringo - it should have something like a gray circle
# Look for the pattern after <!-- Ringo Rivera --> comment
# Find the image placeholder or where to insert
div_start = content.find('<div style="flex:1 1 280px', ringo_idx)
if div_start < 0:
    print("Couldn't find Ringo's card div")
    exit(1)

# Look for existing placeholder image (gray circle or initials)
# Find the image area - typically after the card div opening, there's an image container
card_content = content[div_start:div_start+800]
print("\nRingo card content:")
print(card_content)

# Look for the image placeholder pattern
# Typically: <div style="...border-radius:50%...">RR</div> or similar
placeholder_patterns = [
    re.compile(r'<div[^>]*border-radius:\s*50%[^>]*>[^<]*</div>', re.DOTALL),
    re.compile(r'<img[^>]*placeholder[^>]*>', re.DOTALL),
]

# Find initials placeholder
initials_match = re.search(r'<div[^>]*border-radius:\s*50%[^>]*>(?:RR|[A-Z]{1,2})</div>', card_content)
if initials_match:
    old_placeholder = initials_match.group(0)
    print(f"\nFound initials placeholder: {old_placeholder}")
    new_img = f'<img src="{RINGO_IMG}" alt="Ringo Rivera" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin-bottom:12px;">'
    new_content = content.replace(old_placeholder, new_img)
else:
    # Look for any circular div placeholder
    circ_match = re.search(r'<div style="[^"]*width:\s*120px[^"]*height:\s*120px[^"]*border-radius:\s*50%[^"]*">[^<]*</div>', card_content)
    if circ_match:
        old_placeholder = circ_match.group(0)
        print(f"\nFound circular placeholder: {old_placeholder[:80]}...")
        new_img = f'<img src="{RINGO_IMG}" alt="Ringo Rivera" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin-bottom:12px;">'
        new_content = content.replace(old_placeholder, new_img)
    else:
        # Just look for any div with initials or placeholder in the card
        # Find the first child div after the card opens
        inner_match = re.search(r'(<div style="[^"]*background:#[A-Fa-f0-9]+[^"]*width:\s*\d+px[^"]*height:\s*\d+px[^"]*">)[^<]*(</div>)', card_content)
        if inner_match:
            old_placeholder = inner_match.group(0)
            print(f"\nFound generic placeholder: {old_placeholder[:80]}...")
            new_img = f'<img src="{RINGO_IMG}" alt="Ringo Rivera" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin-bottom:12px;">'
            new_content = content.replace(old_placeholder, new_img)
        else:
            print("\nNo placeholder found. Will insert image after card div opening.")
            # Insert after the opening div of the card + text-align center div
            align_div = content.find('text-align:center', div_start)
            if align_div > 0:
                close_bracket = content.find('>', align_div)
                insert_at = close_bracket + 1
                new_img = f'\n<img src="{RINGO_IMG}" alt="Ringo Rivera" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin-bottom:12px;">'
                new_content = content[:insert_at] + new_img + content[insert_at:]
            else:
                print("Cannot find insertion point!")
                exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"\nUpdate: {r2.status_code}")
if r2.status_code == 200:
    print("Done — Ringo Rivera headshot added to About Us page.")
else:
    print(f"Error: {r2.text[:400]}")
