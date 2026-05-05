from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('dose', '0037_alter_userprofile_tenant_slug_to_varchar'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'user_tenant_memberships'
                        AND column_name = 'tenant_id'
                        AND data_type = 'bigint'
                    ) THEN
                        ALTER TABLE user_tenant_memberships
                        ALTER COLUMN tenant_id TYPE varchar(50) USING tenant_id::varchar(50);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'user_tenant_memberships'
                        AND column_name = 'tenant_id'
                        AND data_type = 'character varying'
                    ) THEN
                        ALTER TABLE user_tenant_memberships
                        ALTER COLUMN tenant_id TYPE bigint USING tenant_id::bigint;
                    END IF;
                END $$;
            """
        ),
    ]
