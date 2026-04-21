"""Fix OpenAPI page - remove Odoo body content, keep only OpenAPI content."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Current length: {len(content)}")

# Find the OpenAPI title
title_idx = content.find('>OpenAPI / Swagger</h2>')
print(f"Title at: {title_idx}")

# Find the <!-- /wp:html --> right after title
title_end = title_idx + len('>OpenAPI / Swagger</h2>')
# Look for <!-- /wp:html --> within next 50 chars
next_close = content.find('<!-- /wp:html -->', title_end, title_end + 50)
if next_close >= 0:
    preamble_end = next_close + len('<!-- /wp:html -->')
    print(f"Title wp:html close at: {next_close}, preamble_end: {preamble_end}")
else:
    # No close tag nearby, just use after </h2>
    preamble_end = title_end
    print(f"No close tag nearby, preamble_end at title_end: {preamble_end}")

preamble = content[:preamble_end]
print(f"Preamble: {len(preamble)} chars")

# Show what comes right after preamble
after = content[preamble_end:preamble_end+200]
print(f"After preamble: {after[:200]}")

# Find where the NEW content starts (Standardized API Documentation)
new_start = content.find('Standardized API Documentation')
if new_start >= 0:
    # Walk back to find the <!-- wp:html --> before it
    wp_open = content.rfind('<!-- wp:html -->', max(0, new_start - 200), new_start)
    if wp_open >= 0:
        new_body = content[wp_open:]
        print(f"New body starts at: {wp_open}, length: {len(new_body)}")
    else:
        # Find the <p> or <h2> before it
        p_start = content.rfind('<p', max(0, new_start - 200), new_start)
        new_body = content[p_start:]
        print(f"New body from <p> at: {p_start}")
else:
    print("ERROR: New content not found! Page may be corrupted.")
    exit(1)

# Build clean page: preamble + new body only
new_content = preamble + '\n' + new_body
print(f"Final content: {len(new_content)} chars")

# Verify
key_caps = len(re.findall(r'Key Capabilities', new_content))
odoo_refs = len(re.findall(r'Odoo', new_content))
print(f"Key Capabilities: {key_caps}, Odoo references: {odoo_refs}")

if key_caps == 1 and odoo_refs == 0:
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
    print(f"Update: {r2.status_code}")
else:
    print(f"WARNING: Expected 1 Key Capabilities and 0 Odoo refs. Got {key_caps} and {odoo_refs}")
    print("Updating anyway...")
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
    print(f"Update: {r2.status_code}")
