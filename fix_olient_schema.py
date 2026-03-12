"""
Fix olient schema: manually drop the partial index that the allauth migration
can't drop as a constraint, then fake the migration.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

print("=== Step 1: Drop the partial index in olient schema ===")
cursor.execute("SET search_path TO olient")
try:
    cursor.execute("DROP INDEX IF EXISTS account_emailaddress_email_idx")
    connection.connection.commit()
    print("  Dropped account_emailaddress_email_idx")
except Exception as e:
    print(f"  Failed: {e}")
    connection.connection.rollback()

# Also drop any leftover duplicates
try:
    cursor.execute("DROP INDEX IF EXISTS account_emailaddress_email_idx1")
    cursor.execute("DROP INDEX IF EXISTS account_emailaddress_email_idx2")
    connection.connection.commit()
    print("  Cleaned up idx1/idx2 duplicates")
except Exception as e:
    print(f"  Cleanup note: {e}")
    connection.connection.rollback()

cursor.execute("SET search_path TO public")
connection.connection.commit()

print("\n=== Step 2: Fake migration 0004 for olient schema ===")
# We need to mark account.0004 as applied for the olient schema
# Since our custom migrate_all_schemas handles per-schema migration,
# we'll directly insert the migration record
try:
    cursor.execute("SET search_path TO olient, public")
    # Check if django_migrations table exists in olient
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'olient' AND table_name = 'django_migrations'
        )
    """)
    has_table = cursor.fetchone()[0]

    if has_table:
        # Check if already faked
        cursor.execute("""
            SELECT id FROM django_migrations
            WHERE app = 'account' AND name = '0004_alter_emailaddress_drop_unique_email'
        """)
        exists = cursor.fetchone()
        if exists:
            print("  Migration 0004 already recorded — nothing to fake")
        else:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('account', '0004_alter_emailaddress_drop_unique_email', NOW())
            """)
            connection.connection.commit()
            print("  Faked account.0004 for olient schema")
    else:
        print("  No django_migrations table in olient — using public")
        cursor.execute("SET search_path TO public")
        cursor.execute("""
            SELECT id FROM django_migrations
            WHERE app = 'account' AND name = '0004_alter_emailaddress_drop_unique_email'
        """)
        exists = cursor.fetchone()
        if exists:
            print("  Migration 0004 already recorded in public schema")
        else:
            print("  Migration 0004 NOT in public schema either — will need manual fake")

except Exception as e:
    print(f"  Fake failed: {e}")
    connection.connection.rollback()

cursor.execute("SET search_path TO public")
connection.connection.commit()

print("\n=== Step 3: Retry full migrate ===")
from django.core.management import call_command
call_command('migrate', verbosity=1)

print("\nDone")
