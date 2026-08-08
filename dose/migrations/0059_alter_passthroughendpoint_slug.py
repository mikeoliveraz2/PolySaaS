from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dose", "0058_subscription_free_period_ends_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="passthroughendpoint",
            name="slug",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Optional application label. Passthrough routing does not use this field; "
                    "the endpoint_url record is the sole source of truth."
                ),
                max_length=100,
            ),
        ),
    ]