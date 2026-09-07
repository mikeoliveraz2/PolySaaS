"""List Mattermost outgoing webhooks."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

import requests
from dose.models import TenantApp, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path

def main():
    tenant = Tenant.objects.filter(schema_name='polysaasonline').first()
    if not tenant:
        tenant = Tenant.objects.exclude(schema_name='public').first()
    if not tenant:
        print('No tenant found')
        return 1
    
    with tenant_schema_search_path(tenant):
        ta = TenantApp.objects.filter(app_name='mattermost').first()
        if not ta:
            print('No Mattermost TenantApp found')
            return 1
        
        ec = ta.extra_config or {}
        mm_url = ec.get('mm_url', 'http://localhost:8065')
        mm_token = ec.get('mm_token', '')
        
        if not mm_token:
            print('No mm_token')
            return 1
        
        # List outgoing webhooks
        resp = requests.get(
            f'{mm_url}/api/v4/hooks/outgoing',
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        
        if resp.status_code == 200:
            hooks = resp.json()
            print(f'Found {len(hooks)} outgoing webhooks:')
            for h in hooks:
                print(f'  ID: {h.get("id")}')
                print(f'  Display: {h.get("display_name")}')
                print(f'  Team ID: {h.get("team_id")}')
                print(f'  Channel ID: {h.get("channel_id") or "(all channels)"}')
                print(f'  Trigger words: {h.get("trigger_words")}')
                print(f'  Trigger when: {h.get("trigger_when")} (0=first word, 1=exactly)')
                print(f'  Callback URLs: {h.get("callback_urls")}')
                print(f'  Content type: {h.get("content_type")}')
                print()
        else:
            print(f'Error {resp.status_code}: {resp.text}')
            return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
