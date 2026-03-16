"""Audit every page for standard footer presence and unclosed HTML tags."""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get all published pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?per_page=100&status=publish&context=edit")
pages = r.json()
print(f"Total published pages: {len(pages)}\n")

# For each page, check the rendered HTML for footer widgets
print(f"{'Page':<30} {'Divs':>6} {'Footer?':>8}  Notes")
print("-" * 85)

for page in sorted(pages, key=lambda p: p['slug']):
    slug = page['slug']
    content = page['content']['raw']
    
    # Count div balance
    open_divs = len(re.findall(r'<div[\s>]', content))
    close_divs = len(re.findall(r'</div>', content))
    div_diff = open_divs - close_divs
    
    # Check other tag mismatches
    mismatches = []
    for tag in ['div', 'style', 'a', 'span']:
        opens = len(re.findall(f'<{tag}[\\s>]', content))
        closes = len(re.findall(f'</{tag}>', content))
        if opens != closes:
            mismatches.append(f"{tag}:{opens-closes:+d}")
    
    # Fetch the actual rendered page to check for footer widgets
    try:
        r2 = requests.get(f"{AZURE}/{slug}/", timeout=15)
        html = r2.text
        has_footer_widgets = 'footer-widget-area' in html or 'site-footer-upper' in html or 'footer-row' in html
        has_contact = 'michael.oliver@polysaas.online' in html or '5900 Balcones' in html
        has_privacy = 'Privacy Policy' in html
        
        if has_contact and has_privacy:
            footer_status = "FULL"
        elif has_privacy and not has_contact:
            footer_status = "PARTIAL"
        elif not has_privacy and not has_contact:
            footer_status = "MISSING"
        else:
            footer_status = "PARTIAL"
    except Exception as e:
        footer_status = f"ERR"
        has_footer_widgets = False
    
    notes = ""
    if div_diff != 0:
        notes += f"div-balance:{div_diff:+d} "
    if mismatches:
        notes += " ".join(mismatches)
    if footer_status != "FULL":
        notes += " *** FOOTER ISSUE ***"
    
    print(f"{slug:<30} {div_diff:>+5}  {footer_status:>8}  {notes}")

print("\n\nLegend: FULL = contact+privacy+links, PARTIAL = some missing, MISSING = no footer widgets")
