"""
Compare the CSS blocks between homepage and About Us to find what's different.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

home = [p for p in pages if p['slug'] == 'home'][0]
about = [p for p in pages if p['slug'] == 'about-us'][0]

# Extract all style blocks from each
def get_styles(raw):
    styles = []
    for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL):
        if '<style' in block:
            clean = re.sub(r'</?p>', '', block)
            styles.append(clean)
    # Also check for loose style blocks
    for block in re.findall(r'<style[^>]*>(.*?)</style>', raw, re.DOTALL):
        styles.append(block)
    return styles

home_styles = get_styles(home['content']['raw'])
about_styles = get_styles(about['content']['raw'])

print(f"Homepage: {len(home_styles)} style sections")
print(f"About Us: {len(about_styles)} style sections")

# Compare unique CSS rules
def extract_rules(styles):
    rules = set()
    for s in styles:
        for line in s.split('\n'):
            line = line.strip()
            if line and not line.startswith('/*') and not line.startswith('*') and not line.startswith('<'):
                rules.add(line)
    return rules

home_rules = extract_rules(home_styles)
about_rules = extract_rules(about_styles)

only_home = home_rules - about_rules
only_about = about_rules - home_rules

if only_home:
    print(f"\n=== Rules ONLY on homepage ({len(only_home)}) ===")
    for r in sorted(only_home):
        if any(kw in r.lower() for kw in ['margin', 'padding', 'height', 'top', 'content', 'entry', 'hero', 'block']):
            print(f"  {r}")

# Also show first 500 chars of each page's content after CSS blocks
home_raw = home['content']['raw']
about_raw = about['content']['raw']

# Find where actual content starts on each
for name, raw in [("HOME", home_raw), ("ABOUT", about_raw)]:
    last_toggle = raw.rfind('ps-dark-toggle')
    if last_toggle > 0:
        end = raw.find('<!-- /wp:html -->', last_toggle) + len('<!-- /wp:html -->')
        content_start = raw[end:end+500].strip()
        print(f"\n=== {name} content after toggle ===")
        print(content_start[:400])
