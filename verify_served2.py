"""Find the exact location of the red background in the served HTML."""
import requests, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
url = f"{BASE}/?nocache={int(time.time())}"
r = requests.get(url, timeout=30)
html = r.text

# Find ALL occurrences of 'background:red'
pos = 0
count = 0
while True:
    pos = html.find('background:red', pos)
    if pos < 0:
        break
    count += 1
    start = max(0, pos - 200)
    end = min(len(html), pos + 200)
    print(f"\n=== Occurrence {count} at position {pos} ===")
    print(html[start:end])
    pos += 1

print(f"\nTotal 'background:red' occurrences: {count}")

# Find the Platform Features heading with id attribute
pos = html.find('id="platform-features"')
while pos > 0 and html[pos] != '<':
    pos -= 1
# Get context
print(f"\n\n=== Platform Features heading and surrounding 800 chars ===")
start = max(0, pos - 600)
end = min(len(html), pos + 200)
print(html[start:end])

# Check: is the user perhaps looking at a different URL?
print(f"\n\n=== Page canonical URL ===")
import re
canonical = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)
if canonical:
    print(f"Canonical: {canonical.group(1)}")
    
# Check for front page setting
ogurl = re.search(r'<meta[^>]+property="og:url"[^>]+content="([^"]+)"', html)
if ogurl:
    print(f"OG URL: {ogurl.group(1)}")
