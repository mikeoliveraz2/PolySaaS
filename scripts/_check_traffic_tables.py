import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute(
        "SELECT schemaname, tablename FROM pg_tables "
        "WHERE tablename LIKE '%traffic%' ORDER BY 1 LIMIT 30"
    )
    for row in c.fetchall():
        print(row)
