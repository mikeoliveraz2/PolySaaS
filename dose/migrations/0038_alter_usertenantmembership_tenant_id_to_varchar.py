from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('dose', '0037_alter_userprofile_tenant_slug_to_varchar'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE user_tenant_memberships
                ALTER COLUMN tenant_id TYPE varchar(50) USING tenant_id::varchar(50);
            """,
            reverse_sql="""
                ALTER TABLE user_tenant_memberships
                ALTER COLUMN tenant_id TYPE bigint USING tenant_id::bigint;
            """
        ),
    ]
