import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()
from django.db import connection
cur = connection.cursor()
cur.execute("SET search_path TO public")
cur.execute("SELECT extra_config FROM dose_tenantapp WHERE id=45")
row = cur.fetchone()
if row:
    import json
    cfg = row[0] if isinstance(row[0], dict) else json.loads(row[0])
    print("login_id keys:", [k for k in cfg if 'login' in k or 'user' in k or 'mail' in k])
    print("password keys:", [k for k in cfg if 'pass' in k or 'pwd' in k or 'secret' in k])
    login_id = cfg.get('mattermost_login_id') or cfg.get('mm_login_id') or cfg.get('login_id') or ''
    password  = cfg.get('mattermost_password') or cfg.get('mm_password') or cfg.get('password') or ''
    print(f"login_id={login_id!r}  password_present={bool(password)}")
    import urllib.request, json as _json
    payload = _json.dumps({'login_id': login_id, 'password': password}).encode()
    req = urllib.request.Request(
        'https://polysaas-mattermost.onrender.com/api/v4/users/login',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            token = resp.headers.get('Token')
            print(f"HTTP {resp.status} — Token present: {bool(token)} — preview: {(token or '')[:20]}")
    except Exception as e:
        print(f"Login request failed: {e}")
