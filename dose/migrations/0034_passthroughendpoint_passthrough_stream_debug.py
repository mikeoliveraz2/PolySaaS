# PassThroughEndpoint: optional passthrough stream diagnostics flag

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0033_add_extra_config_to_tenantapp"),
    ]

    operations = [
        migrations.AddField(
            model_name="passthroughendpoint",
            name="passthrough_stream_debug",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "If True, log passthrough stream diagnostics to the server console. "
                    "Or set POLYSNIFFER_PASSTHROUGH_DEBUG in settings for all endpoints."
                ),
            ),
        ),
    ]
