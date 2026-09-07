"""Delete the old broken Mattermost webhook."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

import requests
from dose.models import TenantApp, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path

OLD_WEBHOOK_ID = 'notqo38oojd4bqgtsprk9dsk4a'

def main():
    tenant = Tenant.objects.filter(schema_name='polysaasonline').first()
    if not tenant:
        tenant = Tenant.objects.exclude(schema_name='public').first()
    
    with tenant_schema_search_path(tenant):
        ta = TenantApp.objects.filter(app_name='mattermost').first()
        ec = ta.extra_config or {}
        mm_url = ec.get('mm_url', 'http://localhost:8065')
        mm_token = ec.get('mm_token', '')
        
        print(f'Deleting old webhook {OLD_WEBHOOK_ID}...')
        resp = requests.delete(
            f'{mm_url}/api/v4/hooks/outgoing/{OLD_WEBHOOK_ID}',
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        
        if resp.status_code in (200, 204):
            print('Deleted successfully!')
        else:
            print(f'Error {resp.status_code}: {resp.text}')

if __name__ == '__main__':
    main()
