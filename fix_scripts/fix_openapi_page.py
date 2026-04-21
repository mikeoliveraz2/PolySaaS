"""Fix OpenAPI page - remove old duplicate content, keep only new layout."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Current length: {len(content)}")

# Find the title H2
title_pattern = r'(<h2[^>]*>OpenAPI / Swagger</h2>\s*<!-- /wp:html -->)'
title_match = re.search(title_pattern, content)
if not title_match:
    # Try without wp:html comment
    title_pattern = r'(<h2[^>]*>OpenAPI / Swagger</h2>)'
    title_match = re.search(title_pattern, content)

if title_match:
    print(f"Title found at {title_match.start()}-{title_match.end()}")
    preamble_end = title_match.end()
else:
    print("Title not found!")
    exit(1)

# Find where the NEW content starts (Standardized API Documentation)
new_start = content.find('Standardized API Documentation')
if new_start < 0:
    print("New content marker not found!")
    exit(1)

# Find the H2 containing it
h2_before_new = content.rfind('<h2', max(0, new_start - 100), new_start)
print(f"New content H2 starts at {h2_before_new}")

# Everything from preamble_end to h2_before_new is the OLD content to remove
old_section = content[preamble_end:h2_before_new]
print(f"Old section to remove: {len(old_section)} chars")
print(f"Preview: {old_section[:200]}...")

# Build clean content: preamble + new content only
new_content = content[:preamble_end] + '\n' + content[h2_before_new:]
print(f"New length: {len(new_content)}")

# Verify no duplicate "Key Capabilities"
key_caps = len(re.findall(r'Key Capabilities', new_content))
print(f"'Key Capabilities' occurrences: {key_caps}")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done - duplicate content removed.")
