"""
Fix About Us page spacing to match Homepage.

The "About Us" H2 is inside a wp-block-group that creates the grey title band.
Remove the H2, the wrapping group divs, and the stale hero comment.
Also clean up leftover hero-kill CSS from previous failed attempts.
"""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

s = requests.Session()
s.auth = (USER, PASS)

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
pages = r.json()
page = pages[0]
pid = page['id']
content = page['content']['raw']
print(f"Page ID: {pid}, Content length: {len(content)}")

# Step 1: Remove the hero-kill CSS block (from previous failed fix)
hero_kill_start = content.find('/* Kill the Kadence page title hero section completely */')
if hero_kill_start >= 0:
    hero_kill_end = content.find('#inner-wrap {', hero_kill_start)
    if hero_kill_end >= 0:
        # Find the closing brace after #inner-wrap rule
        closing = content.find('}', hero_kill_end)
        if closing >= 0:
            next_closing = content.find('}', closing + 1)
            # Find end of the block - look for next non-whitespace/comment
            end_search = content[closing:]
            # Find the end: after the last } in this CSS section
            block_end = content.find('\n}', hero_kill_start)
            # Simpler approach: remove from "/* Kill" to just before the next real CSS comment or </style>
            # Find the boundary
            remaining = content[hero_kill_start:]
            # Find where the hero-kill CSS ends - it ends with the #inner-wrap closing brace
            lines = remaining.split('\n')
            remove_lines = []
            brace_depth = 0
            for i, line in enumerate(lines):
                remove_lines.append(line)
                if '/* Kill' in line or '/* Also target' in line or '/* Remove any gap' in line:
                    continue
                if line.strip().startswith('.') or line.strip().startswith('#'):
                    continue
                if '{' in line:
                    brace_depth += line.count('{')
                if '}' in line:
                    brace_depth -= line.count('}')
                # Once we hit a line that doesn't belong to the kill CSS, stop
                if line.strip() == '' and i > 2:
                    # Check if next line starts a new section
                    if i + 1 < len(lines) and not lines[i+1].strip().startswith('.') and not lines[i+1].strip().startswith('#') and '/*' not in lines[i+1]:
                        break
            
            kill_text = '\n'.join(remove_lines)
            print(f"Removing hero-kill CSS ({len(kill_text)} chars)")
    # Simpler: just regex remove the whole block
    pattern = r'/\* Kill the Kadence page title hero section completely \*/.*?/\* Remove any gap between header and content \*/.*?padding-top: 0 !important;\s*\}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        kill_css = match.group()
        print(f"Hero-kill CSS found: {len(kill_css)} chars")
        content = content.replace(kill_css, '')
        print("Removed hero-kill CSS")
    else:
        print("Could not match hero-kill CSS pattern cleanly, trying broader approach")
        # Just remove line by line from "/* Kill" to the end of that section
        start_idx = content.find('/* Kill the Kadence page title hero')
        if start_idx >= 0:
            # Find the next real comment or non-hero CSS
            end_idx = start_idx
            depth = 0
            i = start_idx
            while i < len(content):
                if content[i:i+2] == '/*' and 'Kill' not in content[i:i+50] and 'Also target' not in content[i:i+50] and 'Remove any gap' not in content[i:i+50]:
                    break
                if content[i:i+8] == '</style>':
                    break
                i += 1
            end_idx = i
            removed = content[start_idx:end_idx]
            print(f"Removing {len(removed)} chars of hero-kill CSS")
            content = content[:start_idx] + content[end_idx:]

# Step 2: Remove the "About Us" H2 title and its wrapping group
# The structure is:
# <p><!-- Hero Section --></p>
# <div class="wp-block-group" style="padding-top:10px;padding-bottom:10px">
# <div class="wp-block-group__inner-container">
# <h2 ...>About Us</h2>
# <!-- wp:html -->
# <div ...><img .../></div>
# ...

# Remove the <!-- Hero Section --> comment
content = re.sub(r'<p>\s*<!--\s*Hero Section\s*-->\s*</p>\s*', '', content)

# Remove the opening group divs
content = re.sub(
    r'<div class="wp-block-group"[^>]*style="padding-top:10px;padding-bottom:10px"[^>]*>\s*'
    r'<div class="wp-block-group__inner-container">\s*',
    '',
    content
)

# Remove the About Us H2
content = re.sub(
    r'<h2[^>]*>\s*About Us\s*</h2>\s*',
    '',
    content
)

# Now we need to find and remove the closing </div></div> for the group
# These should be near the end of the content (after the main content, before footer/CTA)
# Let's find the closing pattern. The wp-block-group ends somewhere.
# Since we removed the opening divs, we need to remove matching closing divs.
# Look for </div>\n</div> patterns that were the group closings.

# Actually, let's be smarter. The group probably wraps most of the page content.
# Let me find where it closes by looking for the pattern near the bottom.

# Find orphaned closing divs - look for </div></div> that close the group
# These would be right before the closing <!-- /wp:html --> or at the very end
end_divs = content.rfind('</div>\n</div>')
if end_divs >= 0:
    # Check what's around it
    ctx = content[max(0,end_divs-100):end_divs+50]
    print(f"\nFound closing divs near end at {end_divs}:")
    print(f"Context: ...{ctx}...")

# Let me count opening vs closing divs to verify balance
open_divs = len(re.findall(r'<div[ >]', content))
close_divs = len(re.findall(r'</div>', content))
print(f"\nDiv balance: {open_divs} opens, {close_divs} closes, diff={close_divs - open_divs}")

# If there are 2 extra closing divs (from the group we removed), remove them
if close_divs - open_divs == 2:
    # Remove the last two orphaned </div> tags
    # Find the last </div></div> pair
    pos = content.rfind('</div>')
    if pos >= 0:
        content = content[:pos] + content[pos+6:]
        pos = content.rfind('</div>')
        if pos >= 0:
            content = content[:pos] + content[pos+6:]
            print("Removed 2 orphaned closing </div> tags")
elif close_divs - open_divs > 0:
    diff = close_divs - open_divs
    for _ in range(diff):
        pos = content.rfind('</div>')
        if pos >= 0:
            content = content[:pos] + content[pos+6:]
    print(f"Removed {diff} orphaned closing </div> tags")
else:
    print("Divs are balanced - no orphans to remove")

# Step 3: Also reduce the padding on the logo section to bring content closer to header
# The logo div has padding:20px 0 10px 0 — reduce it
content = content.replace(
    'style="text-align:center;padding:20px 0 10px 0;"',
    'style="text-align:center;padding:5px 0 5px 0;"'
)

# Step 4: Also reduce the top padding on the About PolySaaS H1
content = content.replace(
    'style="font-size:2.2rem;font-weight:700;color:#2563EB !important;margin-bottom:8px"',
    'style="font-size:2.2rem;font-weight:700;color:#2563EB !important;margin-bottom:8px;margin-top:0;padding-top:0"'
)

print(f"\nFinal content length: {len(content)}")

# Verify no About Us H2 remains
if re.search(r'<h2[^>]*>\s*About Us\s*</h2>', content):
    print("WARNING: About Us H2 still present!")
else:
    print("About Us H2 successfully removed")

# Show what the content starts with after the style block
style_end = content.find('</style>')
if style_end >= 0:
    after_style = content[style_end:style_end+500]
    print(f"\nAfter </style>:\n{after_style[:400]}")

# Update the page
print("\nUpdating page...")
r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}",
    json={"content": content})
print(f"Update: {r.status_code}")
if r.status_code != 200:
    print(f"Error: {r.text[:500]}")
else:
    print("Done! About Us page should now match homepage spacing.")
