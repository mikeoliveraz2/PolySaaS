"""Remove the duplicate CTA and add buttons to the existing contact section."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# First, remove the duplicate "Interested in Our Seed Round?" block I just added
seed_block = re.search(
    r'<!-- wp:html -->\s*<div[^>]*>.*?Interested in Our Seed Round\?.*?</div>\s*<!-- /wp:html -->',
    content, re.DOTALL
)
if seed_block:
    content = content.replace(seed_block.group(0), '')
    print("Removed duplicate Seed Round CTA block")

# Now find the existing "Quick 15-Minute Call" section and show it
call_pos = content.find('Quick 15-Minute Call')
if call_pos > 0:
    start = max(0, call_pos - 500)
    end = min(len(content), call_pos + 1500)
    print(f"\n=== Existing contact section ===")
    print(content[start:end])
