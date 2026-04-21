"""Move neural network background to only behind the logo, revert heading."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find the current hero block with background
hero_pos = content.find("hero-bg-neural")
if hero_pos < 0:
    print("Hero bg not found!")
    sys.exit(1)

# Get a window around the hero bg to see the full block
start = content.rfind("<!-- wp:html -->", 0, hero_pos)
end = content.find("<!-- /wp:html -->", hero_pos) + len("<!-- /wp:html -->")
hero_block = content[start:end]
print("=== Current hero block ===")
print(hero_block[:600])
print("...")

# Now find the logo/image block that follows
# Search after the hero block for the logo image
after_hero = content[end:]
print("\n=== After hero block (first 1500 chars) ===")
print(after_hero[:1500])
