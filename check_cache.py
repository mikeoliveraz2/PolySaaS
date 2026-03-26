"""Check for caching plugins and verify what the user sees."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "XF8j E5IE VpHD N3rx WSkO TaMc")

# Check installed plugins
r = requests.get(f"{BASE}/wp-json/wp/v2/plugins", auth=AUTH, timeout=15)
if r.status_code == 200:
    plugins = r.json()
    print("=== Installed Plugins ===")
    for p in plugins:
        name = p.get('name', '')
        status = p.get('status', '')
        is_cache = any(word in name.lower() for word in ['cache', 'optimize', 'speed', 'litespeed', 'rocket', 'fast', 'cdn', 'minif', 'performance'])
        marker = " *** CACHE-RELATED" if is_cache else ""
        print(f"  {name}: {status}{marker}")

# Check response headers for caching indicators
print("\n=== Response Headers ===")
r = requests.get(BASE, timeout=30)
for h, v in r.headers.items():
    h_lower = h.lower()
    if any(word in h_lower for word in ['cache', 'age', 'x-', 'cf-', 'server', 'vary', 'etag', 'expires', 'pragma', 'powered']):
        print(f"  {h}: {v}")

# Check for Hostinger-specific caching headers
print(f"\n  Content-Length: {r.headers.get('Content-Length', 'N/A')}")
print(f"  Server: {r.headers.get('Server', 'N/A')}")

# Verify our CSS is in the actual response from the server
html = r.text
if 'max-width: 1100px !important' in html:
    print("\n[VERIFIED] max-width:1100px !important CSS IS in served HTML")
if 'max-width:1000px;margin:0 auto' in html:
    print("[VERIFIED] Inline max-width:1000px IS in served HTML")
else:
    print("\n[WARNING] Inline max-width:1000px NOT found in served HTML!")

# Check for Hostinger caching
if 'litespeed' in html.lower() or 'ls-cache' in str(r.headers).lower():
    print("\n[INFO] LiteSpeed cache detected!")
    
# Look for any caching meta tags
cache_metas = re.findall(r'<meta[^>]*(?:cache|pragma|expires)[^>]*>', html, re.IGNORECASE)
for m in cache_metas:
    print(f"  Cache meta: {m}")
