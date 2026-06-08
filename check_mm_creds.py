import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as cur:
    cur.execute("SET search_path TO polysaast122, public")
    # Get column names first
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='dose_tenantapp' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print("TenantApp columns:", cols)
    
    cur.execute("SELECT id, extra_config FROM dose_tenantapp")
    rows = cur.fetchall()
    for row in rows:
        ec = row[1] or {}
        if isinstance(ec, str):
            ec = json.loads(ec)
        print(f"\nid={row[0]}")
        for k, v in ec.items():
            print(f"  {k}: {str(v)[:50]}")

# Check env vars
print("\n--- ENV vars with mattermost/mm ---")
for k, v in os.environ.items():
    if any(x in k.upper() for x in ['MATTERMOST', 'MM_ADMIN', 'MM_TOKEN', 'MM_URL']):
        print(f"  {k} = {str(v)[:40]}")
