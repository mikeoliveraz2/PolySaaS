# Generated migration for PassThroughEndpoint detected_base_url and detected_subpaths fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0006_passthroughendpoint_trigger_path_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='passthroughendpoint',
            name='detected_base_url',
            field=models.URLField(blank=True, help_text='Auto-detected base URL (scheme + domain, e.g., https://example.cloud)', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='passthroughendpoint',
            name='detected_subpaths',
            field=models.JSONField(blank=True, default=list, help_text="Auto-detected subpaths from endpoint_url (e.g., ['scp', 'dashboard.php'])", null=True),
        ),
    ]
