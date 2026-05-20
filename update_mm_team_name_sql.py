#!/usr/bin/env python
"""
Direct SQL update to set mm_team_name in TenantApp extra_config
Bypasses Django to avoid gcloud auth issues.
"""
import json
import psycopg2
from psycopg2 import sql
import os

# Get database connection details from environment or settings
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5433))
DB_NAME = os.getenv('DB_NAME', 'dosedbsaas')
DB_USER = os.getenv('DB_USER', 'dosedbadmin')
DB_PASSWORD = os.getenv('DOSE_DB_PASSWORD', 'PolySaaS2026!')

def update_team_names():
    """Update mm_team_name in all Mattermost TenantApps."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Get all Mattermost TenantApps
        cursor.execute("""
            SELECT id, tenant_id, extra_config 
            FROM dose_tenantapp 
            WHERE app_name = 'mattermost'
        """)
        
        results = cursor.fetchall()
        
        for ta_id, tenant_id, extra_config in results:
            config = json.loads(extra_config) if extra_config else {}
            old_team = config.get('mm_team_name', 'NOT SET')
            
            config['mm_team_name'] = 'PolySaaS-Dev-Team'
            new_config = json.dumps(config)
            
            cursor.execute("""
                UPDATE dose_tenantapp 
                SET extra_config = %s 
                WHERE id = %s
            """, (new_config, ta_id))
            
            print(f"✅ TenantApp {ta_id}: mm_team_name {old_team} → PolySaaS-Dev-Team")
        
        conn.commit()
        print(f"\nUpdated {len(results)} Mattermost TenantApps")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    print("[MM TEAM NAME UPDATE - SQL] Starting...")
    update_team_names()
    print("[MM TEAM NAME UPDATE - SQL] Complete!")
