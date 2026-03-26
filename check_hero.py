"""Check current hero section structure on the homepage."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find the hero section - it starts with "Industrial Strength SaaS"
hero_pos = content.find('Industrial Strength SaaS')
if hero_pos > 0:
    # Go back to find the start of the block
    start = max(0, hero_pos - 1000)
    end = min(len(content), hero_pos + 500)
    print("=== Hero section ===")
    print(content[start:end])

# Also check what comes right after the style blocks (first content block)
# Find the end of the last style/toggle block and the first content
first_content = content.find('<!-- wp:heading')
if first_content < 0:
    first_content = content.find('<h1')
if first_content < 0:
    first_content = content.find('<h2')
    
print(f"\n=== First content block position: {first_content} ===")
if first_content > 0:
    print(content[first_content:first_content+500])
