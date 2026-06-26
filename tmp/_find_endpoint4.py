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
        SELECT nspname FROM pg_namespace
        WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'
        ORDER BY 1
        """
    )
    schemas = [r[0] for r in c.fetchall()]

for s in schemas:
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{s}", public')
        try:
            c.execute(
                "SELECT id, menu_title, endpoint_url FROM dose_passthroughendpoint WHERE id=4"
            )
            row = c.fetchone()
            if row:
                print(f"endpoint 4 in {s}:", row)
        except Exception as exc:
            print(f"skip {s}: {exc}")
