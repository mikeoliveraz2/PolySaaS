"""Replace the localStorage counter with Post Views Counter shortcode."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
PAGE_ID = 2565

r = requests.get(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit&_fields=content",
                 auth=AUTH, timeout=45)
content = r.json()['content']['raw']

# Find the counter block using regex - from <!-- wp:html --> containing ps-visit-counter to <!-- /wp:html -->
pattern = r'<!-- wp:html -->\s*<div id="ps-visit-counter".*?</script>\s*<!-- /wp:html -->'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_block = match.group(0)
    print(f"Found counter block ({len(old_block)} chars)")
    
    new_block = '''<!-- wp:html -->
<div style="text-align:center;padding:14px 20px;margin:20px auto;max-width:280px;border:1px solid var(--ps-border, #334155);border-radius:8px;background:var(--ps-bg-alt, #1E293B)">
  <span style="font-size:0.75rem;color:var(--ps-text-muted, #94A3B8);text-transform:uppercase;letter-spacing:1.5px">Page Views</span><br>
  <span style="font-size:2rem;font-weight:700;color:var(--ps-accent, #5EEAD4)">[post-views]</span>
</div>
<!-- /wp:html -->'''
    
    new_content = content.replace(old_block, new_block)
    
    r2 = requests.post(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}",
                       auth=AUTH,
                       json={"content": new_content},
                       timeout=30)
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Counter now uses server-side Post Views Counter plugin")
        print("Tracks ALL visitors across all devices/browsers")
else:
    print("Counter block not found with regex!")
    # Show area around ps-visit-counter
    pos = content.find('ps-visit-counter')
    if pos >= 0:
        print(f"\nActual content around counter:")
        print(content[max(0,pos-100):pos+800])
