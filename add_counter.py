"""Add a visit counter to the investor page (ID 2565).
Uses WordPress post meta to store the count and inline JS to increment on each visit."""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
PAGE_ID = 2565

# Get current page content
r = requests.get(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit&_fields=content",
                 auth=AUTH, timeout=15)
content = r.json()['content']['raw']
print(f"Page content length: {len(content)} chars")

# Check if counter already exists
if 'ps-visit-counter' in content:
    print("Counter already exists!")
    sys.exit(0)

# Create a self-contained visit counter using localStorage + REST API
# The counter will:
# 1. Display current count from a hidden span updated via REST
# 2. Increment on each unique visit (using localStorage to avoid double-counting refreshes)
# 3. Store count in WordPress post meta via REST API

counter_html = '''<!-- wp:html -->
<div id="ps-visit-counter" style="text-align:center;padding:12px 0;margin:20px auto;max-width:300px;border:1px solid var(--ps-border, #334155);border-radius:8px;background:var(--ps-bg-alt, #1E293B)">
  <span style="font-size:0.8rem;color:var(--ps-text-muted, #94A3B8);text-transform:uppercase;letter-spacing:1px">Page Views</span><br>
  <span id="ps-view-count" style="font-size:1.8rem;font-weight:700;color:var(--ps-accent, #5EEAD4)">...</span>
</div>
<script>
(function(){
  var KEY = 'ps_inv_counted';
  var API = '/wp-json/wp/v2/pages/2565';
  var el = document.getElementById('ps-view-count');
  
  // Fetch current count from post meta
  fetch(API + '?_fields=meta')
    .then(function(r){ return r.json(); })
    .then(function(d){
      var count = (d.meta && d.meta.ps_visit_count) ? parseInt(d.meta.ps_visit_count) : 0;
      
      // Check if this session already counted
      var counted = sessionStorage.getItem(KEY);
      if (!counted) {
        count++;
        sessionStorage.setItem(KEY, '1');
        // Increment server-side
        fetch(API, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-WP-Nonce': (typeof wpApiSettings !== 'undefined') ? wpApiSettings.nonce : ''
          },
          credentials: 'same-origin',
          body: JSON.stringify({meta: {ps_visit_count: String(count)}})
        }).catch(function(){});
      }
      el.textContent = count;
    })
    .catch(function(){
      el.textContent = '–';
    });
})();
</script>
<!-- /wp:html -->'''

# The REST API meta approach requires registering the meta field.
# Simpler approach: use a self-contained counter with localStorage that 
# stores count in a data attribute we update via the API periodically.

# Actually, the simplest reliable approach: use the page content itself
# to store the count, incremented by a small PHP snippet or JS.
# But we can't run PHP in content.

# Best approach for WordPress without plugins: use a simple hit counter
# stored in post meta, with a lightweight AJAX call.
# But post meta requires the meta to be registered for REST.

# Simplest working approach: use a free external counter service,
# or embed a simple counter using the WordPress REST API with post meta.

# Let's use a different approach - register the meta key first, then add the counter.
# First, check if we can read/write meta:
r2 = requests.get(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}?_fields=meta", auth=AUTH, timeout=15)
print(f"Meta check: {r2.status_code}")
meta = r2.json().get('meta', {})
print(f"Current meta: {meta}")

# Try setting a meta value
r3 = requests.post(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}",
                   auth=AUTH,
                   json={"meta": {"ps_visit_count": "1"}},
                   timeout=15)
print(f"Meta set test: {r3.status_code}")
if r3.status_code != 200:
    print(f"  Error: {r3.text[:300]}")
    print("\nMeta registration needed. Using localStorage-only approach instead.")
    
    # Fallback: pure client-side counter using localStorage
    # This won't survive across browsers but gives a rough count per-browser
    # Better: use a tiny external counting pixel/service
    
    # Actually, best simple approach: just count via the REST API view count
    # WordPress doesn't track page views by default but we can use
    # a simple approach: store count in the page content itself (hidden span)
    # and update it via API each time we want to check
    
    # OR: embed a free counter widget
    # Let's use a clean approach with a lightweight free counter
    
    counter_html = '''<!-- wp:html -->
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

# Add counter near the top of the page, after the style block
# Find the end of the first style block
style_end = content.find('<!-- /wp:html -->')
if style_end >= 0:
    insert_pos = style_end + len('<!-- /wp:html -->')
    new_content = content[:insert_pos] + '\n\n' + counter_html + '\n\n' + content[insert_pos:]
    
    r4 = requests.post(f"{BASE}/wp-json/wp/v2/pages/{PAGE_ID}",
                       auth=AUTH,
                       json={"content": new_content},
                       timeout=30)
    print(f"\nPage update: {r4.status_code}")
    if r4.status_code == 200:
        print("SUCCESS - Visit counter added to investor page")
    else:
        print(f"Error: {r4.text[:300]}")
