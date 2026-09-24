# VendorHistory — Captured Topics Vendors family (Slice 6 two-topic design).

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0068_contact_history"),
    ]

    operations = [
        migrations.CreateModel(
            name="VendorHistory",
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
                    "odoo_vendor_id",
                    models.BigIntegerField(blank=True, db_index=True, null=True),
                ),
                (
                    "odoo_contact_id",
                    models.BigIntegerField(blank=True, null=True),
                ),
                ("name", models.CharField(blank=True, default="", max_length=255)),
                ("email", models.CharField(blank=True, default="", max_length=255)),
                ("region", models.CharField(blank=True, default="", max_length=255)),
                ("raw_record", models.JSONField(blank=True, default=dict)),
                (
                    "consumed_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
            ],
            options={
                "verbose_name": "Vendor (history)",
                "verbose_name_plural": "Vendors (history)",
                "db_table": "history_vendor",
                "ordering": ["-consumed_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="vendorhistory",
            index=models.Index(
                fields=["topic", "consumed_at"], name="vendor_hist_topic_idx"
            ),
        ),
    ]
