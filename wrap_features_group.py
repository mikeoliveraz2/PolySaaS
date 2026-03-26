"""Wrap Platform Features section in a wp-block-group container.
This mimics the Bricks approach: one-column wrapper at 100% containing
two-column blocks at 50%/50%. The wp-block-group with is-layout-constrained
gives the Kadence theme a container to center within.
"""
import requests, sys, json, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

HOME_PAGE_ID = 1313

# Get current content
r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
          params={"context": "edit", "_fields": "content"},
          timeout=30)
content = r.json()['content']['raw']
lines = content.split('\n')

# Find the Platform Features heading
pf_idx = None
for i, line in enumerate(lines):
    if 'id="platform-features"' in line:
        pf_idx = i
        break

if pf_idx is None:
    print("ERROR: Could not find Platform Features heading")
    sys.exit(1)

print(f"Found 'Platform Features' heading at line {pf_idx}")

# Find the end of the features section - it ends just before the CTA banner
# Look for the "Stop Managing Tools" heading or the ps-cta-banner div
end_idx = None
for i in range(pf_idx + 1, len(lines)):
    if 'ps-cta-banner' in lines[i] or 'Stop Managing Tools' in lines[i]:
        end_idx = i
        break

if end_idx is None:
    print("ERROR: Could not find end of features section")
    sys.exit(1)

print(f"Features section ends at line {end_idx}")
print(f"Section spans {end_idx - pf_idx} lines")

# Extract the features section
features_section = '\n'.join(lines[pf_idx:end_idx])

# Check if it's already wrapped in a group
if 'wp-block-group' in lines[pf_idx - 1] if pf_idx > 0 else False:
    print("Features section already wrapped in a group block - checking...")

# Wrap in a wp-block-group with constrained layout
# This mimics: Group block (100% width, max-width constrained, centered)
#   -> Columns blocks (50%/50%)
group_open = '<div class="wp-block-group" style="padding-top:10px;padding-bottom:12px">\n<div class="wp-block-group__inner-container is-layout-constrained wp-block-group-is-layout-constrained">'
group_close = '</div>\n</div>'

wrapped_section = f'{group_open}\n{features_section}\n{group_close}'

# Replace in content
new_content = '\n'.join(lines[:pf_idx]) + '\n' + wrapped_section + '\n' + '\n'.join(lines[end_idx:])

# Verify the change
print(f"\nOriginal content length: {len(content)}")
print(f"New content length: {len(new_content)}")
print(f"Added {len(new_content) - len(content)} chars (group wrapper)")

# Preview the wrapping
preview_lines = new_content.split('\n')
for i in range(max(0, pf_idx - 2), min(len(preview_lines), pf_idx + 5)):
    print(f"  {i}: {preview_lines[i][:150]}")
print("  ...")
for i in range(end_idx - 1, min(len(preview_lines), end_idx + 5)):
    print(f"  {i}: {preview_lines[i][:150]}")

# Update the page
r2 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
    json={"content": new_content},
    timeout=30
)
print(f"\nPage update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS: Platform Features section wrapped in Group block")
else:
    print(f"ERROR: {r2.text[:300]}")
