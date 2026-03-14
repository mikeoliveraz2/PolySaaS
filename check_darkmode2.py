"""Check if dark mode CSS rules exist on pages"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = {p['slug']: p for p in r.json()}

# Check architecture page full raw content
arch = pages['architecture']
raw = arch['content']['raw']

# Check for dark mode presence
has_dark_mode_css = 'body.dark-mode' in raw
has_root_vars = ':root' in raw
has_toggle_btn = 'ps-theme-toggle' in raw
has_toggle_script = 'ps-dark-mode' in raw

print(f"architecture page:")
print(f"  body.dark-mode CSS: {has_dark_mode_css}")
print(f"  :root variables: {has_root_vars}")
print(f"  Toggle button: {has_toggle_btn}")
print(f"  Toggle script: {has_toggle_script}")

# Find exactly what's in the style block
style_blocks = re.findall(r'<style>(.*?)</style>', raw, re.DOTALL)
for i, sb in enumerate(style_blocks):
    print(f"\n  Style block {i} ({len(sb)} chars):")
    # Show all CSS selectors
    selectors = re.findall(r'([^\{]+)\{', sb)
    for sel in selectors[:20]:
        print(f"    selector: {sel.strip()}")

# Now check homepage
home = pages['home']
hraw = home['content']['raw']
print(f"\nhome page:")
print(f"  body.dark-mode CSS: {'body.dark-mode' in hraw}")

hstyle_blocks = re.findall(r'<style>(.*?)</style>', hraw, re.DOTALL)
for i, sb in enumerate(hstyle_blocks):
    print(f"\n  Style block {i} ({len(sb)} chars):")
    selectors = re.findall(r'([^\{]+)\{', sb)
    for sel in selectors[:20]:
        print(f"    selector: {sel.strip()}")
