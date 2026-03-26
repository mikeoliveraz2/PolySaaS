"""Add CTA buttons to investor contact section and remove duplicate Seed Round block."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]
print(f"Content: {len(content)} chars")

# Remove the duplicate "Seed Round" block using exact string match
seed_start = content.find('Interested in Our Seed Round?')
if seed_start > 0:
    # Find the wp:html block around it
    block_start = content.rfind('<!-- wp:html -->', 0, seed_start)
    block_end = content.find('<!-- /wp:html -->', seed_start)
    if block_start > 0 and block_end > 0:
        block_end += len('<!-- /wp:html -->')
        seed_block = content[block_start:block_end]
        content = content.replace(seed_block, '')
        print(f"Removed Seed Round block ({len(seed_block)} chars)")

# Now add CTA buttons inside the existing contact section
# Find the closing </p> </div> of the inv-cta section
old_end = """</a>
  </p>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-disclaimer">"""

if old_end in content:
    new_end = """</a>
  </p>
  <div style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
    <a href="/schedule-demo/" style="display:inline-block;background:#0F766E;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem">Schedule a Meeting</a>
    <a href="mailto:michael.oliver@polysaas.online" style="display:inline-block;background:transparent;color:#0F766E;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;border:2px solid #0F766E">Email Us</a>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-disclaimer">"""
    content = content.replace(old_end, new_end)
    print("Added CTA buttons to contact section")
else:
    print("Exact pattern not found, trying alternate...")
    # Show what's near LinkedIn
    lpos = content.find('linkedin.com/in/')
    if lpos > 0:
        print(repr(content[lpos:lpos+200]))

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print(f"SUCCESS - {len(content)} chars saved")
else:
    print(f"Error: {r2.text[:300]}")
