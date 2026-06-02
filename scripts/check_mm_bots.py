"""Quick check: Mattermost outgoing webhooks, teams, and bot accounts."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

import requests
from django.conf import settings

url = settings.MATTERMOST_URL.rstrip('/')
token = settings.MATTERMOST_ADMIN_TOKEN
h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("=== Outgoing Webhooks ===")
r = requests.get(f'{url}/api/v4/hooks/outgoing', headers=h, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    hooks = r.json()
    print(f"Found {len(hooks)} outgoing webhook(s)")
    for hook in hooks:
        hid = hook.get('id', '?')
        ch = hook.get('channel_id', '?')
        triggers = hook.get('trigger_words', [])
        urls = hook.get('callback_urls', [])
        print(f"  ID={hid}  channel={ch}  triggers={triggers}  urls={urls}")
else:
    print(f"Error: {r.text[:200]}")

print("\n=== Teams ===")
r2 = requests.get(f'{url}/api/v4/teams', headers=h, timeout=15)
if r2.status_code == 200:
    for t in r2.json():
        print(f"  {t.get('name')} (id={t.get('id')})")
else:
    print(f"Error: {r2.text[:200]}")

print("\n=== Bot User Accounts ===")
for uname in ['supergrok', 'grok', 'gemini', 'gem', 'cc', 'copilot', 'github',
              'kimi', 'windsurf', 'ws', 'wsc', 'router', 'openclaw']:
    r3 = requests.get(f'{url}/api/v4/users/username/{uname}', headers=h, timeout=10)
    if r3.status_code == 200:
        u = r3.json()
        print(f"  @{uname}: EXISTS (id={u.get('id')}, roles={u.get('roles', '')})")
    else:
        print(f"  @{uname}: MISSING ({r3.status_code})")

print("\n=== Town Square Channel ===")
r4 = requests.get(f'{url}/api/v4/teams', headers=h, timeout=15)
if r4.status_code == 200:
    for team in r4.json():
        tid = team.get('id')
        r5 = requests.get(f'{url}/api/v4/teams/{tid}/channels/name/town-square', headers=h, timeout=10)
        if r5.status_code == 200:
            ch = r5.json()
            print(f"  Team '{team.get('name')}': town-square id={ch.get('id')}")
