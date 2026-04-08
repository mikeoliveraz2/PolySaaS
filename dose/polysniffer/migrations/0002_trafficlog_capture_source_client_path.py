# Generated manually for passthrough vs browser capture filtering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polysniffer", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="trafficlog",
            name="capture_source",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="passthrough = logged by forward_request_standardized; browser_extension = extension/silent-capture",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="trafficlog",
            name="client_path",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Django path_info for passthrough requests; empty for native-only captures",
                max_length=500,
            ),
        ),
    ]
