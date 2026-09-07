"""Update Mattermost webhook to use host.docker.internal."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

import requests
from dose.models import TenantApp, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path

WEBHOOK_ID = 'to8h4hjgabyzxqrnmdw39gom5h'
NEW_CALLBACK = 'http://host.docker.internal:8000/hooks/mattermost/events/'

def main():
    tenant = Tenant.objects.filter(schema_name='polysaasonline').first()
    if not tenant:
        tenant = Tenant.objects.exclude(schema_name='public').first()
    
    with tenant_schema_search_path(tenant):
        ta = TenantApp.objects.filter(app_name='mattermost').first()
        ec = ta.extra_config or {}
        mm_url = ec.get('mm_url', 'http://localhost:8065')
        mm_token = ec.get('mm_token', '')
        
        print(f'Updating webhook {WEBHOOK_ID}...')
        print(f'New callback: {NEW_CALLBACK}')
        
        # FIXED: Single-word trigger - MM tokenizes on whitespace, so "New contact:" never matches
        # The first word of "New contact: Name, email, Co" is just "New"
        resp = requests.put(
            f'{mm_url}/api/v4/hooks/outgoing/{WEBHOOK_ID}',
            json={
                'id': WEBHOOK_ID,
                'callback_urls': [NEW_CALLBACK],
                'display_name': 'PolySaaS Contact Webhook',
                'trigger_words': ['New'],  # Single token! MM matches first word only
                'trigger_when': 0,  # 0 = exact match on first word
                'content_type': 'application/json',
            },
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        
        if resp.status_code == 200:
            print('Webhook updated successfully!')
            hook = resp.json()
            print(f'Callback URLs: {hook.get("callback_urls")}')
        else:
            print(f'Error {resp.status_code}: {resp.text}')

if __name__ == '__main__':
    main()
