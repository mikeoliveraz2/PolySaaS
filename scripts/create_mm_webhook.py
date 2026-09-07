"""Create Mattermost outgoing webhook for contact messages."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

import requests
from dose.models import TenantApp, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path

NGROK_URL = 'https://euphemism-exes-caregiver.ngrok-free.dev'

def main():
    # Try both possible schema names
    tenant = Tenant.objects.filter(schema_name__in=['olient', 'polysaasonline']).first()
    if not tenant:
        tenant = Tenant.objects.exclude(schema_name='public').first()
    if not tenant:
        print('No tenant found')
        return 1
    print(f'Using tenant: {tenant.schema_name}')
    with tenant_schema_search_path(tenant):
        ta = TenantApp.objects.filter(app_name='mattermost').first()
        if not ta:
            print('No Mattermost TenantApp found')
            return 1
        
        ec = ta.extra_config or {}
        mm_url = ec.get('mm_url', 'http://localhost:8065')
        mm_token = ec.get('mm_token', '')
        team_id = ec.get('mm_team_id', '')
        channel_id = ec.get('mm_channel_id', '')
        
        if not mm_token:
            print('ERROR: No mm_token in TenantApp extra_config')
            return 1
        
        print(f'Creating outgoing webhook on {mm_url}...')
        print(f'Team ID: {team_id}')
        print(f'Channel ID: {channel_id}')
        print(f'Callback: {NGROK_URL}/hooks/mattermost/events/')
        
        resp = requests.post(
            f'{mm_url}/api/v4/hooks/outgoing',
            json={
                'team_id': team_id,
                'channel_id': channel_id,
                'display_name': 'PolySaaS Contact Webhook',
                'description': 'Sends contact messages to PolySaaS for Odoo creation',
                'trigger_words': ['New contact:'],
                'callback_urls': [f'{NGROK_URL}/hooks/mattermost/events/'],
                'content_type': 'application/json',
            },
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        
        if resp.status_code == 201:
            hook = resp.json()
            token = hook.get('token', '')
            print(f'SUCCESS! Webhook created.')
            print(f'Webhook ID: {hook.get("id")}')
            
            # Save token to TenantApp
            ec['mm_webhook_token'] = token
            ta.extra_config = ec
            ta.save(update_fields=['extra_config'])
            print('Token saved to TenantApp.extra_config')
            return 0
        else:
            print(f'ERROR {resp.status_code}: {resp.text}')
            return 1

if __name__ == '__main__':
    sys.exit(main())
