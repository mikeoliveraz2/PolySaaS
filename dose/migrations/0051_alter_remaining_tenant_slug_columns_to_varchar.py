# Fix tenant_slug columns left as bigint after 0036 slug-PK migration.
# 0041/0042 only converted navigation + dashboardbutton; Instruction, CallBackData,
# Mapping, etc. were missed — breaks provision_odoo_invoicing_orchestration on new tenants.

from django.db import migrations

_TENANT_SLUG_TO_VARCHAR_SQL = """
DO $$
DECLARE
    r RECORD;
    target_type text;
BEGIN
    FOR r IN
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name LIKE 'dose_%'
          AND column_name IN ('tenant_slug', 'tenant_id')
          AND data_type IN ('bigint', 'integer', 'smallint')
    LOOP
        IF r.table_name = 'dose_subscription' THEN
            target_type := 'varchar(255)';
        ELSE
            target_type := 'varchar(50)';
        END IF;
        EXECUTE format(
            'ALTER TABLE %I ALTER COLUMN %I TYPE %s USING %I::%s',
            r.table_name, r.column_name, target_type, r.column_name, target_type
        );
    END LOOP;
END $$;
"""

_TENANT_SLUG_TO_BIGINT_REVERSE_SQL = """
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name LIKE 'dose_%'
          AND column_name IN ('tenant_slug', 'tenant_id')
          AND data_type IN ('character varying', 'varchar')
    LOOP
        EXECUTE format(
            'ALTER TABLE %I ALTER COLUMN %I TYPE bigint USING NULLIF(%I, '''')::bigint',
            r.table_name, r.column_name, r.column_name
        );
    END LOOP;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0050_merge_20260522_1343'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_TENANT_SLUG_TO_VARCHAR_SQL,
            reverse_sql=_TENANT_SLUG_TO_BIGINT_REVERSE_SQL,
        ),
    ]
