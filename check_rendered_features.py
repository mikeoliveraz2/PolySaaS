"""Check the rendered HTML to see if our Group wrapper and CSS are present."""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"

# Fetch the page as a regular visitor (no auth = rendered HTML)
r = requests.get(f"{AZURE}/", timeout=30)
html = r.text

# Check for our group wrapper around Platform Features
pf_pos = html.find('id="platform-features"')
if pf_pos > 0:
    # Look 500 chars before to see the group wrapper
    context_before = html[max(0, pf_pos-500):pf_pos]
    print("=== 500 chars BEFORE Platform Features ===")
    print(context_before[-300:])
    
    # Look 500 chars after
    context_after = html[pf_pos:pf_pos+500]
    print("\n=== 500 chars AFTER Platform Features ===")
    print(context_after[:300])

# Check if our <style> block CSS is present
if 'Feature Block Centering' in html:
    print("\n*** Centering CSS IS present in rendered HTML ***")
else:
    print("\n*** Centering CSS NOT found in rendered HTML ***")

# Check if <style> tags exist at all in the content area
style_count = html.count('<style>')
print(f"Total <style> tags in page: {style_count}")

# Check for wp-block-group around platform features
# Find the constrained layout class near platform features
search_area = html[max(0, pf_pos-1000):pf_pos+200]
if 'is-layout-constrained' in search_area:
    print("is-layout-constrained IS present near Platform Features")
    # Show the exact group div
    constrained_pos = search_area.find('is-layout-constrained')
    print(f"  Context: ...{search_area[max(0,constrained_pos-100):constrained_pos+50]}...")
else:
    print("is-layout-constrained NOT present near Platform Features")

# Check what CSS classes are on the content wrapper
content_wrap = re.findall(r'class="[^"]*entry-content[^"]*"', html)
for cw in content_wrap[:3]:
    print(f"\nContent wrapper class: {cw}")

# Check the Kadence content width setting from the rendered CSS
# Look for --global-content-width or similar
width_vars = re.findall(r'--global-content-width[^;]*;', html)
for wv in width_vars[:3]:
    print(f"Content width var: {wv}")

# Also check for max-width on the entry-content-wrap
ecw_matches = re.findall(r'entry-content-wrap[^{]*\{[^}]*\}', html)
for m in ecw_matches[:3]:
    print(f"Entry content wrap style: {m[:200]}")
