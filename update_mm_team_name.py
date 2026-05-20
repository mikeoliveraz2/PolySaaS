#!/usr/bin/env python
"""
Update Mattermost team name in TenantApp extra_config for test tenants.
Set mm_team_name to PolySaaS-Dev-Team for all Mattermost TenantApps.
"""
import os
import django
import json
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '/workspace' if os.path.exists('/workspace') else '/f/PolySaaS')
django.setup()

from dose.models import TenantApp
from django.db import connection

def update_mattermost_team_names():
    """Update mm_team_name to PolySaaS-Dev-Team in all Mattermost TenantApps."""
    
    # Update all Mattermost tenant apps
    with connection.cursor() as cur:
        cur.execute("SET search_path TO public,pg_catalog")
        
        # Get all mattermost TenantApps
        mattermost_apps = TenantApp.objects.filter(app_name='mattermost')
        
        for ta in mattermost_apps:
            config = ta.extra_config or {}
            old_team_name = config.get('mm_team_name', 'NOT SET')
            
            # Update team name
            config['mm_team_name'] = 'PolySaaS-Dev-Team'
            ta.extra_config = config
            ta.save(update_fields=['extra_config'])
            
            print(f"✅ {ta.tenant.name} Mattermost: mm_team_name {old_team_name} → PolySaaS-Dev-Team")

if __name__ == '__main__':
    print("[MM TEAM NAME UPDATE] Starting...")
    update_mattermost_team_names()
    print("[MM TEAM NAME UPDATE] Complete!")
