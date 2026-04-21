"""
1. Update Mike Oliver's title to 'Founder and Chief Architect'
2. Add a simple H2 header above the hero with 20px padding
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get About Us page
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"slug": "about-us", "_fields": "id,content"})
pages = r.json()
if not pages:
    print("ERROR: About Us page not found!")
    sys.exit(1)

page = pages[0]
pid = page['id']
content = page['content']['rendered']
print(f"About Us page ID: {pid}, content length: {len(content)}")

# 1. Update Mike's title from "Founder & CEO" to "Founder and Chief Architect"
old_title = "Founder &amp; CEO"
new_title = "Founder and Chief Architect"
if old_title in content:
    content = content.replace(old_title, new_title)
    print(f"Updated: '{old_title}' -> '{new_title}'")
else:
    # Try without HTML entity
    old_title2 = "Founder & CEO"
    if old_title2 in content:
        content = content.replace(old_title2, new_title)
        print(f"Updated: '{old_title2}' -> '{new_title}'")
    else:
        print("WARNING: Could not find Mike's title to update")
        # Search for what's there
        for term in ['Founder', 'CEO', 'Chief']:
            idx = content.find(term)
            if idx >= 0:
                print(f"  Found '{term}' at {idx}: ...{content[max(0,idx-30):idx+50]}...")

# 2. Add H2 "About Us" header above the hero with 20px padding
# Find the beginning of the actual page content (after any wp:html CSS blocks)
# The hero section likely starts with "About PolySaaS" heading
hero_marker = '>About PolySaaS<'
if hero_marker in content:
    idx = content.find(hero_marker)
    # Find the opening tag for this heading
    tag_start = content.rfind('<h', 0, idx)
    if tag_start >= 0:
        # Insert H2 before the hero section
        h2_block = '<!-- wp:html -->\n<h2 style="text-align:center;padding:20px 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">About Us</h2>\n<!-- /wp:html -->\n'
        
        # Check if there's already an "About Us" H2 above
        before_hero = content[:tag_start]
        if '>About Us<' in before_hero:
            print("H2 'About Us' header already exists above hero")
        else:
            content = content[:tag_start] + h2_block + content[tag_start:]
            print("Added H2 'About Us' header above hero with 20px padding")
    else:
        print("WARNING: Could not find hero heading tag start")
else:
    print(f"WARNING: Hero marker '{hero_marker}' not found")
    # Search for it
    for term in ['About PolySaaS', 'About Poly', 'hero']:
        idx = content.find(term)
        if idx >= 0:
            print(f"  Found '{term}' at {idx}")

# Save
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
if r2.status_code == 200:
    print(f"Page updated successfully")
else:
    print(f"ERROR: {r2.status_code} - {r2.text[:300]}")

print("Done!")
