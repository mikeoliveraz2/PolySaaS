"""Add inline max-width and margin:auto to the Group wrapper around
Platform Features, so the container itself is constrained and centered.
"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

HOME_PAGE_ID = 1313

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
          params={"context": "edit", "_fields": "content"},
          timeout=30)
content = r.json()['content']['raw']

# Find the group wrapper we added right before Platform Features
# Current: <div class="wp-block-group" style="padding-top:10px;padding-bottom:12px">
# followed by: <div class="wp-block-group__inner-container is-layout-constrained...">
# followed by: <h2 ... id="platform-features">

# We need to find the SPECIFIC group that wraps platform features
# Look for the inner-container div just before platform-features
old_inner = '<div class="wp-block-group__inner-container is-layout-constrained wp-block-group-is-layout-constrained">\n<h2 class="wp-block-heading has-text-align-center has-primary-color has-text-color" style="margin-bottom:18px;font-size:1.6rem;font-weight:600" id="platform-features">'

if old_inner not in content:
    # Try without the newline
    old_inner = '<div class="wp-block-group__inner-container is-layout-constrained wp-block-group-is-layout-constrained">\n<h2 class="wp-block-heading has-text-align-center has-primary-color has-text-color" style="margin-bottom:18px;font-size:1.6rem;font-weight:600" id="platform-features">'
    
if old_inner not in content:
    print("Looking for the group wrapper pattern...")
    # Find the position of platform-features heading
    pf_pos = content.find('id="platform-features"')
    if pf_pos > 0:
        # Show context
        print(f"Found at pos {pf_pos}")
        print(f"Context: ...{content[max(0,pf_pos-300):pf_pos+50]}...")
    sys.exit(1)

# Replace the outer group div to add inline centering
old_outer = '<div class="wp-block-group" style="padding-top:10px;padding-bottom:12px">\n<div class="wp-block-group__inner-container is-layout-constrained wp-block-group-is-layout-constrained">\n<h2 class="wp-block-heading has-text-align-center has-primary-color has-text-color" style="margin-bottom:18px;font-size:1.6rem;font-weight:600" id="platform-features">'

# Count occurrences of the outer group pattern
# The "Eight Enterprise-Grade Applications" section uses the same pattern
# We need to be specific

# Let's do a targeted replacement - find the group div that contains platform-features
pf_pos = content.find('id="platform-features"')
# Walk backwards to find the group divs
before_pf = content[:pf_pos]
inner_pos = before_pf.rfind('wp-block-group__inner-container')
outer_start = before_pf.rfind('<div class="wp-block-group"', 0, inner_pos)

print(f"Platform Features at: {pf_pos}")
print(f"Inner container at: {inner_pos}")
print(f"Outer group starts at: {outer_start}")

# Get the outer div tag
outer_end = content.find('>', outer_start) + 1
outer_tag = content[outer_start:outer_end]
print(f"Outer tag: {outer_tag}")

# Replace with centered version
new_outer_tag = '<div class="wp-block-group" style="max-width:1000px;margin:0 auto;padding-top:10px;padding-bottom:12px">'

# Also update the inner container to not constrain (let the outer do it)
inner_end = content.find('>', inner_pos) + 1
inner_tag = content[content.find('<div', inner_pos):inner_end]
# Actually let's keep the inner but make it simpler
new_inner_tag = '<div class="wp-block-group__inner-container">'

inner_tag_start = before_pf.rfind('<div class="wp-block-group__inner-container')
inner_tag_end = content.find('>', inner_tag_start) + 1
actual_inner_tag = content[inner_tag_start:inner_tag_end]
print(f"Inner tag: {actual_inner_tag}")

new_content = content[:outer_start] + new_outer_tag + content[outer_end:inner_tag_start] + new_inner_tag + content[inner_tag_end:]

print(f"\nOld length: {len(content)}")
print(f"New length: {len(new_content)}")

# Verify
pf_check = new_content.find('id="platform-features"')
check_before = new_content[max(0,pf_check-400):pf_check]
print(f"\nNew context before Platform Features:\n{check_before[-300:]}")

# Update
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
            json={"content": new_content}, timeout=30)
print(f"\nUpdate: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS: Added max-width:1000px and margin:0 auto to features wrapper")
else:
    print(f"ERROR: {r2.text[:300]}")
