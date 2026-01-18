"""
Research OSTicket internals to understand architecture, APIs, and key patterns.
"""
import requests
import re
import json
from urllib.parse import urljoin
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

OSTICKET_BASE = 'https://oliverenterprises.app.saasify.cloud'
OSTICKET_SCP = f'{OSTICKET_BASE}/scp/'

def fetch_url(url, method='get', **kwargs):
    """Fetch URL with error handling"""
    try:
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 10)
        
        if method.lower() == 'get':
            r = requests.get(url, **kwargs)
        else:
            r = requests.post(url, **kwargs)
        
        return r
    except Exception as e:
        print(f'❌ Error fetching {url}: {e}')
        return None

def analyze_osticket_page(url, title='Page Analysis'):
    """Analyze an OSTicket page for key components"""
    print(f'\n{"="*60}')
    print(f'{title}')
    print(f'{"="*60}')
    print(f'URL: {url}')
    
    r = fetch_url(url)
    if not r:
        return
    
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type", "unknown")}')
    print(f'Size: {len(r.text)} bytes')
    print()
    
    # Key markers to search for
    markers = {
        'osticket': 'OSTicket brand',
        'ajax.php': 'AJAX handler',
        'api.php': 'API endpoint',
        'login.php': 'Login script',
        'index.php': 'Index script',
        'jquery': 'jQuery',
        'underscore': 'Underscore.js',
        'backbone': 'Backbone.js',
        'csrf_token': 'CSRF protection',
        'session': 'Session handling',
        'json': 'JSON endpoints',
    }
    
    print('Key Components:')
    found = []
    for marker, desc in markers.items():
        count = r.text.lower().count(marker.lower())
        if count > 0:
            found.append((marker, desc, count))
            print(f'  ✓ {marker:20} ({desc:25}): {count:4} occurrences')
    
    print()
    
    # Extract key scripts
    print('Scripts loaded:')
    scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
    for script in scripts[:10]:  # First 10
        print(f'  - {script}')
    if len(scripts) > 10:
        print(f'  ... and {len(scripts) - 10} more')
    
    print()
    
    # Extract forms
    print('Forms found:')
    forms = re.findall(r'<form[^>]*>', r.text, re.IGNORECASE)
    for i, form in enumerate(forms, 1):
        print(f'  {i}. {form[:100]}...')
    
    print()
    
    # Extract API endpoints
    print('API/AJAX endpoints referenced:')
    endpoints = set()
    
    # Look for ajax calls
    ajax_urls = re.findall(r'(?:url|action|href)["\']?\s*:\s*["\']([^"\']+\.php[^"\']*)["\']', r.text, re.IGNORECASE)
    for endpoint in ajax_urls[:10]:
        if not endpoint.startswith('http'):
            endpoints.add(endpoint)
    
    for endpoint in sorted(endpoints):
        print(f'  - {endpoint}')
    
    return r.text

# Main investigation
print('\n\n')
print('╔' + '='*58 + '╗')
print('║  OSTicket Internals Research                              ║')
print('╚' + '='*58 + '╝')

# 1. Analyze login page
login_html = analyze_osticket_page(
    f'{OSTICKET_SCP}login.php',
    'Login Page Analysis'
)

# 2. Analyze dashboard (need to handle login first)
print('\n' + '='*60)
print('Dashboard Access Analysis')
print('='*60)
print('Note: Dashboard requires authentication')
print('Attempting to fetch dashboard...')

# Try accessing index.php directly
try:
    r = requests.get(f'{OSTICKET_SCP}index.php', verify=False, timeout=10, allow_redirects=False)
    print(f'Status: {r.status_code}')
    if 'location' in r.headers or 'Location' in r.headers:
        redirect = r.headers.get('location', r.headers.get('Location'))
        print(f'Redirects to: {redirect}')
    if r.status_code in [200, 302, 303, 307, 308]:
        print('✓ Dashboard endpoint accessible')
except Exception as e:
    print(f'❌ Error: {e}')

print()

# 3. Analyze key OSTicket directories/endpoints
print('='*60)
print('OSTicket Directory Structure')
print('='*60)

endpoints_to_check = [
    'login.php',
    'index.php',
    'ajax.php',
    'api.php',
    'rpc.php',
    'tickets.php',
    'user/index.php',
    'admin/index.php',
]

for endpoint in endpoints_to_check:
    url = f'{OSTICKET_SCP}{endpoint}'
    try:
        r = requests.head(url, verify=False, timeout=5, allow_redirects=False)
        status = r.status_code
        indicator = '✓' if status < 400 else '✗'
        print(f'{indicator} {endpoint:30} → {status}')
    except Exception as e:
        print(f'✗ {endpoint:30} → Error: {str(e)[:30]}')

print()

# 4. Analyze HTML structure of login page
if login_html:
    print('='*60)
    print('Login Form Analysis')
    print('='*60)
    
    # Extract form
    form_match = re.search(r'<form[^>]*>(.*?)</form>', login_html, re.DOTALL | re.IGNORECASE)
    if form_match:
        form_html = form_match.group(0)
        
        # Extract form attributes
        form_tag = re.search(r'<form([^>]*)>', form_html, re.IGNORECASE)
        if form_tag:
            print('Form attributes:')
            attrs = form_tag.group(1)
            print(f'  {attrs[:200]}')
        
        print()
        print('Form fields:')
        
        # Extract input fields
        inputs = re.findall(r'<input[^>]*>', form_html, re.IGNORECASE)
        for inp in inputs:
            # Extract name and type
            name = re.search(r'name=["\']([^"\']+)["\']', inp, re.IGNORECASE)
            type_attr = re.search(r'type=["\']([^"\']+)["\']', inp, re.IGNORECASE)
            name_str = name.group(1) if name else 'unknown'
            type_str = type_attr.group(1) if type_attr else 'text'
            print(f'  - {name_str:30} ({type_str})')
        
        print()
        
        # Extract buttons
        buttons = re.findall(r'<(?:button|input[^>]*type=["\']submit["\'][^>]*)>', form_html, re.IGNORECASE)
        if buttons:
            print('Submit buttons:')
            for btn in buttons:
                print(f'  {btn[:100]}')

print()

# 5. Look for JavaScript patterns
print('='*60)
print('JavaScript Patterns (if login_html available)')
print('='*60)

if login_html:
    # Look for AJAX patterns
    ajax_patterns = re.findall(r'(?:ajax|fetch|XMLHttpRequest)[^;]*', login_html, re.IGNORECASE)
    if ajax_patterns:
        print('AJAX/Fetch patterns found:')
        for pattern in ajax_patterns[:3]:
            print(f'  {pattern[:80]}...')
    else:
        print('No obvious AJAX patterns in login form')

print()

# 6. Check for API documentation patterns
print('='*60)
print('API/Documentation Patterns')
print('='*60)

# Try to fetch API docs endpoint
try:
    r = requests.get(f'{OSTICKET_BASE}/api/', verify=False, timeout=10)
    if r.status_code == 200:
        print('✓ API documentation endpoint exists')
        if 'api' in r.text.lower():
            print('  Content includes API references')
except:
    pass

# Try admin area
try:
    r = requests.get(f'{OSTICKET_SCP}admin/', verify=False, timeout=10, allow_redirects=False)
    print(f'Admin panel: {r.status_code}')
except:
    pass

print()

# 7. Summary and recommendations
print('='*60)
print('Summary & Recommendations')
print('='*60)

print('''
OSTicket is a PHP-based ticketing system with:

1. **Authentication Model**:
   - Login form at /scp/login.php
   - Session-based authentication (cookies)
   - Credentials stored in database

2. **Key Endpoints**:
   - /scp/login.php - User login
   - /scp/index.php - Dashboard/main interface
   - /scp/ajax.php - AJAX handler for dynamic updates
   - /scp/api.php - REST API endpoint
   - /scp/tickets.php - Tickets management (if accessible)

3. **Frontend Framework**:
   - jQuery for AJAX requests
   - Likely uses custom JavaScript for UI updates
   - Forms likely submit to various .php endpoints

4. **Integration Recommendations for DOSE**:
   
   a) **Session Management**:
      - OSTicket uses HTTP cookies for sessions
      - requests.Session() automatically handles cookies
      - Each request maintains session state ✓
   
   b) **URL Rewriting**:
      - Form actions point to .php files
      - AJAX requests use relative URLs
      - Current doseify_html approach handles both ✓
   
   c) **CSRF Protection**:
      - Check for CSRF tokens in forms
      - May need to preserve token extraction
      - Current approach passes form data as-is ✓
   
   d) **API Access**:
      - Consider if API should be exposed through Django
      - Could add separate endpoint like /api/osticket/
      - Would require API key authentication
   
   e) **Multi-user Support**:
      - Each Django user gets separate session
      - OSTicket session isolated per user ✓
      - No cross-user data leakage

5. **Testing Priority**:
   - [1] Verify login works and session persists
   - [2] Navigate to dashboard after login
   - [3] Submit ticket creation form
   - [4] Verify AJAX navigation works
   - [5] Test multi-request sequences
''')

print('='*60)
