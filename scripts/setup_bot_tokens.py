"""
Create missing Mattermost bot accounts and generate Personal Access Tokens.

Run once. Prints env-var export lines for any new tokens created.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

import requests
from django.conf import settings

MM_URL = settings.MATTERMOST_URL.rstrip('/')
ADMIN_TOKEN = settings.MATTERMOST_ADMIN_TOKEN
ADMIN_PASS = getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')
H = {'Authorization': f'Bearer {ADMIN_TOKEN}', 'Content-Type': 'application/json'}

BOTS_NEEDED = [
    # (username, display_name, email_domain, env_var_name)
    ('cc', 'CC (Cursor Claude)', 'BOT_TOKEN_CC'),
    ('wsc', 'WSC (Windsurf Claude)', 'BOT_TOKEN_WSC'),
    ('router', 'Router', 'BOT_TOKEN_ROUTER'),
    ('openclaw', 'OpenClaw', 'BOT_TOKEN_OPENCLAW'),
    ('copilot', 'Copilot', 'BOT_TOKEN_COPILOT'),
    ('github', 'GitHub', 'BOT_TOKEN_GITHUB'),
    ('supergrok', 'SuperGrok', 'BOT_TOKEN_SUPERGROK'),
    ('gemini', 'Gemini', 'BOT_TOKEN_GEMINI'),
    ('kimi', 'Kimi', 'BOT_TOKEN_KIMI'),
    ('windsurf', 'Windsurf', 'BOT_TOKEN_WINDSURF'),
]

def get_or_create_user(username, display_name):
    """Get existing user or create a new one. Returns user_id or None."""
    r = requests.get(f'{MM_URL}/api/v4/users/username/{username}', headers=H, timeout=15)
    if r.status_code == 200:
        uid = r.json().get('id')
        print(f"  @{username}: already exists (id={uid})")
        return uid

    email = f'{username}-bot@polysaas.local'
    r2 = requests.post(f'{MM_URL}/api/v4/users', headers=H, json={
        'username': username,
        'email': email,
        'password': ADMIN_PASS,
        'first_name': display_name,
        'last_name': '(AI Peer)',
    }, timeout=15)
    if r2.status_code == 201:
        uid = r2.json().get('id')
        print(f"  @{username}: CREATED (id={uid})")
        return uid
    else:
        print(f"  @{username}: FAILED to create ({r2.status_code}: {r2.text[:150]})")
        return None


def ensure_system_post_all(user_id, username):
    """Grant system_post_all role so the bot can post in any channel."""
    r = requests.get(f'{MM_URL}/api/v4/users/{user_id}', headers=H, timeout=10)
    if r.status_code != 200:
        return
    roles = r.json().get('roles', '')
    if 'system_post_all' not in roles:
        new_roles = (roles + ' system_post_all').strip()
        r2 = requests.put(f'{MM_URL}/api/v4/users/{user_id}/roles', headers=H,
                          json={'roles': new_roles}, timeout=10)
        if r2.status_code == 200:
            print(f"  @{username}: granted system_post_all")
        else:
            print(f"  @{username}: FAILED to grant roles ({r2.status_code})")


def get_existing_tokens(user_id):
    """List existing PATs for a user."""
    r = requests.get(f'{MM_URL}/api/v4/users/{user_id}/tokens', headers=H, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []


def create_token(user_id, username):
    """Create a Personal Access Token. Returns the token string or None."""
    existing = get_existing_tokens(user_id)
    for t in existing:
        if 'PolySaaS' in (t.get('description') or ''):
            print(f"  @{username}: PAT already exists (id={t.get('id')}), but value not retrievable")
            return None

    r = requests.post(f'{MM_URL}/api/v4/users/{user_id}/tokens', headers=H,
                      json={'description': f'PolySaaS AI Peer - {username}'}, timeout=15)
    if r.status_code == 200:
        token = r.json().get('token', '')
        print(f"  @{username}: NEW TOKEN CREATED")
        return token
    else:
        print(f"  @{username}: FAILED to create token ({r.status_code}: {r.text[:150]})")
        return None


def main():
    print("=" * 60)
    print("Mattermost Bot Setup - Create accounts & tokens")
    print("=" * 60)

    new_tokens = {}

    for username, display_name, env_var in BOTS_NEEDED:
        existing_token = getattr(settings, env_var, '')
        print(f"\n--- @{username} ({env_var}) ---")

        if existing_token:
            # Verify the token still works
            r = requests.get(f'{MM_URL}/api/v4/users/me',
                             headers={'Authorization': f'Bearer {existing_token}'},
                             timeout=10)
            if r.status_code == 200:
                uid = r.json().get('id')
                uname = r.json().get('username')
                print(f"  Token valid -> @{uname} (id={uid})")
                ensure_system_post_all(uid, username)
                continue
            else:
                print(f"  Token INVALID ({r.status_code}) -- will create new one")

        user_id = get_or_create_user(username, display_name)
        if not user_id:
            continue

        ensure_system_post_all(user_id, username)
        token = create_token(user_id, username)
        if token:
            new_tokens[env_var] = token

    print("\n" + "=" * 60)
    if new_tokens:
        print("NEW TOKENS - Add these to your environment:")
        print("=" * 60)
        for var, tok in new_tokens.items():
            print(f'$env:{var}="{tok}"')
        print()
        print("# Or add to .env / system environment permanently")
    else:
        print("No new tokens needed -- all existing tokens are valid.")
    print("=" * 60)


if __name__ == '__main__':
    main()
