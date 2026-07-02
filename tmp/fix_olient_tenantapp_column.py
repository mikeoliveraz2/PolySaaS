"""Add missing oauth_application_id column to olient.dose_tenantapp."""
from django.db import connection

with connection.cursor() as cur:
    # Check first
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='olient' AND table_name='dose_tenantapp'
        AND column_name='oauth_application_id';
    """)
    exists = cur.fetchone()
    if exists:
        print("Column already exists in olient.dose_tenantapp — nothing to do.")
    else:
        cur.execute("""
            ALTER TABLE olient.dose_tenantapp
            ADD COLUMN IF NOT EXISTS oauth_application_id integer NULL;
        """)
        print("SUCCESS: Added oauth_application_id to olient.dose_tenantapp")

    # Verify
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='olient' AND table_name='dose_tenantapp'
        ORDER BY ordinal_position;
    """)
    cols = [r[0] for r in cur.fetchall()]
    print(f"olient.dose_tenantapp now has {len(cols)} columns: {cols}")
