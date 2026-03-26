"""Extract the dark mode toggle + CSS from an existing polysaas.online page."""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(BASE + "/wp-json/wp/v2/pages", params={
    "slug": "dynamic-orchestration", "context": "edit", "_fields": "id,content"
})
pages = r.json()
if not pages:
    print("Page not found")
    sys.exit(1)

content = pages[0]['content']['raw']

# Find the dark-mode CSS block
dm_idx = content.find('body.dark-mode')
if dm_idx >= 0:
    style_start = content.rfind('<style', 0, dm_idx)
    style_end = content.find('</style>', dm_idx) + len('</style>')
    print("=== DARK MODE STYLE BLOCK ===")
    print(content[style_start:style_end])
else:
    print("No body.dark-mode found")

# Find the toggle button block
toggle_idx = content.find('ps-dark-toggle')
if toggle_idx >= 0:
    block_start = content.rfind('<!-- wp:html -->', 0, toggle_idx)
    block_end = content.find('<!-- /wp:html -->', toggle_idx) + len('<!-- /wp:html -->')
    print("\n=== TOGGLE BUTTON BLOCK ===")
    print(content[block_start:block_end])
else:
    print("No toggle button found")
