"""Remove the second image (man on laptop / hubspot flow) from Dynamic Orchestration page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find the second image block and its wrapper div
# Structure: <div style="text-align:center;margin:20px auto;">
#   <img ... alt="Customer Signup Flow" .../>
#   <p ...>caption</p>
# </div>

img_match = re.search(
    r'<div style="text-align:center;margin:20px auto;">\s*'
    r'<img[^>]*alt="Customer Signup Flow"[^>]*/>\s*'
    r'(?:<p[^>]*>.*?</p>\s*)?'
    r'</div>',
    content,
    re.DOTALL
)

if img_match:
    print(f"Found image block at {img_match.start()}-{img_match.end()}")
    print(f"Removing: {img_match.group()[:200]}...")
    content = content[:img_match.start()] + content[img_match.end():]
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("Done - second image removed.")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("Could not find the image block. Trying broader search...")
    # Try matching just around the image
    idx = content.find('alt="Customer Signup Flow"')
    if idx >= 0:
        # Find the enclosing div
        div_start = content.rfind('<div', max(0, idx - 200), idx)
        div_end = content.find('</div>', idx)
        if div_start >= 0 and div_end >= 0:
            block = content[div_start:div_end + 6]
            print(f"Found block ({len(block)} chars):")
            print(block[:300])
            content = content[:div_start] + content[div_end + 6:]
            r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
            print(f"Update: {r2.status_code}")
        else:
            print(f"Could not find enclosing div (div_start={div_start}, div_end={div_end})")
    else:
        # Maybe it's "Example" alt text
        idx2 = content.find('hubspot-flow')
        if idx2 >= 0:
            print(f"Found 'hubspot-flow' at {idx2}")
            ctx = content[max(0,idx2-300):idx2+300]
            print(f"Context: {ctx}")
