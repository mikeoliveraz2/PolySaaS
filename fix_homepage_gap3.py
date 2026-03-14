"""
Reduce gap between H2 title and logo on homepage:
1. Reduce H2 padding
2. Remove empty <p><br /></p> between H2 and content
3. Check logo container margins
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "home", "context": "edit", "_fields": "id,content"
}).json()
home = pages[0]
raw = home['content']['raw']

changes = 0

# 1. Reduce H2 title padding
old_h2 = '<h2 style="text-align:center;padding:20px 0 10px 0;margin:0;'
new_h2 = '<h2 style="text-align:center;padding:5px 0 0 0;margin:0;'
if old_h2 in raw:
    raw = raw.replace(old_h2, new_h2)
    print("Reduced H2 padding from 20px/10px to 5px/0")
    changes += 1

# 2. Remove empty paragraphs between H2 block and next content
# Pattern: <!-- /wp:html -->\n\n\n<p><br />\n</p>
raw = re.sub(r'(<!-- /wp:html -->)\s*<p><br\s*/?\s*>\s*</p>', r'\1', raw)
print("Removed empty <p><br></p> spacers")
changes += 1

# 3. Check and reduce logo container margins
# The logo is in: <figure class="aligncenter size-full is-resized">
# Find the wp:group containing the logo and reduce padding
logo_idx = raw.find('Industrial-PolySaas-Cropped')
if logo_idx > 0:
    # Look for the containing group block
    before_logo = raw[max(0, logo_idx-500):logo_idx]
    print(f"\nBefore logo (last 300 chars): {before_logo[-300:]}")
    
    # Find wp-block-group padding before the logo
    group_match = re.search(r'(wp-block-group[^"]*)"[^>]*style="([^"]*)"', before_logo)
    if group_match:
        print(f"Group style: {group_match.group(2)}")

# 4. Also add homepage-specific CSS to further reduce gaps
# Find the aggressive padding CSS block and add homepage-specific rules
old_css_end = '/* Aggressive top whitespace reduction */'
homepage_extra = '''/* Homepage-specific gap reduction */
.home .wp-block-group { margin-top: 0 !important; padding-top: 0 !important; }
.home .wp-block-image { margin-top: 0 !important; margin-bottom: 10px !important; }
.home .aligncenter { margin-top: 0 !important; }
.home figure.aligncenter { margin-top: 0 !important; margin-bottom: 10px !important; }
.home .entry-content > * { margin-top: 0 !important; }
.home .entry-content > *:first-child { margin-top: 0 !important; padding-top: 0 !important; }
'''
if old_css_end in raw and 'Homepage-specific gap reduction' not in raw:
    raw = raw.replace(old_css_end, old_css_end + '\n' + homepage_extra)
    print("Added homepage-specific gap CSS")
    changes += 1

if changes > 0:
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{home['id']}", json={"content": raw})
    print(f"\nUpdate homepage: {r.status_code}")
else:
    print("No changes needed")
