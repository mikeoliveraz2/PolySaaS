# Generated manually to add user scoping to NavigationItem
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dose', '0008_remove_passthroughendpoint_trigger_path_length'),
    ]

    operations = [
        # Add created_by_user field
        migrations.AddField(
            model_name='navigationitem',
            name='created_by_user',
            field=models.ForeignKey(
                blank=True,
                help_text="If set, this is a personal bookmark visible only to this user. If null, it's a tenant-wide item (admin-created).",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='personal_navigation_items',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add is_personal field
        migrations.AddField(
            model_name='navigationitem',
            name='is_personal',
            field=models.BooleanField(
                default=False,
                help_text='True = personal user bookmark, False = tenant-wide admin item'
            ),
        ),
        # Change target default from _self to _blank
        migrations.AlterField(
            model_name='navigationitem',
            name='target',
            field=models.CharField(
                choices=[
                    ('_self', 'Same Window/Tab'),
                    ('_blank', 'New Window/Tab'),
                    ('_parent', 'Parent Frame'),
                    ('modal', 'Modal Dialog'),
                    ('iframe', 'Embedded Frame')
                ],
                default='_blank',
                help_text='How the link should open (default: new window)',
                max_length=10
            ),
        ),
    ]
