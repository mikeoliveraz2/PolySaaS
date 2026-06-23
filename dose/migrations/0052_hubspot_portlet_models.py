# Generated manually for HubSpot User Context Manager models

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0051_alter_remaining_tenant_slug_columns_to_varchar'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HubSpotPortletDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey(blank=True, db_column='tenant_slug', help_text='Tenant this record belongs to (for multi-tenant data isolation, FK to slug)', null=True, on_delete=django.db.models.deletion.CASCADE, to='dose.tenant', to_field='slug')),
                ('slug', models.SlugField(max_length=64)),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, default='')),
                ('hubspot_object_type', models.CharField(blank=True, default='', max_length=64)),
                ('executescript', models.CharField(blank=True, default='', max_length=120)),
                ('default_config', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('default_sort_order', models.PositiveIntegerField(default=100)),
                ('icon', models.CharField(blank=True, default='📊', max_length=32)),
            ],
            options={
                'verbose_name': 'HubSpot portlet definition',
                'verbose_name_plural': 'HubSpot portlet definitions',
                'ordering': ['default_sort_order', 'slug'],
                'unique_together': {('tenant', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='UserHubSpotPortlet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey(blank=True, db_column='tenant_slug', help_text='Tenant this record belongs to (for multi-tenant data isolation, FK to slug)', null=True, on_delete=django.db.models.deletion.CASCADE, to='dose.tenant', to_field='slug')),
                ('sort_order', models.PositiveIntegerField(default=100)),
                ('is_visible', models.BooleanField(default=True)),
                ('column_span', models.PositiveSmallIntegerField(default=1)),
                ('config_json', models.JSONField(blank=True, default=dict)),
                ('definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_layouts', to='dose.hubspotportletdefinition')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User HubSpot portlet',
                'verbose_name_plural': 'User HubSpot portlets',
                'ordering': ['sort_order', 'id'],
                'unique_together': {('tenant', 'user', 'definition')},
            },
        ),
    ]
