"""Add CTA buttons with exact string match."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

old = 'LinkedIn &rarr;</a>\n  </p>\n</div>'
new = '''LinkedIn &rarr;</a>
  </p>
  <div style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
    <a href="/schedule-demo/" style="display:inline-block;background:#0F766E;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem">Schedule a Meeting</a>
    <a href="mailto:michael.oliver@polysaas.online" style="display:inline-block;background:transparent;color:#0F766E;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;border:2px solid #0F766E">Email Us</a>
  </div>
</div>'''

if old in content:
    content = content.replace(old, new)
    print("Inserted CTA buttons")
else:
    print("Pattern not found")
    sys.exit(1)

# Also remove the Seed Round duplicate if present
seed_start = content.find('Interested in Our Seed Round?')
if seed_start > 0:
    block_start = content.rfind('<!-- wp:html -->', 0, seed_start)
    block_end = content.find('<!-- /wp:html -->', seed_start)
    if block_start > 0 and block_end > 0:
        content = content[:block_start] + content[block_end + len('<!-- /wp:html -->'):]
        print("Removed Seed Round duplicate")

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print(f"SUCCESS - {len(content)} chars")
else:
    print(f"Error: {r2.text[:300]}")
