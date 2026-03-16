"""Move Dynamic Orchestration diagrams from above the title to below the intro text, before Key Capabilities."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Page id={pid}, length={len(content)}")

# Find the image block we inserted (it's a wp:html block with the two diagrams)
marker_start = content.find('dynamic-orchestration-agent-flow')
if marker_start < 0:
    print("Could not find agent-flow image!")
    exit(1)

# Find the enclosing wp:html block
block_start = content.rfind('<!-- wp:html -->', 0, marker_start)
block_end = content.find('<!-- /wp:html -->', marker_start) + len('<!-- /wp:html -->')

image_block = content[block_start:block_end]
print(f"Found image block: chars {block_start}..{block_end} ({len(image_block)} chars)")

# Remove it from current position
content_without = content[:block_start] + content[block_end:]

# Now find Key Capabilities in the cleaned content
key_cap_idx = content_without.find('Key Capabilities')
if key_cap_idx < 0:
    print("Could not find Key Capabilities!")
    exit(1)

# Find the wp:html block start before Key Capabilities
insert_before = content_without.rfind('<!-- wp:html -->', 0, key_cap_idx)
if insert_before < 0:
    insert_before = key_cap_idx

print(f"Inserting image block at position {insert_before} (before Key Capabilities)")

new_content = content_without[:insert_before] + '\n' + image_block + '\n' + content_without[insert_before:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — diagrams moved below intro, before Key Capabilities.")
else:
    print(f"Error: {r2.text[:300]}")
