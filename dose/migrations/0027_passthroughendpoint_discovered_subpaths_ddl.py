# 0011 used RunSQL.noop + state_operations, so migration state had discovered_subpaths
# but PostgreSQL never got the column. This migration applies the real DDL.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0026_remove_fake_public_schema_tenant"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE dose_passthroughendpoint
            ADD COLUMN IF NOT EXISTS discovered_subpaths jsonb NOT NULL DEFAULT '{}'::jsonb;
            """,
            reverse_sql="""
            ALTER TABLE dose_passthroughendpoint DROP COLUMN IF EXISTS discovered_subpaths;
            """,
        ),
    ]
