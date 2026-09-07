"""List Mattermost teams."""
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
    
    with tenant_schema_search_path(tenant):
        ta = TenantApp.objects.filter(app_name='mattermost').first()
        ec = ta.extra_config or {}
        mm_url = ec.get('mm_url', 'http://localhost:8065')
        mm_token = ec.get('mm_token', '')
        
        # List teams
        resp = requests.get(
            f'{mm_url}/api/v4/teams',
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        
        if resp.status_code == 200:
            teams = resp.json()
            print(f'Found {len(teams)} teams:')
            for t in teams:
                print(f'  ID: {t.get("id")}')
                print(f'  Name: {t.get("name")}')
                print(f'  Display: {t.get("display_name")}')
                print()
        else:
            print(f'Error {resp.status_code}: {resp.text}')

if __name__ == '__main__':
    main()
