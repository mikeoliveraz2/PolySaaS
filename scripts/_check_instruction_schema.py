import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()
from django.db import connection

for schema in ['polysaasppd', 'polysaast121', 'public']:
    with connection.cursor() as c:
        c.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'dose_instruction'
            ORDER BY ordinal_position
        """, [schema])
        rows = c.fetchall()
        print(f'\n=== {schema}.dose_instruction columns ===')
        if not rows:
            print('  (table missing)')
        for name, dtype in rows:
            print(f'  {name}: {dtype}')
