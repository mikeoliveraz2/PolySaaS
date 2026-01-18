import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("=== Checking Schema for Allauth Tables ===\n")

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE 'socialaccount%'
        ORDER BY schemaname, tablename;
    """)

    tables = cursor.fetchall()
    print(f"Found {len(tables)} socialaccount tables across schemas:\n")

    current_schema = None
    for schema, table in tables:
        if schema != current_schema:
            current_schema = schema
            print(f"\n[Schema: {schema}]")
        print(f"  - {table}")

print("\n=== Current Database Connection ===")
print(f"Database: {connection.settings_dict['NAME']}")
print(f"Schema search path: {connection.schema_name if hasattr(connection, 'schema_name') else 'default'}")
