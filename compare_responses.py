"""
Compare what a normal browser sees from Mattermost directly
vs what our proxy fetches and serves.
"""
import requests, re, os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(__file__))

# ─── 1. Direct request — simulate what a browser would send to Mattermost ───
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

r_direct = requests.get('http://localhost:8065/', headers=BROWSER_HEADERS, timeout=15)
direct_html = r_direct.text

print("=== DIRECT REQUEST TO MATTERMOST ===")
print(f"Status : {r_direct.status_code}")
print(f"Length : {len(direct_html)} chars")
print("Response headers:")
for k, v in r_direct.headers.items():
    print(f"  {k}: {v}")

# ─── 2. What the proxy fetches ───
django.setup()
from dose.passthrough.forwarding import _outbound_headers_from_request

# Simulate what the proxy does — use same request headers
r_proxy_fetch = requests.get(
    'http://localhost:8065/',
    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,*/*', 'Accept-Encoding': 'identity'},
    timeout=15,
    allow_redirects=True,
)
proxy_raw = r_proxy_fetch.text

print("\n=== PROXY FETCHES FROM MATTERMOST ===")
print(f"Status : {r_proxy_fetch.status_code}")
print(f"Length : {len(proxy_raw)} chars")

# ─── 3. Extract and compare key parts ───
def extract_scripts(html):
    return re.findall(r'<script[^>]+src="([^"]+)"', html)

def extract_links(html):
    return re.findall(r'<link[^>]+href="([^"]+)"', html)

def extract_meta_csp(html):
    return re.findall(r'<meta[^>]+Content-Security-Policy[^>]*/?\s*>', html, re.I)

d_scripts = extract_scripts(direct_html)
p_scripts = extract_scripts(proxy_raw)

print("\n=== SCRIPT TAGS ===")
print(f"Direct ({len(d_scripts)}):")
for s in d_scripts[:8]: print(f"  {s}")
print(f"Direct last few:")
for s in d_scripts[-3:]: print(f"  {s}")

print(f"\nProxy raw ({len(p_scripts)}):")
for s in p_scripts[:8]: print(f"  {s}")

print("\n=== CSP META TAGS ===")
d_csp = extract_meta_csp(direct_html)
p_csp = extract_meta_csp(proxy_raw)
print(f"Direct: {len(d_csp)}")
for c in d_csp: print(f"  {c[:300]}")
print(f"Proxy raw: {len(p_csp)}")

# ─── 4. Apply the handler and show final proxied output ───
from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler

class FakeRequest:
    path_info = '/pt/admin/mattermost/'
    path = '/pt/admin/mattermost/'
    def build_absolute_uri(self, p): return f'http://localhost:8000{p}'
    def is_secure(self): return False
    def get_host(self): return 'localhost:8000'

class FakeTenant:
    name = 'Oliver Enterprises'
    schema_name = 'olient'

class FakeTA:
    extra_config = {'mm_token': 'test_token_123'}
    status = 'active'
    app_name = 'mattermost'

req = FakeRequest()
req.tenant = FakeTenant()

handler = MattermostPassthroughHandler()
handler._get_mm_token = lambda r: 'test_token_123'  # mock token lookup
result, _ = handler.process_html_response(proxy_raw, req, endpoint_url='http://localhost:8065')

print("\n=== AFTER HANDLER PROCESSING ===")
print(f"Length: {len(result)} chars")
f_scripts = extract_scripts(result)
print(f"Script srcs ({len(f_scripts)}):")
for s in f_scripts[:8]: print(f"  {s}")

shim_present = 'data-polysaas-mattermost-shim' in result
csp_stripped = len(extract_meta_csp(result)) == 0
token_in_shim = 'test_token_123' in result
print(f"\nShim present: {shim_present}")
print(f"CSP meta stripped: {csp_stripped}")
print(f"Token in shim: {token_in_shim}")

# Show the shim itself
shim_start = result.find('<script data-polysaas-mattermost-shim')
if shim_start != -1:
    shim_end = result.find('</script>', shim_start) + 9
    shim = result[shim_start:shim_end]
    print(f"\nShim length: {len(shim)} chars")
    print("First 400 chars of shim:")
    print(shim[:400])

# Save outputs
with open('direct_mm.html', 'w', encoding='utf-8') as f: f.write(direct_html)
with open('proxied_mm.html', 'w', encoding='utf-8') as f: f.write(result)
print("\nSaved direct_mm.html and proxied_mm.html")
