"""Fix CTA section text colors for dark mode on investor page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# The Seed Round CTA has hardcoded dark text colors that are invisible in dark mode
# Fix heading color and paragraph text color to use CSS vars

old = 'color:var(--ps-primary,#001F3F)">Interested in Our Seed Round?'
new = 'color:var(--ps-inv-heading,#2563EB)">Interested in Our Seed Round?'

if old in content:
    content = content.replace(old, new)
    print("Fixed heading color")

old2 = 'color:#111827;line-height:1.6">'
new2 = 'color:var(--ps-text,#111827);line-height:1.6">'

if old2 in content:
    content = content.replace(old2, new2)
    print("Fixed paragraph text color")

# Fix the "Email Us" button border color for dark mode visibility
old3 = 'border:2px solid #0F766E">Email Us</a>'
new3 = 'border:2px solid #5EEAD4">Email Us</a>'

if old3 in content:
    content = content.replace(old3, new3)
    print("Fixed Email Us button border")

# Fix the background to work in dark mode
old_bg = 'background:linear-gradient(135deg,var(--ps-card-bg,#F9FAFB),var(--ps-bg-alt,#F3F4F6));border:1px solid var(--ps-border,#E5E7EB)'
new_bg = 'background:var(--ps-card-bg,#F9FAFB);border:1px solid var(--ps-border,#334155)'

if old_bg in content:
    content = content.replace(old_bg, new_bg)
    print("Fixed background for dark mode")

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - CTA dark mode text fixed")
else:
    print(f"Error: {r2.text[:300]}")
