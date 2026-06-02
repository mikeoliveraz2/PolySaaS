"""Check which teams the passthrough user belongs to and add to test-121 if missing."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

import requests
from django.conf import settings

url = settings.MATTERMOST_URL.rstrip('/')
token = settings.MATTERMOST_ADMIN_TOKEN
h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

TARGET_TEAM_ID = 'zxnswsfyhpbs5m8m3qjnau5zzc'  # polysaas-test-121
TARGET_CHANNEL_ID = 'ho8di8ifxfgbjnhkmjeuhcheno'  # town-square

for uname in ['polysaast121', 'pst121']:
    r = requests.get(f'{url}/api/v4/users/username/{uname}', headers=h, timeout=15)
    if r.status_code != 200:
        print(f'@{uname}: not found ({r.status_code})')
        continue

    u = r.json()
    uid = u.get('id')
    email = u.get('email', '')
    print(f'@{uname}: id={uid}, email={email}')

    r2 = requests.get(f'{url}/api/v4/users/{uid}/teams', headers=h, timeout=15)
    if r2.status_code == 200:
        teams = r2.json()
        print(f'  Member of {len(teams)} team(s):')
        for t in teams:
            name = t.get('name', '?')
            tid = t.get('id', '?')
            marker = ' <-- TARGET' if tid == TARGET_TEAM_ID else ''
            print(f'    {name} (id={tid}){marker}')

        team_ids = {t.get('id') for t in teams}
        if TARGET_TEAM_ID not in team_ids:
            print(f'\n  NOT in polysaas-test-121 -- adding now...')
            r3 = requests.post(f'{url}/api/v4/teams/{TARGET_TEAM_ID}/members', headers=h,
                               json={'team_id': TARGET_TEAM_ID, 'user_id': uid}, timeout=15)
            print(f'  Add to team: {r3.status_code}')
            r4 = requests.post(f'{url}/api/v4/channels/{TARGET_CHANNEL_ID}/members', headers=h,
                               json={'user_id': uid}, timeout=15)
            print(f'  Add to town-square: {r4.status_code}')
        else:
            print(f'  Already in polysaas-test-121')

# Also check what login credentials we're using
print('\n--- Login bridge credentials ---')
from dose.passthrough.credential_container import PassthroughCredentialContainer
try:
    creds = PassthroughCredentialContainer()
    # Check TenantApp for mattermost config
    from dose.models import TenantApp
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute("SET search_path TO polysaast121,public;")
    apps = TenantApp.objects.filter(app_name__icontains='mattermost')
    for app in apps:
        ec = app.extra_config or {}
        mm_user = ec.get('mm_username', '')
        mm_email = ec.get('mm_email', '')
        print(f'  TenantApp: {app.app_name}, mm_username={mm_user}, mm_email={mm_email}')
except Exception as e:
    print(f'  Error checking creds: {e}')
