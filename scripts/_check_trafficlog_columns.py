import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute(
        """
        SELECT table_schema
        FROM information_schema.tables
        WHERE table_name = 'polysniffer_trafficlog'
        ORDER BY 1
        """
    )
    schemas = [r[0] for r in c.fetchall()]
    print("schemas with trafficlog:", len(schemas), "includes polysaasppv", "polysaasppv" in schemas)

with connection.cursor() as c:
    c.execute(
        """
        SELECT table_schema FROM information_schema.tables
        WHERE table_name = 'polysniffer_trafficcapture'
        AND table_schema IN ('public','polysaasppv','polysaast125')
        """
    )
    print("trafficcapture:", c.fetchall())

for schema in ("public", "polysaasppv"):
    with connection.cursor() as c:
        c.execute(
            """
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'polysniffer_trafficlog'
            ORDER BY ordinal_position
            """,
            [schema],
        )
        rows = c.fetchall()
        if rows:
            print(f"\n=== {schema} ===")
            for row in rows:
                print(row)
