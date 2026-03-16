"""Remove the trailing roadmap image block from the About Us page.
It appears after the footer and needs to be removed."""
import requests, json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

PAGE_ID = 1345

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']

# The trailing content is a <!-- wp:html --> block with the roadmap image
# Find and remove it - it starts with "<!-- wp:html -->\n<div" after the footer
trailing_block = '''<!-- wp:html -->
<div style="text-align:center;margin:20px auto 32px;max-width:900px;">
<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/polysaas-roadmap-timeline.jpg" alt="PolySaaS Roadmap Timeline" style="width:100%;max-width:860px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.12);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:10px;font-style:italic;">PolySaaS 2025 Roadmap &mdash; Q1 through Q4 milestones</p>

<!-- /wp:html -->'''

if trailing_block in content:
    new_content = content.replace(trailing_block, '').rstrip()
    print(f"Found and removed trailing roadmap block")
    print(f"Old length: {len(content)}, New length: {len(new_content)}")
    
    r2 = s.post(
        f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}",
        json={"content": new_content},
        timeout=30
    )
    print(f"Update status: {r2.status_code}")
    if r2.status_code == 200:
        print("Done! Roadmap image removed from below the footer.")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    # Try a more flexible match
    pattern = r'<!-- wp:html -->\s*<div[^>]*>\s*<img[^>]*polysaas-roadmap-timeline[^>]*>.*?<!-- /wp:html -->'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        new_content = content[:match.start()] + content[match.end():]
        new_content = new_content.rstrip()
        print(f"Found trailing block via regex (pos {match.start()}-{match.end()})")
        print(f"Old length: {len(content)}, New length: {len(new_content)}")
        
        r2 = s.post(
            f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}",
            json={"content": new_content},
            timeout=30
        )
        print(f"Update status: {r2.status_code}")
        if r2.status_code == 200:
            print("Done! Roadmap image removed from below the footer.")
        else:
            print(f"Error: {r2.text[:300]}")
    else:
        print("ERROR: Could not find trailing roadmap block!")
        print("Last 500 chars of content:")
        print(content[-500:])
