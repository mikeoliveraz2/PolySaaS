"""Check if the Dynamic Orchestration page HTML has unclosed tags breaking the footer."""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
content = page['content']['raw']

# Count all opening and closing div tags
open_divs = len(re.findall(r'<div[\s>]', content))
close_divs = len(re.findall(r'</div>', content))
print(f"Opening <div>: {open_divs}")
print(f"Closing </div>: {close_divs}")
print(f"Difference: {open_divs - close_divs}")

# Check for unclosed tags
for tag in ['div', 'p', 'h2', 'h3', 'a', 'span', 'style']:
    opens = len(re.findall(f'<{tag}[\\s>]', content))
    closes = len(re.findall(f'</{tag}>', content))
    if opens != closes:
        print(f"  MISMATCH: <{tag}> opens={opens}, closes={closes}, diff={opens - closes}")

# Show the last 500 chars of content to see how it ends
print(f"\n=== Last 500 chars of content ===")
print(content[-500:])
