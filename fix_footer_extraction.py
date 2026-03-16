"""Fix: the footer extraction grabbed the entire About Us content. 
Extract ONLY the real footer (from 'Stop Managing Tools' CTA onward) and re-apply."""
import requests, sys, re, time
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Step 1: Extract ONLY the footer from About Us
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
about_content = r.json()[0]['content']['raw']

# The actual footer starts at the "Stop Managing Tools" CTA
# Find it and take from there to the end of the footer (before the roadmap image)
cta_idx = about_content.find('Stop Managing Tools')
if cta_idx < 0:
    print("ERROR: Can't find 'Stop Managing Tools'")
    sys.exit(1)

# Go back to the <h3 that contains "Stop Managing Tools"
h3_start = about_content.rfind('<h3', 0, cta_idx)
# But we need to wrap it in <!-- wp:html --> 
# The footer section is:
#   <h3>Stop Managing Tools...</h3>
#   <p>Join enterprises...</p>
#   <div>Sign Up for a Demo button</div>
#   <div>Contact info + links grid</div>
#   <div>Copyright bar</div>

# Find end of footer (before roadmap or end of content)
roadmap_idx = about_content.find('polysaas-roadmap-timeline', h3_start)
if roadmap_idx > 0:
    # Go back to the <div that starts the roadmap image block
    roadmap_div = about_content.rfind('<div', h3_start, roadmap_idx)
    # But also check if there's a <!-- wp:html --> before the roadmap
    wp_before_roadmap = about_content.rfind('<!-- wp:html -->', h3_start + 50, roadmap_idx)
    if wp_before_roadmap > h3_start:
        footer_end = wp_before_roadmap
    else:
        footer_end = roadmap_div
else:
    # Footer goes to end, minus the last <!-- /wp:html -->
    footer_end = len(about_content)

footer_html = about_content[h3_start:footer_end].strip()

# Wrap in wp:html block
footer_block = f"<!-- wp:html -->\n{footer_html}\n<!-- /wp:html -->"

print(f"Footer block: {len(footer_block)} chars")
print(f"First 200: {footer_block[:200]}")
print(f"Last 200: ...{footer_block[-200:]}")

# Verify it has footer elements but NOT About Us content
assert 'michael.oliver@polysaas.online' in footer_block, "Missing email!"
assert 'Privacy Policy' in footer_block, "Missing privacy!"  
assert 'Stop Managing Tools' in footer_block, "Missing CTA!"
assert 'Meet the Team' not in footer_block, "Contains About Us team content — BAD!"
assert 'Our Mission' not in footer_block, "Contains About Us mission — BAD!"
assert 'Board of Advisors' not in footer_block, "Contains advisors — BAD!"
print("\nFooter validated: has CTA + contact + links, NO About Us page content.")

# Step 2: Get all pages and fix them
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?per_page=100&status=publish&context=edit")
pages = r.json()

fixed = 0
skipped = 0

for page in sorted(pages, key=lambda p: p['slug']):
    slug = page['slug']
    pid = page['id']
    content = page['content']['raw']
    
    # Skip About Us and Home (they have their own footer already)
    if slug in ['about-us', 'home']:
        print(f"  SKIP {slug} — original footer")
        skipped += 1
        continue
    
    # Check if this page has the incorrectly added About Us content
    if 'About PolySaaS' in content or 'Meet the Team' in content or 'Our Mission' in content:
        # Remove everything from the wrongly-added block
        # Find where the wrong footer starts — it begins with the About Us content
        # Look for the CTA image or the "About PolySaaS" heading that shouldn't be there
        
        # The wrongly added content starts with <!-- wp:html --> followed by About Us content
        # Find the LAST occurrence of page-specific content before the wrong footer
        
        # Strategy: find "Stop Managing Tools" and go backwards to find where the 
        # wrong content was appended. The wrong content starts with a <!-- wp:html -->
        # block that contains "About PolySaaS"
        
        about_marker = content.find('About PolySaaS')
        if about_marker > 0:
            # Find the <!-- wp:html --> before this
            wrong_start = content.rfind('<!-- wp:html -->', 0, about_marker)
            if wrong_start > 0:
                # Remove everything from wrong_start to end, then add correct footer
                clean_content = content[:wrong_start].rstrip()
                new_content = clean_content + "\n\n" + footer_block
                
                r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
                if r2.status_code == 200:
                    print(f"  FIXED {slug}")
                    fixed += 1
                else:
                    print(f"  ERR   {slug} — {r2.status_code}")
            else:
                print(f"  WARN  {slug} — couldn't find wrong block start")
        else:
            print(f"  WARN  {slug} — has team content but no 'About PolySaaS' marker")
        
        time.sleep(0.5)
    elif 'michael.oliver@polysaas.online' in content:
        # Has footer but no About Us content — might be OK
        print(f"  OK    {slug} — has footer, no About Us content")
        skipped += 1
    else:
        # No footer at all — add the correct one
        new_content = content.rstrip() + "\n\n" + footer_block
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
        if r2.status_code == 200:
            print(f"  ADDED {slug}")
            fixed += 1
        else:
            print(f"  ERR   {slug} — {r2.status_code}")
        time.sleep(0.5)

print(f"\nFixed/Added: {fixed}, Skipped: {skipped}")
