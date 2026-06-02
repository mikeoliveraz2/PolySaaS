"""Regenerate tokens for bots that have expired PATs."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

import requests
from django.conf import settings

MM_URL = settings.MATTERMOST_URL.rstrip('/')
ADMIN_TOKEN = settings.MATTERMOST_ADMIN_TOKEN
H = {'Authorization': f'Bearer {ADMIN_TOKEN}', 'Content-Type': 'application/json'}

REGEN = {
    'supergrok': ('wekn1bb1affq7b47ta5jzjjkxc', 'BOT_TOKEN_SUPERGROK'),
    'gemini': ('6jyogh17bjg97fxqrz55oiinzc', 'BOT_TOKEN_GEMINI'),
    'copilot': ('yjcig8brztd9xppwi41xt7zegw', 'BOT_TOKEN_COPILOT'),
    'github': ('49635fas4f83bd9nb9us1tf3kr', 'BOT_TOKEN_GITHUB'),
}

for username, (user_id, env_var) in REGEN.items():
    print(f"--- @{username} ---")
    r = requests.post(f'{MM_URL}/api/v4/users/{user_id}/tokens', headers=H,
                      json={'description': f'PolySaaS AI Peer regen - {username}'}, timeout=15)
    if r.status_code == 200:
        token = r.json().get('token', '')
        print(f'  $env:{env_var}="{token}"')
    else:
        print(f'  FAILED ({r.status_code}: {r.text[:150]})')
