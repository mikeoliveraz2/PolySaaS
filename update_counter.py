"""Update the investor page counter to use Post Views Counter plugin data."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
PAGE_ID = 2565

# Check if PVC exposes view count in the REST API
r = requests.get(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}?_fields=id,title,meta,post_views",
                 auth=AUTH, timeout=15)
data = r.json()
print(f"Page data keys: {list(data.keys())}")
if 'post_views' in data:
    print(f"Post views: {data['post_views']}")

# Check the plugin's REST endpoints
r2 = requests.get(f"{BASE}/wp-json/", auth=AUTH, timeout=15)
routes = r2.json().get('routes', {})
pvc_routes = [rt for rt in routes if 'view' in rt.lower() or 'pvc' in rt.lower()]
print(f"\nPVC-related routes: {pvc_routes}")

# Get page content to update the counter widget
r3 = requests.get(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit&_fields=content",
                  auth=AUTH, timeout=15)
content = r3.json()['content']['raw']

# The Post Views Counter plugin automatically counts views when a page is loaded.
# It stores counts in its own table and provides shortcodes:
# [post-views] - displays the view count for the current post
# Let's replace our localStorage counter with the plugin's shortcode

old_counter = '''<!-- wp:html -->
<div id="ps-visit-counter" style="text-align:center;padding:14px 20px;margin:20px auto;max-width:280px;border:1px solid var(--ps-border, #334155);border-radius:8px;background:var(--ps-bg-alt, #1E293B)">
  <span style="font-size:0.75rem;color:var(--ps-text-muted, #94A3B8);text-transform:uppercase;letter-spacing:1.5px">Page Views</span><br>
  <span id="ps-view-count" style="font-size:2rem;font-weight:700;color:var(--ps-accent, #5EEAD4)">0</span>
</div>
<script>
(function(){
  var STORE_KEY = "ps_inv_views";
  var SESSION_KEY = "ps_inv_session";
  var el = document.getElementById("ps-view-count");
  
  // Get count from localStorage
  var count = parseInt(localStorage.getItem(STORE_KEY) || "0");
  
  // Increment if new session
  if (!sessionStorage.getItem(SESSION_KEY)) {
    count++;
    sessionStorage.setItem(SESSION_KEY, "1");
    localStorage.setItem(STORE_KEY, String(count));
  }
  
  el.textContent = count;
})();
</script>
<!-- /wp:html -->'''

new_counter = '''<!-- wp:html -->
<div style="text-align:center;padding:14px 20px;margin:20px auto;max-width:280px;border:1px solid var(--ps-border, #334155);border-radius:8px;background:var(--ps-bg-alt, #1E293B)">
  <span style="font-size:0.75rem;color:var(--ps-text-muted, #94A3B8);text-transform:uppercase;letter-spacing:1.5px">Page Views</span><br>
  <span style="font-size:2rem;font-weight:700;color:var(--ps-accent, #5EEAD4)">[post-views]</span>
</div>
<!-- /wp:html -->'''

if old_counter in content:
    new_content = content.replace(old_counter, new_counter)
    r4 = requests.post(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}",
                       auth=AUTH,
                       json={"content": new_content},
                       timeout=30)
    print(f"\nUpdate: {r4.status_code}")
    if r4.status_code == 200:
        print("SUCCESS - Counter now uses Post Views Counter plugin (server-side)")
        print("Every unique visitor will be counted across all browsers/devices")
else:
    print("Old counter block not found - checking...")
    if 'ps-visit-counter' in content:
        print("Counter IS in content but exact match failed")
        # Show what's there
        pos = content.find('ps-visit-counter')
        print(content[max(0,pos-50):pos+200])
    else:
        print("No counter found in content at all")
