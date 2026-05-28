#!/usr/bin/env python3
"""
Standalone plugin deploy script — no Django required.
Uses MATTERMOST_ADMIN_TOKEN from environment.
"""
import os
import sys
import requests

MM_URL = os.environ.get('MATTERMOST_SHARED_URL', 'https://polysaas-mattermost.onrender.com').rstrip('/')
TOKEN = os.environ.get('MATTERMOST_ADMIN_TOKEN', '')
PLUGIN_ZIP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'mattermost-passthrough-plugin', 'polysaas-passthrough-plugin.zip')
PLUGIN_ID = 'com.polysaas.passthrough'


def main():
    if not TOKEN:
        print("ERROR: MATTERMOST_ADMIN_TOKEN not set in environment")
        print("Set it: export MATTERMOST_ADMIN_TOKEN=your_token_here")
        sys.exit(1)

    if not os.path.exists(PLUGIN_ZIP):
        print(f"ERROR: Plugin zip not found: {PLUGIN_ZIP}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Verify token
    print(f"Checking token against {MM_URL}...")
    me = requests.get(f"{MM_URL}/api/v4/users/me", headers=headers, timeout=10)
    if me.status_code != 200:
        print(f"ERROR: Token invalid: {me.status_code}")
        sys.exit(1)
    print(f"OK: Token valid (user: {me.json().get('username')})")

    # Check if plugin already exists and remove it
    print(f"Checking for existing plugin {PLUGIN_ID}...")
    plugins = requests.get(f"{MM_URL}/api/v4/plugins", headers=headers, timeout=10)
    if plugins.status_code == 200:
        for p in plugins.json():
            if p.get('id') == PLUGIN_ID:
                print(f"Removing existing plugin {PLUGIN_ID}...")
                r = requests.delete(f"{MM_URL}/api/v4/plugins/{PLUGIN_ID}", headers=headers, timeout=30)
                print(f"  Remove: {r.status_code}")
                break

    # Upload
    print(f"Uploading {PLUGIN_ZIP}...")
    with open(PLUGIN_ZIP, 'rb') as f:
        upload = requests.post(
            f"{MM_URL}/api/v4/plugins",
            headers=headers,
            files={'plugin': ('polysaas-passthrough-plugin.zip', f, 'application/zip')},
            timeout=60,
        )
    print(f"  Upload: {upload.status_code}")
    if upload.status_code not in (200, 201):
        print(f"  Response: {upload.text[:300]}")
        sys.exit(1)

    # Enable
    print(f"Enabling plugin {PLUGIN_ID}...")
    enable = requests.post(f"{MM_URL}/api/v4/plugins/{PLUGIN_ID}/enable", headers=headers, timeout=30)
    print(f"  Enable: {enable.status_code}")

    print("\nDone. Plugin installed and enabled.")
    print("\nNEXT STEPS:")
    print("1. Go to Mattermost System Console → Plugins → PolySaaS Passthrough Plugin")
    print("2. Set 'PolySaaS Shared Secret' to a strong random string")
    print("3. Set the SAME string in Django's MATTERMOST_PASSTHROUGH_SECRET setting")
    print("   export MATTERMOST_PASSTHROUGH_SECRET=<same-value>")


if __name__ == '__main__':
    main()
