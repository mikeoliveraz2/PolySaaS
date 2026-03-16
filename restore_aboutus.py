"""Restore About Us page from its revision history - the previous fix incorrectly 
removed the main page content."""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

PAGE_ID = 1345

# Get revisions
r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}/revisions?per_page=10&context=edit", timeout=30)
print(f"Revisions status: {r.status_code}")

if r.status_code == 200:
    revisions = r.json()
    print(f"Found {len(revisions)} revisions")
    
    for i, rev in enumerate(revisions[:5]):
        rev_id = rev['id']
        rev_date = rev.get('date', 'unknown')
        content = rev.get('content', {}).get('raw', '')
        has_footer = 'Stop Managing Tools' in content
        has_about = 'About PolySaaS' in content
        print(f"\n  Rev {i}: ID={rev_id}, date={rev_date}")
        print(f"    Content length: {len(content)}")
        print(f"    Has footer: {has_footer}, Has About section: {has_about}")
    
    # Find the most recent revision that has BOTH the footer and the about content
    target_rev = None
    for rev in revisions:
        content = rev.get('content', {}).get('raw', '')
        if 'About PolySaaS' in content and 'Stop Managing Tools' in content:
            target_rev = rev
            break
    
    if target_rev:
        rev_content = target_rev['content']['raw']
        print(f"\nRestoring from revision {target_rev['id']} (date: {target_rev.get('date', '?')})")
        print(f"Content length: {len(rev_content)}")
        
        # Now find and remove content AFTER the footer properly
        # The footer is the LAST <!-- wp:html --> block containing "Stop Managing Tools"
        footer_marker = "Stop Managing Tools"
        footer_pos = rev_content.rfind(footer_marker)  # Use rfind for the LAST occurrence
        print(f"Footer marker at: {footer_pos}")
        
        # Find the <!-- wp:html --> block that contains this marker
        # Search backwards from footer_pos for <!-- wp:html -->
        search_area = rev_content[:footer_pos]
        footer_block_start = search_area.rfind('<!-- wp:html -->')
        print(f"Footer block starts at: {footer_block_start}")
        
        # Now find the LAST <!-- /wp:html --> in the entire content
        # The footer block should be the very last block on the page
        last_close = rev_content.rfind('<!-- /wp:html -->')
        footer_block_end = last_close + len('<!-- /wp:html -->')
        print(f"Footer block ends at: {footer_block_end}")
        
        after_footer = rev_content[footer_block_end:].strip()
        print(f"Content after footer: '{after_footer[:200]}'")
        print(f"After footer length: {len(after_footer)}")
        
        if after_footer:
            # Remove content after the footer
            new_content = rev_content[:footer_block_end]
            print(f"\nRemoving {len(after_footer)} chars after footer")
        else:
            # Content is already clean, just restore as-is
            new_content = rev_content
            print("\nNo extra content after footer, restoring as-is")
        
        # Update the page
        r2 = s.post(
            f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}",
            json={"content": new_content},
            timeout=30
        )
        print(f"Update status: {r2.status_code}")
        if r2.status_code == 200:
            print(f"Page restored! New content length: {len(new_content)}")
        else:
            print(f"Error: {r2.text[:300]}")
    else:
        print("\nERROR: Could not find a good revision to restore from!")
        print("Showing available revisions:")
        for rev in revisions[:5]:
            content = rev.get('content', {}).get('raw', '')
            print(f"  Rev {rev['id']}: {len(content)} chars, About={('About PolySaaS' in content)}, Footer={('Stop Managing Tools' in content)}")
