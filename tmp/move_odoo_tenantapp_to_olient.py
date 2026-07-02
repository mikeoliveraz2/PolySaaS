"""
Copy the Odoo TenantApp row from public.dose_tenantapp into olient.dose_tenantapp.
TenantApp is a tenant-scoped model and should live in the tenant schema.
"""
from django.db import connection

with connection.cursor() as cur:
    # Read from public
    cur.execute("""
        SELECT id, app_name, app_url, provisioned_at, status, last_error,
               tenant_id, extra_config, oauth_application_id
        FROM public.dose_tenantapp
        WHERE app_name = 'odoo' AND tenant_id = 'olient';
    """)
    row = cur.fetchone()
    if not row:
        print("ERROR: No Odoo TenantApp found in public for tenant_id='olient'")
    else:
        (pid, app_name, app_url, provisioned_at, status, last_error,
         tenant_id, extra_config, oauth_application_id) = row
        import json
        if isinstance(extra_config, str):
            extra_config = json.loads(extra_config)
        print(f"Found in public: id={pid} app_name={app_name} status={status}")
        print(f"  extra_config keys: {list(extra_config.keys()) if extra_config else 'None'}")

        # Check if already in olient
        cur.execute("SELECT id FROM olient.dose_tenantapp WHERE app_name='odoo';")
        existing = cur.fetchone()
        if existing:
            print(f"Already exists in olient (id={existing[0]}) — updating extra_config...")
            cur.execute("""
                UPDATE olient.dose_tenantapp
                SET extra_config = %s, status = %s, last_error = %s
                WHERE app_name = 'odoo';
            """, [connection.Database.extras.Json(extra_config) if hasattr(connection.Database, 'extras') else extra_config, status, last_error])
        else:
            print("Inserting into olient.dose_tenantapp...")
            cur.execute("""
                INSERT INTO olient.dose_tenantapp
                    (app_name, app_url, provisioned_at, status, last_error,
                     tenant_id, extra_config, oauth_application_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s);
            """, [
                app_name, app_url, provisioned_at, status, last_error,
                tenant_id, json.dumps(extra_config) if extra_config else '{}', oauth_application_id
            ])

        # Verify
        cur.execute("""
            SELECT id, app_name, status, extra_config->'odoo_url' as url,
                   extra_config->'odoo_login' as login
            FROM olient.dose_tenantapp WHERE app_name='odoo';
        """)
        verify = cur.fetchone()
        if verify:
            print(f"\nVerified in olient: id={verify[0]} status={verify[2]} url={verify[3]} login={verify[4]}")
        else:
            print("\nERROR: Row not found in olient after insert!")
