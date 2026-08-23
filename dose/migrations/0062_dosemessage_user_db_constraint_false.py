# Generated manually for tenant-safe DoseMessage user references.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def drop_dosemessage_user_fk(apps, schema_editor):
    """Drop physical FKs so public User PKs can be stored in tenant schemas."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.conname
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = current_schema()
              AND t.relname = 'dose_dosemessage'
              AND c.contype = 'f'
              AND pg_get_constraintdef(c.oid) ILIKE '%%user_id%%'
            """
        )
        for (name,) in cursor.fetchall():
            cursor.execute(
                f'ALTER TABLE dose_dosemessage DROP CONSTRAINT IF EXISTS "{name}"'
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dose", "0061_webhook_mailbox"),
    ]

    operations = [
        migrations.RunPython(drop_dosemessage_user_fk, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dosemessage",
            name="user",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
