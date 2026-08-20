from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dose", "0059_alter_passthroughendpoint_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="passthroughendpoint",
            name="endpoint_url",
            field=models.CharField(
                help_text=(
                    "Unique canonical URL for this tenant endpoint and the sole source "
                    "of passthrough identity"
                ),
                max_length=300,
                unique=True,
            ),
        ),
    ]