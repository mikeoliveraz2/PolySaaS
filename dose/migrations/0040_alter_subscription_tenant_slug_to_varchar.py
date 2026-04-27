from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("dose", "0039_alter_subscription_tenant"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE dose_subscription ALTER COLUMN tenant_slug TYPE varchar(255) USING tenant_slug::varchar;",
            reverse_sql="ALTER TABLE dose_subscription ALTER COLUMN tenant_slug TYPE bigint USING tenant_slug::bigint;",
        ),
    ]
