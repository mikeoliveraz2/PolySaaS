"""
Scrape the full pricing page from polysaas.online to find the value proposition text
that appears below the three pricing tiers.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

r = requests.get("https://polysaas.online/pricing/", timeout=15)
html = r.text

# Strip scripts and styles
text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

# Get all text after "Get Started" (last tier button) to "Back to Home"
# This should capture the value prop footer section
match = re.search(r'Get Started.*?(All plans.*?(?:Contact us[^<]*|enterprise[^<]*))', text, re.DOTALL)
if match:
    chunk = match.group(1)
    chunk = re.sub(r'<[^>]+>', '\n', chunk)
    chunk = re.sub(r'\n\s*\n+', '\n', chunk).strip()
    print("=== Value proposition text ===")
    print(chunk)
else:
    print("Pattern not found, dumping post-pricing section...")
    # Find everything between last "Get Started" and "Back to Home"
    idx = html.rfind('Get Started')
    end = html.find('Back to Home', idx) if idx > 0 else -1
    if idx > 0 and end > 0:
        section = html[idx:end]
        section = re.sub(r'<[^>]+>', '\n', section)
        section = re.sub(r'\n\s*\n+', '\n', section).strip()
        print(section)

# Also look for any additional sections on the page
print("\n=== Full page text (pricing area) ===")
# Find from "Pricing Plans" to end of content
start = html.find('Pricing Plans')
if start > 0:
    section = html[start:start+5000]
    section = re.sub(r'<script[^>]*>.*?</script>', '', section, flags=re.DOTALL)
    section = re.sub(r'<style[^>]*>.*?</style>', '', section, flags=re.DOTALL)
    section = re.sub(r'<[^>]+>', '\n', section)
    section = re.sub(r'\n\s*\n+', '\n', section).strip()
    for line in section.split('\n'):
        line = line.strip()
        if line:
            print(f"  {line}")
