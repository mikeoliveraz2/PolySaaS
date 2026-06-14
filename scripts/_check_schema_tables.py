import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()
from django.db import connection

with connection.cursor() as c:
    c.execute(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name IN ('polysaasppd','polysaast121','olient') ORDER BY 1"
    )
    print('schemas:', c.fetchall())
    for s in ['polysaasppd', 'polysaast121', 'olient']:
        c.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name LIKE 'dose_%%'",
            [s],
        )
        print(f'{s} dose_* table count:', c.fetchone()[0])
        c.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=%s AND table_name='dose_instruction'",
            [s],
        )
        print(f'  dose_instruction exists:', bool(c.fetchone()))
