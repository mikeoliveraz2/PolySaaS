from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dose", "0034_passthroughendpoint_passthrough_stream_debug"),
    ]

    operations = [
        migrations.AddField(
            model_name="passthroughendpoint",
            name="slug",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Optional identifier for non–passthrough features (menus, links, other Django code). "
                    "Distinct from trigger_path, which is the URL segment for /pt/admin/<trigger>/ only. "
                    "Leave blank if unused."
                ),
                max_length=100,
            ),
        ),
    ]
