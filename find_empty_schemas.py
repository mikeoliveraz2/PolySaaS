import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()
from django.db import connection

with connection.cursor() as c:
    c.execute("""
        SELECT n.nspname
        FROM pg_namespace n
        WHERE n.nspname NOT IN ('public','information_schema','pg_catalog','pg_toast')
          AND n.nspname NOT LIKE 'pg_%'
        ORDER BY n.nspname
    """)
    schemas = [r[0] for r in c.fetchall()]

    empty = []
    for s in schemas:
        c.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name='dose_tenantapp'",
            [s]
        )
        if c.fetchone()[0] == 0:
            empty.append(s)

print("Schemas missing dose_tenantapp:")
for s in empty:
    print(f"  {s}")
print(f"Total: {len(empty)}")
