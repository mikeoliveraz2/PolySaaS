import os, sys, re
sys.path.insert(0, r'D:\PolySaaS')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User

c = Client()
u = User.objects.get(username='pso17')
c.force_login(u)
c.session['tenant_slug'] = 'pso17'
c.session.save()

r = c.get('/pt/polysniff/4/admin/index.php?mainmenu=home&leftmenu=setup&mesg=setupnotcomplete')
if r.status_code in (301, 302):
    print('REDIRECT', r.get('Location'))
    r = c.get(r.get('Location'))
print('STATUS', r.status_code)
html = r.content.decode('utf-8', 'ignore')
print('LEN', len(html))
print('has /dose/home/', '/dose/home/' in html)
print('has /accounts/login/', '/accounts/login/' in html)
print('has text/html', 'text/html' in html)

# Find all script/link hrefs containing dose/home or accounts/login
for m in re.finditer(r'<(script|link)[^>]*(?:src|href)=["\']([^"\']*(?:dose/home|accounts/login)[^"\']*)["\'][^>]*>', html, re.I):
    print('  BAD:', m.group(0)[:200])

# Find all script/link tags to see distribution
for m in re.finditer(r'<(script|link)[^>]*(?:src|href)=["\']([^"\']+)["\'][^>]*>', html, re.I):
    tag, url = m.group(1), m.group(2)
    if '/pt/' not in url and not url.startswith('http'):
        if tag == 'script' and 'home' in url:
            print('  SUSPICIOUS SCRIPT:', url[:100])
        elif tag == 'link' and 'login' in url:
            print('  SUSPICIOUS LINK:', url[:100])
