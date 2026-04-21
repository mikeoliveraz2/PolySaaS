"""Remove duplicate CTA, add buttons to existing contact section."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Show the "Quick 15-Minute Call" section
pos = content.find('Quick 15-Minute Call')
start = max(0, pos - 300)
end = min(len(content), pos + 800)
print("=== Existing contact section ===")
print(content[start:end])
print("\n===")

# 1. Remove the duplicate "Seed Round" block
seed_pat = r'<!-- wp:html -->\s*<div[^>]*>.*?Interested in Our Seed Round\?.*?</div>\s*<!-- /wp:html -->'
seed_match = re.search(seed_pat, content, re.DOTALL)
if seed_match:
    content = content.replace(seed_match.group(0), '')
    print("Removed duplicate Seed Round block")

# 2. Find the LinkedIn link in the contact section and add CTA buttons after it
old_linkedin = 'LinkedIn &rarr;</a>'
if old_linkedin not in content:
    old_linkedin = 'LinkedIn →</a>'
if old_linkedin not in content:
    # try HTML entity
    old_linkedin = 'LinkedIn &#8594;</a>'

if old_linkedin in content:
    new_linkedin = old_linkedin + '''
<div style="margin-top:20px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
  <a href="/schedule-demo/" style="display:inline-block;background:#0F766E;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem">Schedule a Meeting</a>
  <a href="mailto:michael.oliver@polysaas.online" style="display:inline-block;background:transparent;color:#0F766E;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;border:2px solid #0F766E">Email Us</a>
</div>'''
    content = content.replace(old_linkedin, new_linkedin)
    print("Added CTA buttons after LinkedIn link")
else:
    print("LinkedIn link not found, searching...")
    linkedin_pos = content.find('LinkedIn')
    if linkedin_pos > 0:
        print(content[linkedin_pos:linkedin_pos+100])

# Save
r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS")
else:
    print(f"Error: {r2.text[:300]}")
