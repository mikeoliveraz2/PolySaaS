"""Compare direct Mattermost HTML vs proxied HTML."""
import requests, re, os, django, difflib
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# 1) Direct to Mattermost
r1 = requests.get('http://localhost:8065/', timeout=10)
direct = r1.text

# 2) Through the proxy (login first)
session = requests.Session()
login_page = session.get('http://localhost:8000/admin/login/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
if csrf:
    session.post('http://localhost:8000/admin/login/', data={
        'csrfmiddlewaretoken': csrf.group(1),
        'username': 'olientAdmin',
        'password': 'Olient2026!',
        'next': '/admin/',
    }, headers={'Referer': 'http://localhost:8000/admin/login/'})

r2 = session.get('http://localhost:8000/pt/admin/mattermost/', timeout=30)
proxied = r2.text

# Save both for inspection
with open('direct_mm.html', 'w', encoding='utf-8') as f:
    f.write(direct)
with open('proxied_mm.html', 'w', encoding='utf-8') as f:
    f.write(proxied)

print(f"Direct:  {len(direct)} chars, status {r1.status_code}")
print(f"Proxied: {len(proxied)} chars, status {r2.status_code}")
print(f"\nDirect headers: Content-Security-Policy = {r1.headers.get('Content-Security-Policy', '(none)')}")
print(f"Proxied headers: Content-Security-Policy = {r2.headers.get('Content-Security-Policy', '(none)')}")

# Show first diff
d_lines = direct.splitlines(keepends=True)
p_lines = proxied.splitlines(keepends=True)

diff = list(difflib.unified_diff(d_lines[:50], p_lines[:50], fromfile='direct', tofile='proxied', n=1))
print("\n=== DIFF (first 50 lines) ===")
for line in diff[:80]:
    print(line, end='')

# Check script tags
d_scripts = re.findall(r'<script[^>]*src="([^"]*)"', direct)
p_scripts = re.findall(r'<script[^>]*src="([^"]*)"', proxied)
print(f"\n\n=== SCRIPT SRCS ===")
print(f"Direct ({len(d_scripts)}):")
for s in d_scripts[:5]:
    print(f"  {s}")
print(f"Proxied ({len(p_scripts)}):")
for s in p_scripts[:5]:
    print(f"  {s}")

# Check for shim
has_shim = 'data-polysaas-mattermost-shim' in proxied
print(f"\nShim injected: {has_shim}")

# Check for CSP meta tag
d_csp = re.findall(r'<meta[^>]*Content-Security-Policy[^>]*>', direct, re.I)
p_csp = re.findall(r'<meta[^>]*Content-Security-Policy[^>]*>', proxied, re.I)
print(f"Direct CSP meta tags: {len(d_csp)}")
print(f"Proxied CSP meta tags: {len(p_csp)}")
if d_csp:
    print(f"  Direct CSP: {d_csp[0][:200]}")
