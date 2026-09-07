"""Enable Mattermost internal connections to host.docker.internal."""
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
        
        # Get current config first
        print('Getting current config...')
        resp = requests.get(
            f'{mm_url}/api/v4/config',
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        if resp.status_code != 200:
            print(f'Error getting config: {resp.status_code}')
            return
        
        config = resp.json()
        config['ServiceSettings']['AllowedUntrustedInternalConnections'] = 'host.docker.internal localhost 127.0.0.1'
        
        # Update config
        print('Updating Mattermost config to allow host.docker.internal...')
        resp = requests.put(
            f'{mm_url}/api/v4/config',
            json=config,
            headers={'Authorization': f'Bearer {mm_token}'},
            timeout=15
        )
        
        if resp.status_code == 200:
            print('Config updated successfully!')
            config = resp.json()
            service = config.get('ServiceSettings', {})
            print(f'AllowedUntrustedInternalConnections: {service.get("AllowedUntrustedInternalConnections")}')
        else:
            print(f'Error {resp.status_code}: {resp.text[:500]}')

if __name__ == '__main__':
    main()
