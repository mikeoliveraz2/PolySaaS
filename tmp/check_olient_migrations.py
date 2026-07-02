"""Check migration state and table columns in olient schema."""
from django.db import connection

with connection.cursor() as cur:
    # Latest migrations in olient
    try:
        cur.execute("SELECT app, name FROM olient.django_migrations ORDER BY applied DESC LIMIT 15;")
        rows = cur.fetchall()
        print("Latest migrations in olient schema:")
        for r in rows:
            print(f"  {r[0]}.{r[1]}")
    except Exception as e:
        print(f"Error reading olient.django_migrations: {e}")

    # Check columns on olient.dose_tenantapp
    try:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='olient' AND table_name='dose_tenantapp'
            ORDER BY ordinal_position;
        """)
        cols = [r[0] for r in cur.fetchall()]
        print(f"\nolient.dose_tenantapp columns ({len(cols)}):")
        for c in cols:
            print(f"  {c}")
    except Exception as e:
        print(f"Error: {e}")

    # Check columns on public.dose_tenantapp
    try:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name='dose_tenantapp'
            ORDER BY ordinal_position;
        """)
        cols = [r[0] for r in cur.fetchall()]
        print(f"\npublic.dose_tenantapp columns ({len(cols)}):")
        for c in cols:
            print(f"  {c}")
    except Exception as e:
        print(f"Error: {e}")
