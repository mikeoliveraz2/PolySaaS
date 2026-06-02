"""Quick test: post a message from each bot to verify tokens work."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

import requests
from django.conf import settings

MM_URL = settings.MATTERMOST_URL.rstrip('/')
ADMIN_TOKEN = settings.MATTERMOST_ADMIN_TOKEN
H = {'Authorization': f'Bearer {ADMIN_TOKEN}', 'Content-Type': 'application/json'}

TEAM_SLUG = 'polysaas-test-121'
CHANNEL_ID = 'ho8di8ifxfgbjnhkmjeuhcheno'

BOTS = [
    ('supergrok', 'BOT_TOKEN_SUPERGROK', 'Grok (xAI)'),
    ('gemini', 'BOT_TOKEN_GEMINI', 'Gemini (Google)'),
    ('cc', 'BOT_TOKEN_CC', 'CC (Cursor Claude)'),
    ('copilot', 'BOT_TOKEN_COPILOT', 'Copilot (Anthropic)'),
    ('github', 'BOT_TOKEN_GITHUB', 'GitHub (Anthropic)'),
    ('wsc', 'BOT_TOKEN_WSC', 'WSC (Windsurf Claude)'),
    ('router', 'BOT_TOKEN_ROUTER', 'Router (Anthropic)'),
    ('openclaw', 'BOT_TOKEN_OPENCLAW', 'OpenClaw (Anthropic)'),
    ('kimi', 'BOT_TOKEN_KIMI', 'Kimi (Moonshot)'),
    ('windsurf', 'BOT_TOKEN_WINDSURF', 'Windsurf'),
]

# First ensure all bots are in the team + channel
team_id = 'zxnswsfyhpbs5m8m3qjnau5zzc'

print("=== Adding bots to team + channel ===")
for username, token_var, label in BOTS:
    token = getattr(settings, token_var, '') or os.environ.get(token_var, '')
    if not token:
        print(f"  @{username}: NO TOKEN -- skipping")
        continue
    # Get user id from token
    r = requests.get(f'{MM_URL}/api/v4/users/me',
                     headers={'Authorization': f'Bearer {token}'}, timeout=10)
    if r.status_code != 200:
        print(f"  @{username}: token invalid ({r.status_code})")
        continue
    uid = r.json().get('id')
    # Add to team
    requests.post(f'{MM_URL}/api/v4/teams/{team_id}/members', headers=H,
                  json={'team_id': team_id, 'user_id': uid}, timeout=10)
    # Add to channel
    requests.post(f'{MM_URL}/api/v4/channels/{CHANNEL_ID}/members', headers=H,
                  json={'user_id': uid}, timeout=10)
    print(f"  @{username}: added to team + channel")

print("\n=== Posting test messages ===")
for username, token_var, label in BOTS:
    token = getattr(settings, token_var, '') or os.environ.get(token_var, '')
    if not token:
        print(f"  @{username}: NO TOKEN -- skipping")
        continue
    r = requests.post(f'{MM_URL}/api/v4/posts',
                      headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                      json={'channel_id': CHANNEL_ID, 'message': f'**{label}** checking in! Ready to answer questions.'},
                      timeout=15)
    status = 'OK' if r.status_code == 201 else f'FAIL ({r.status_code}: {r.text[:80]})'
    print(f"  @{username}: {status}")
