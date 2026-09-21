# Generated manually for ContactHistory (cross-app contact capture).

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0067_topic_history_rename"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("topic", models.CharField(db_index=True, max_length=500)),
                ("source_event_id", models.CharField(db_index=True, max_length=64)),
                (
                    "source_mailbox_id",
                    models.BigIntegerField(blank=True, db_index=True, null=True),
                ),
                (
                    "source_app",
                    models.CharField(blank=True, db_index=True, default="", max_length=32),
                ),
                (
                    "external_id",
                    models.CharField(blank=True, db_index=True, default="", max_length=128),
                ),
                ("name", models.CharField(blank=True, default="", max_length=255)),
                (
                    "email",
                    models.CharField(blank=True, db_index=True, default="", max_length=255),
                ),
                ("phone", models.CharField(blank=True, default="", max_length=64)),
                ("company", models.CharField(blank=True, default="", max_length=255)),
                ("username", models.CharField(blank=True, default="", max_length=128)),
                ("active", models.BooleanField(default=True)),
                ("raw_record", models.JSONField(blank=True, default=dict)),
                (
                    "consumed_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
            ],
            options={
                "verbose_name": "Contact (history)",
                "verbose_name_plural": "Contacts (history)",
                "db_table": "history_contact",
                "ordering": ["-consumed_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="contacthistory",
            index=models.Index(
                fields=["topic", "consumed_at"], name="contact_hist_topic_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="contacthistory",
            index=models.Index(
                fields=["source_app", "email"], name="contact_hist_app_email_idx"
            ),
        ),
    ]
