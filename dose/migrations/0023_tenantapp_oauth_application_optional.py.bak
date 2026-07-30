# Optional: adds oauth_application FK only when django-oauth-toolkit is installed.
# No dependency on oauth2_provider so this migration loads when the app is not installed.

from django.apps import apps as live_apps
from django.db import connection, migrations


def add_oauth_application_column_if_installed(apps, schema_editor):
    if not live_apps.is_installed('oauth2_provider'):
        return
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'dose_tenantapp' AND column_name = 'oauth_application_id'
        """)
        if cursor.fetchone():
            return
        cursor.execute("""
            ALTER TABLE dose_tenantapp
            ADD COLUMN oauth_application_id integer NULL UNIQUE
            REFERENCES oauth2_provider_application(id) ON DELETE SET NULL
        """)


def remove_oauth_application_column_if_installed(apps, schema_editor):
    if not live_apps.is_installed('oauth2_provider'):
        return
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'dose_tenantapp' AND column_name = 'oauth_application_id'
        """)
        if not cursor.fetchone():
            return
        cursor.execute("ALTER TABLE dose_tenantapp DROP COLUMN IF EXISTS oauth_application_id")


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0022_tenantapp'),
    ]

    operations = [
        migrations.RunPython(add_oauth_application_column_if_installed, remove_oauth_application_column_if_installed),
    ]
