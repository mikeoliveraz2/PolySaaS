"""Extract standard footer from About Us and add to all pages missing it."""
import requests, sys, re, time
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Step 1: Extract the footer from About Us
print("Extracting footer from About Us...")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
about = r.json()[0]
about_content = about['content']['raw']

# The footer starts with the "Stop Managing Tools" heading area
# Find the footer block — it starts with the CTA + contact info section
footer_marker = 'Stop Managing Tools'
footer_idx = about_content.find(footer_marker)
if footer_idx < 0:
    print("ERROR: Cannot find footer marker in About Us!")
    sys.exit(1)

# Go back to find the wp:html block start before the footer
block_start = about_content.rfind('<!-- wp:html -->', 0, footer_idx)
# The footer ends before the roadmap image (which is page-specific content after the footer)
# Find the roadmap image block
roadmap_idx = about_content.find('polysaas-roadmap-timeline', block_start)
if roadmap_idx > 0:
    # Footer ends at the <!-- wp:html --> before the roadmap
    footer_end_search = about_content.rfind('<!-- wp:html -->', block_start + 1, roadmap_idx)
    if footer_end_search > block_start:
        # There's a separate block for the roadmap — footer is between block_start and footer_end_search
        footer_html = about_content[block_start:footer_end_search].strip()
    else:
        # Footer and roadmap might be in the same block — get just the footer part
        roadmap_div = about_content.rfind('<div style="text-align:center;margin:20px auto', block_start, roadmap_idx)
        footer_html = about_content[block_start:roadmap_div].strip()
else:
    # No roadmap — footer goes to end of content
    footer_html = about_content[block_start:].strip()

print(f"Footer HTML extracted ({len(footer_html)} chars)")
print(f"Starts with: {footer_html[:100]}...")
print(f"Ends with: ...{footer_html[-100:]}")

# Verify it has the key elements
assert 'michael.oliver@polysaas.online' in footer_html, "Missing email!"
assert 'Privacy Policy' in footer_html, "Missing privacy link!"
assert 'Applications' in footer_html or 'Liferay' in footer_html, "Missing app links!"
print("Footer validated: has contact info, privacy links, and app links.\n")

# Step 2: Get all published pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?per_page=100&status=publish&context=edit")
pages = r.json()
print(f"Total published pages: {len(pages)}")

# Step 3: Add footer to pages that don't have it
updated = 0
skipped = 0
errors = 0

for page in sorted(pages, key=lambda p: p['slug']):
    slug = page['slug']
    pid = page['id']
    content = page['content']['raw']
    
    # Skip pages that already have the footer
    if 'michael.oliver@polysaas.online' in content or '5900 Balcones' in content:
        print(f"  SKIP {slug} — already has footer")
        skipped += 1
        continue
    
    # Skip special pages that shouldn't have a footer
    if slug in ['privacy-policy', 'terms-of-service', 'disclaimer']:
        print(f"  SKIP {slug} — legal page")
        skipped += 1
        continue
    
    # Add footer to end of content
    # First, find the last <!-- /wp:html --> to insert after it
    # Or just append to the end
    new_content = content.rstrip() + "\n\n" + footer_html
    
    # Post update
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
    if r2.status_code == 200:
        print(f"  OK   {slug}")
        updated += 1
    else:
        print(f"  ERR  {slug} — {r2.status_code}: {r2.text[:100]}")
        errors += 1
    
    time.sleep(0.5)  # Be gentle with the API

print(f"\n{'='*50}")
print(f"Updated: {updated}")
print(f"Skipped: {skipped}")
print(f"Errors:  {errors}")
print(f"Total:   {updated + skipped + errors}")
