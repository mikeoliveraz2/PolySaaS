"""Fix feature block centering on wide screens.
The wp-block-columns rows need to be centered within the content area.
Use the page's style block to force centering with high specificity.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "home", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']
print(f"Page ID: {page_id}, length: {len(raw)} chars")

# Remove the wrapper div - it's not working because WP's layout system ignores it
if 'ps-features-centered' in raw:
    raw = raw.replace(
        '<div class="ps-features-centered" style="max-width:900px;margin:0 auto;padding:0 20px;">',
        ''
    )
    # Find and remove the closing </div> that corresponds to our wrapper
    # It should be right before the footer section or at end of content
    # Find it by searching for </div> before "Stop Managing Tools"
    footer_idx = raw.find('Stop Managing Tools')
    if footer_idx > 0:
        # The closing </div> for our wrapper should be right before the footer
        search_area = raw[footer_idx-100:footer_idx]
        close_idx = search_area.rfind('</div>')
        if close_idx >= 0:
            abs_idx = footer_idx - 100 + close_idx
            raw = raw[:abs_idx] + raw[abs_idx+6:]
            print("  Removed wrapper div and closing tag")
    print("  Removed wrapper div")

# The real fix: add CSS to the page style block that centers the wp-block-columns
# Using !important with the actual WordPress-generated class names
CENTER_CSS = '''
/* Center Platform Features rows on wide screens */
.wp-block-columns.are-vertically-aligned-center {
    max-width: 1100px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
.entry-content > .wp-block-columns,
.entry-content-wrap .wp-block-columns {
    max-width: 1100px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''

# Remove any old centering CSS attempts
for old_comment in ['Center Platform Features rows', 'Center Platform Features']:
    while old_comment in raw:
        # Find the comment and remove the entire CSS block
        comment_idx = raw.find(old_comment)
        if comment_idx < 0:
            break
        block_start = raw.rfind('/*', max(0, comment_idx - 10), comment_idx)
        if block_start < 0:
            break
        block_end = raw.find('}', comment_idx)
        if block_end < 0:
            break
        # Find the last } in the rule block
        next_comment = raw.find('/*', block_end)
        next_style_end = raw.find('</style>', block_end)
        end = min(
            next_comment if next_comment > 0 else len(raw),
            next_style_end if next_style_end > 0 else len(raw)
        )
        # Find last } before end
        last_brace = raw.rfind('}', block_end, end)
        if last_brace > block_end:
            raw = raw[:block_start] + raw[last_brace+1:]
        else:
            raw = raw[:block_start] + raw[block_end+1:]
        print(f"  Removed old CSS block containing '{old_comment}'")

# Add new CSS
style_end = raw.find('</style>')
if style_end > 0:
    raw = raw[:style_end] + CENTER_CSS + raw[style_end:]
    print("  Added centering CSS")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS!")
else:
    print(f"  ERROR: {r2.text[:500]}")
