"""Check About Us page for content below the footer and clean it up."""
import requests, json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get About Us page
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit", timeout=30)
pages = r.json()
if not pages:
    r = s.get(f"{AZURE}/wp-json/wp/v2/pages?search=About+Us&context=edit", timeout=30)
    pages = r.json()

if not pages:
    print("ERROR: Could not find About Us page")
    sys.exit(1)

page = pages[0]
page_id = page['id']
content = page['content']['raw']
print(f"Page ID: {page_id}")
print(f"Content length: {len(content)} chars")

# Find the footer section - look for the CTA "Stop Managing Tools"
footer_marker = "Stop Managing Tools"
footer_idx = content.find(footer_marker)
print(f"\nFooter marker '{footer_marker}' found at index: {footer_idx}")

if footer_idx > 0:
    # Show what's around and after the footer
    # Find the wp:html block containing the footer
    # Look backwards from footer_marker to find the opening <!-- wp:html -->
    before_footer = content[:footer_idx]
    last_wp_html_open = before_footer.rfind('<!-- wp:html -->')
    print(f"Footer block starts at: {last_wp_html_open}")
    
    # Find the closing <!-- /wp:html --> after the footer content
    after_footer_start = content[last_wp_html_open:]
    
    # The footer block should end with <!-- /wp:html -->
    # But we need to find the RIGHT closing tag - the one that closes the footer
    # Count nested wp:html blocks
    pos = last_wp_html_open
    rest = content[pos:]
    
    # Find all <!-- wp:html --> and <!-- /wp:html --> tags in the rest
    open_tags = [(m.start(), 'open') for m in re.finditer(r'<!-- wp:html -->', rest)]
    close_tags = [(m.start(), 'close') for m in re.finditer(r'<!-- /wp:html -->', rest)]
    
    all_tags = sorted(open_tags + close_tags, key=lambda x: x[0])
    
    # Find the matching close for the first open
    depth = 0
    footer_end_pos = None
    for tag_pos, tag_type in all_tags:
        if tag_type == 'open':
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                footer_end_pos = pos + tag_pos + len('<!-- /wp:html -->')
                break
    
    if footer_end_pos:
        print(f"Footer block ends at: {footer_end_pos}")
        after_footer = content[footer_end_pos:].strip()
        print(f"\nContent AFTER footer ({len(after_footer)} chars):")
        print(after_footer[:2000])
        
        if after_footer:
            print(f"\n--- Removing {len(after_footer)} chars of content after footer ---")
            new_content = content[:footer_end_pos]
            
            # Update the page
            r2 = s.post(
                f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
                json={"content": new_content},
                timeout=30
            )
            print(f"Update status: {r2.status_code}")
            if r2.status_code == 200:
                print("Successfully removed content below footer!")
            else:
                print(f"Error: {r2.text[:300]}")
        else:
            print("\nNo content found after footer - page looks clean")
    else:
        print("ERROR: Could not find end of footer block")
        # Try simpler approach - find last <!-- /wp:html -->
        last_close = content.rfind('<!-- /wp:html -->')
        print(f"Last <!-- /wp:html --> at: {last_close}")
        after_last = content[last_close + len('<!-- /wp:html -->'):].strip()
        print(f"Content after last close tag ({len(after_last)} chars):")
        print(after_last[:1000])
