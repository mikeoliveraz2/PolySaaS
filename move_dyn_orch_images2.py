"""Move Dynamic Orchestration diagrams to after the existing event-driven image, before Key Capabilities."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find our image block
marker = 'dynamic-orchestration-agent-flow'
marker_idx = content.find(marker)
block_start = content.rfind('<!-- wp:html -->', 0, marker_idx)
block_end = content.find('<!-- /wp:html -->', marker_idx) + len('<!-- /wp:html -->')
image_block = content[block_start:block_end]
print(f"Image block: {block_start}..{block_end}")

# Remove it
content_clean = content[:block_start] + content[block_end:]

# Now find landmarks in the cleaned content
title_idx = content_clean.find('>Dynamic Orchestration</h2>')
intro_idx = content_clean.find('without writing code')
event_img_idx = content_clean.find('Event-Driven Architecture')
if event_img_idx < 0:
    event_img_idx = content_clean.find('Event-driven architecture powering')
key_cap_idx = content_clean.find('Key Capabilities')

print(f"Title at: {title_idx}")
print(f"Intro text at: {intro_idx}")
print(f"Event-driven image at: {event_img_idx}")
print(f"Key Capabilities at: {key_cap_idx}")

# Show what's between the event image and Key Capabilities
if event_img_idx > 0 and key_cap_idx > 0:
    between = content_clean[event_img_idx:key_cap_idx]
    print(f"\nBetween event image and Key Caps ({len(between)} chars):")
    print(between[:300])

# Insert AFTER the event-driven image block, BEFORE Key Capabilities
# Find the <!-- /wp:html --> that closes the block containing the event-driven image
if event_img_idx > 0:
    wp_close_after_event = content_clean.find('<!-- /wp:html -->', event_img_idx)
    if wp_close_after_event > 0:
        insert_at = wp_close_after_event + len('<!-- /wp:html -->')
        print(f"\nInserting at position {insert_at} (after event-driven image block)")
        new_content = content_clean[:insert_at] + '\n' + image_block + '\n' + content_clean[insert_at:]
    else:
        print("Could not find wp:html close after event image")
        exit(1)
else:
    # Fallback: insert before Key Capabilities
    kc_block = content_clean.rfind('<!-- wp:html -->', 0, key_cap_idx)
    insert_at = kc_block if kc_block > 0 else key_cap_idx
    print(f"\nFallback: inserting at {insert_at}")
    new_content = content_clean[:insert_at] + '\n' + image_block + '\n' + content_clean[insert_at:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — diagrams moved after intro/event image, before Key Capabilities.")
else:
    print(f"Error: {r2.text[:300]}")
