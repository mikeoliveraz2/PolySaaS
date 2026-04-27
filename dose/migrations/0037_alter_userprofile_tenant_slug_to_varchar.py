from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('dose', '0036_remove_trafficlog_user_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE dose_userprofile
                ALTER COLUMN tenant_slug TYPE varchar(50) USING tenant_slug::varchar(50);
            """,
            reverse_sql="""
                ALTER TABLE dose_userprofile
                ALTER COLUMN tenant_slug TYPE bigint USING tenant_slug::bigint;
            """
        ),
    ]
