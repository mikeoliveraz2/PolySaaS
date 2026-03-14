"""Check what's actually in the architecture page now"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = {p['slug']: p for p in r.json()}

raw = pages['architecture']['content']['raw']

# Check if body.dark-mode exists
print(f"Has body.dark-mode: {'body.dark-mode' in raw}")
print(f"Has :root: {':root' in raw}")
print(f"Has --ps-primary: #60A5FA: {'--ps-primary: #60A5FA' in raw}")

# Find the toggle block
toggle_match = re.search(r'onclick="(.*?)"', raw)
if toggle_match:
    print(f"\nToggle onclick: {toggle_match.group(1)[:200]}...")

# Find all style blocks and check for <p> contamination
style_blocks = re.findall(r'<style>(.*?)</style>', raw, re.DOTALL)
print(f"\n{len(style_blocks)} style blocks found")
for i, sb in enumerate(style_blocks):
    has_p = '<p>' in sb or '</p>' in sb
    has_dark = 'body.dark-mode' in sb
    print(f"  Block {i}: {len(sb)} chars, <p> contamination={has_p}, dark-mode={has_dark}")
    if has_p:
        # Show first few lines
        lines = sb.split('\n')[:5]
        for line in lines:
            print(f"    | {line[:120]}")
