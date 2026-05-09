"""
Surgical fix: restore missing migration records in public schema,
and properly handle the polysaas tenant schema separately.
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
import django
django.setup()
from django.db import connection

# Step 1: Restore migration records in the PUBLIC schema that we accidentally deleted
# (The polysaas schema shared the same django_migrations table as public due to search_path)
# Actually check: does polysaas have its own django_migrations?
with connection.cursor() as c:
    c.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name = 'django_migrations'
        ORDER BY table_schema;
    """)
    rows = c.fetchall()
    print("django_migrations tables found:", rows)
