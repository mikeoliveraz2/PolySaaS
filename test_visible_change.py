"""Make a very obvious visual change to the features section to diagnose the issue."""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get current page content
r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1313?context=edit", auth=AUTH, timeout=15)
print(f"GET status: {r.status_code}")
page = r.json()
print(f"Keys: {list(page.keys())[:10]}")

if 'content' in page:
    content = page['content']
    if isinstance(content, dict):
        raw = content.get('raw', content.get('rendered', ''))
    else:
        raw = content
elif 'raw' in page:
    raw = page['raw']
else:
    # Might have different structure - let's inspect
    print(f"Page structure (first 500): {json.dumps(page, indent=2)[:500]}")
    sys.exit(1)

print(f"Content length: {len(raw)}")

# Find our wrapper div
old_wrapper = '<div class="wp-block-group" style="max-width:1000px;margin:0 auto;padding-top:10px;padding-bottom:12px">'
if old_wrapper in raw:
    new_wrapper = '<div class="wp-block-group" style="max-width:700px;margin:0 auto;padding-top:10px;padding-bottom:12px;background:red;border:5px solid yellow">'
    new_content = raw.replace(old_wrapper, new_wrapper)
    r2 = requests.post(
        f"{BASE}/wp-json/wp/v2/pages/1313",
        auth=AUTH,
        json={"content": new_content},
        timeout=30
    )
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Added red background + yellow border + 700px width")
else:
    print(f"Wrapper not found. Searching for 'platform-features'...")
    pf_pos = raw.find('platform-features')
    if pf_pos > 0:
        start = max(0, pf_pos - 500)
        print(raw[start:pf_pos+100])
    else:
        pf_pos = raw.find('Platform Features')
        if pf_pos > 0:
            start = max(0, pf_pos - 500)
            print(raw[start:pf_pos+100])
        else:
            print("'Platform Features' not found anywhere in content!")
