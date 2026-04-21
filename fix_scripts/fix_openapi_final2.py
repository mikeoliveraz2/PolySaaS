"""Fix OpenAPI page - strip ALL Odoo content, keep only CSS/toggle, add fresh OpenAPI body."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Current length: {len(content)}")

# Find the toggle button end - that's where CSS/toggle preamble ends
toggle_idx = content.find('ps-dark-toggle')
if toggle_idx < 0:
    print("No toggle found!")
    exit(1)

# Find the closing </script> after the toggle
script_close = content.find('</script>', toggle_idx)
if script_close >= 0:
    # Find the <!-- /wp:html --> after the script
    wp_close = content.find('<!-- /wp:html -->', script_close)
    if wp_close >= 0:
        css_preamble_end = wp_close + len('<!-- /wp:html -->')
    else:
        css_preamble_end = script_close + len('</script>')
else:
    # Find </button> after toggle
    btn_close = content.find('</button>', toggle_idx)
    wp_close = content.find('<!-- /wp:html -->', btn_close)
    css_preamble_end = wp_close + len('<!-- /wp:html -->')

css_preamble = content[:css_preamble_end]
print(f"CSS/toggle preamble: {len(css_preamble)} chars")

# Check what's right after
after = content[css_preamble_end:css_preamble_end+200]
print(f"After preamble: {after[:150]}")

# Now find the new OpenAPI content (Standardized API Documentation)
new_marker = content.find('Standardized API Documentation')
if new_marker >= 0:
    # Walk back to find the start of this section
    wp_open = content.rfind('<!-- wp:html -->', max(0, new_marker - 200), new_marker)
    if wp_open >= 0:
        new_body = content[wp_open:]
    else:
        p_start = content.rfind('<p', max(0, new_marker - 200), new_marker)
        new_body = '\n<!-- wp:html -->\n' + content[p_start:]
    print(f"New body: {len(new_body)} chars")
else:
    print("New content not found, need to rebuild body")
    exit(1)

# Build the title
title_block = '\n<!-- wp:html -->\n<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">OpenAPI / Swagger</h2>\n<!-- /wp:html -->'

# Assemble: CSS/toggle + title + new body
final = css_preamble + title_block + '\n' + new_body
print(f"Final content: {len(final)} chars")

# Verify no Odoo references
odoo_count = len(re.findall(r'Odoo', final, re.IGNORECASE))
key_caps = len(re.findall(r'Key Capabilities', final))
print(f"Odoo refs: {odoo_count}, Key Capabilities: {key_caps}")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": final})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — OpenAPI page cleaned and rebuilt.")
else:
    print(f"Error: {r2.text[:300]}")
