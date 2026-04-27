from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('dose', '0040_alter_subscription_tenant_slug_to_varchar'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationpanel'
                        AND column_name = 'tenant_slug'
                    ) THEN
                        ALTER TABLE dose_navigationpanel
                        ALTER COLUMN tenant_slug TYPE varchar(50) USING tenant_slug::varchar(50);
                    ELSIF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationpanel'
                        AND column_name = 'tenant_id'
                    ) THEN
                        ALTER TABLE dose_navigationpanel
                        ALTER COLUMN tenant_id TYPE varchar(50) USING tenant_id::varchar(50);
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationitem'
                        AND column_name = 'tenant_slug'
                    ) THEN
                        ALTER TABLE dose_navigationitem
                        ALTER COLUMN tenant_slug TYPE varchar(50) USING tenant_slug::varchar(50);
                    ELSIF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationitem'
                        AND column_name = 'tenant_id'
                    ) THEN
                        ALTER TABLE dose_navigationitem
                        ALTER COLUMN tenant_id TYPE varchar(50) USING tenant_id::varchar(50);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationpanel'
                        AND column_name = 'tenant_slug'
                    ) THEN
                        ALTER TABLE dose_navigationpanel
                        ALTER COLUMN tenant_slug TYPE bigint USING tenant_slug::bigint;
                    ELSIF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationpanel'
                        AND column_name = 'tenant_id'
                    ) THEN
                        ALTER TABLE dose_navigationpanel
                        ALTER COLUMN tenant_id TYPE bigint USING tenant_id::bigint;
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationitem'
                        AND column_name = 'tenant_slug'
                    ) THEN
                        ALTER TABLE dose_navigationitem
                        ALTER COLUMN tenant_slug TYPE bigint USING tenant_slug::bigint;
                    ELSIF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = current_schema()
                        AND table_name = 'dose_navigationitem'
                        AND column_name = 'tenant_id'
                    ) THEN
                        ALTER TABLE dose_navigationitem
                        ALTER COLUMN tenant_id TYPE bigint USING tenant_id::bigint;
                    END IF;
                END $$;
            """,
        ),
    ]
