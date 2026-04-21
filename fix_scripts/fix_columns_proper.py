"""Restore 33% for app grid, fix feature columns to 50/50 centered."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1313?context=edit&_fields=content",
                 auth=AUTH, timeout=30)
content = r.json()['content']['raw']

# Find the current column rule we changed (flex: 1 1 auto)
old_rule = """.wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 auto !important;
    min-width: 200px !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}"""

# New rule: restore 33% for the app grid, add 50% override for features section
new_rule = """.wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 30% !important;
    min-width: 250px !important;
    max-width: 33% !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Feature section: 2-column cards use 50/50, centered */
#platform-features ~ .wp-block-columns.is-layout-flex {
    justify-content: center !important;
}
#platform-features ~ .wp-block-columns.is-layout-flex > .wp-block-column {
    flex: 1 1 45% !important;
    max-width: 48% !important;
    min-width: 200px !important;
}"""

if old_rule in content:
    new_content = content.replace(old_rule, new_rule)
    r2 = requests.post(
        f"{BASE}/wp-json/wp/v2/pages/1313",
        auth=AUTH,
        json={"content": new_content},
        timeout=30
    )
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Restored app grid 33%, feature columns now 50/50 centered")
else:
    print("Old rule not found. Checking what's there...")
    # Find the column rule
    pos = content.find('wp-block-column {')
    if pos > 0:
        print(f"Found at {pos}:")
        print(content[max(0,pos-200):pos+300])

    # Also try to find any style block with the column rule
    style_blocks = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
    for i, sb in enumerate(style_blocks):
        if 'wp-block-column' in sb:
            print(f"\nStyle block {i} has column rules")
            # Find the specific rule
            col_pos = sb.find('wp-block-column')
            print(sb[max(0,col_pos-100):col_pos+300])
