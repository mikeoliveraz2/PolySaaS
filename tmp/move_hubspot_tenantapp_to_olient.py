"""
Copy the HubSpot TenantApp row from public.dose_tenantapp into olient.dose_tenantapp.

TenantApp is tenant-scoped — same pattern as tmp/move_odoo_tenantapp_to_olient.py.
Run once per tenant that still has HubSpot bundle data only in public.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.db import connection

TENANT_SLUG = "olient"
SCHEMA = "olient"
APP_NAME = "hubspot"


def main():
    with connection.cursor() as cur:
        cur.execute("SET search_path TO public")
        cur.execute(
            """
            SELECT t.slug, t.schema_name
            FROM dose_tenant t
            WHERE t.slug = %s AND t.is_active = TRUE
            """,
            [TENANT_SLUG],
        )
        tenant_row = cur.fetchone()
        if not tenant_row:
            print(f"ERROR: Tenant slug={TENANT_SLUG!r} not found in public.dose_tenant")
            return 1
        tenant_id, schema = tenant_row
        schema = schema or SCHEMA
        print(f"Tenant slug={tenant_id} schema={schema}")

        cur.execute(
            """
            SELECT id, app_name, app_url, provisioned_at, status, last_error,
                   tenant_id, extra_config, oauth_application_id
            FROM public.dose_tenantapp
            WHERE app_name = %s AND tenant_id = %s
            """,
            [APP_NAME, tenant_id],
        )
        row = cur.fetchone()
        if not row:
            print(f"No HubSpot TenantApp in public for tenant_id={tenant_id}")
            print("Checking olient schema only...")
        else:
            (
                pid,
                app_name,
                app_url,
                provisioned_at,
                status,
                last_error,
                _tid,
                extra_config,
                oauth_application_id,
            ) = row
            if isinstance(extra_config, str):
                extra_config = json.loads(extra_config)
            print(f"Found in public: id={pid} status={status}")
            keys = list(extra_config.keys()) if isinstance(extra_config, dict) else []
            print(f"  extra_config keys: {keys}")

            cur.execute(
                f"SELECT id FROM {schema}.dose_tenantapp WHERE app_name = %s",
                [APP_NAME],
            )
            existing = cur.fetchone()
            extra_json = json.dumps(extra_config or {})
            if existing:
                print(f"Already in {schema} (id={existing[0]}) — updating extra_config...")
                cur.execute(
                    f"""
                    UPDATE {schema}.dose_tenantapp
                    SET extra_config = %s::jsonb, status = %s, last_error = %s, app_url = %s
                    WHERE app_name = %s
                    """,
                    [extra_json, status, last_error or "", app_url or "", APP_NAME],
                )
            else:
                print(f"Inserting into {schema}.dose_tenantapp...")
                cur.execute(
                    f"""
                    INSERT INTO {schema}.dose_tenantapp
                        (app_name, app_url, provisioned_at, status, last_error,
                         tenant_id, extra_config, oauth_application_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    """,
                    [
                        app_name,
                        app_url,
                        provisioned_at,
                        status,
                        last_error or "",
                        tenant_id,
                        extra_json,
                        oauth_application_id,
                    ],
                )

        cur.execute(
            f"""
            SELECT id, app_name, status,
                   extra_config->>'hs_hub_subdomain' AS hub,
                   extra_config->>'hs_portal_id' AS portal_id,
                   extra_config ? 'hs_web_cookies' AS has_cookies
            FROM {schema}.dose_tenantapp
            WHERE app_name = %s
            """,
            [APP_NAME],
        )
        verify = cur.fetchone()
        if verify:
            print(
                f"\nVerified in {schema}: id={verify[0]} status={verify[2]} "
                f"hub={verify[3]!r} portalId={verify[4]!r} has_cookies={verify[5]}"
            )
        else:
            print(f"\nERROR: No HubSpot TenantApp in {schema} after migration")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
