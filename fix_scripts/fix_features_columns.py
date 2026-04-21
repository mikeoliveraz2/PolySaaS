"""Fix the feature columns - they're limited to 33% each by earlier CSS, 
causing them to be left-aligned instead of filling the full width."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1313?context=edit&_fields=content",
                 auth=AUTH, timeout=30)
content = r.json()['content']['raw']

# First let's see the current CSS in the style block
style_match = re.search(r'<!-- wp:html --><style>(.*?)</style><!-- /wp:html -->', content, re.DOTALL)
if style_match:
    current_css = style_match.group(1)
    print("=== Current CSS ===")
    print(current_css[:3000])
    print("=== End CSS ===\n")

# Find the problematic 33% rule and fix it
# The issue: .wp-block-columns.is-layout-flex > .wp-block-column has max-width:33%
# This works for the 8-app grid but breaks the 2-column feature cards
# Solution: Add a rule that overrides this for columns within the platform-features wrapper

# Check if there's already a rule about wp-block-column max-width
if 'max-width: 33%' in content or 'max-width:33%' in content:
    print("Found 33% max-width rule in content")

# The fix: modify the CSS to exclude the features section from the 33% rule,
# or add a specific override for feature columns
old_css = style_match.group(1) if style_match else None

if old_css and 'max-width: 33%' in old_css:
    # Add override CSS for the features section
    override_css = """

/* Feature cards: allow columns to use full width (50%/50%) */
.wp-block-group:has(#platform-features) .wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 45% !important;
    max-width: 50% !important;
    min-width: 200px !important;
}
.wp-block-group:has(#platform-features) .wp-block-columns.is-layout-flex {
    justify-content: center !important;
    max-width: 100% !important;
}"""
    
    new_css = old_css + override_css
    new_content = content.replace(old_css, new_css)
    
    r2 = requests.post(
        f"{BASE}/wp-json/wp/v2/pages/1313",
        auth=AUTH,
        json={"content": new_content},
        timeout=30
    )
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Feature columns now 50%/50% and centered")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("33% rule not found in style block. Let me check the full content...")
    # Maybe it's elsewhere - check
    positions = []
    for pattern in ['max-width: 33%', 'max-width:33%', 'max-width: 33']:
        pos = content.find(pattern)
        if pos >= 0:
            positions.append((pattern, pos))
            print(f"  Found '{pattern}' at position {pos}")
            print(f"  Context: ...{content[max(0,pos-100):pos+100]}...")
    
    if not positions:
        print("  33% rule NOT in page content at all!")
        print("  It must be in a linked stylesheet from the theme")
        # In this case, add override CSS to the style block
        if style_match:
            override = """

/* Feature cards: center columns properly */
.wp-block-group:has(#platform-features) .wp-block-columns.is-layout-flex {
    justify-content: center !important;
    width: 100% !important;
}
.wp-block-group:has(#platform-features) .wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 45% !important;
    max-width: 50% !important;
}"""
            new_css = old_css + override
            new_content = content.replace(old_css, new_css)
            r2 = requests.post(
                f"{BASE}/wp-json/wp/v2/pages/1313",
                auth=AUTH,
                json={"content": new_content},
                timeout=30
            )
            print(f"Update with override: {r2.status_code}")
