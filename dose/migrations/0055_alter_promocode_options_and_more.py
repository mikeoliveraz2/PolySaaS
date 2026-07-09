import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0054_subscription_billing_method'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='promocode',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Promo Code',
                'verbose_name_plural': 'Promo Codes',
            },
        ),
        migrations.AlterField(
            model_name='hubspotportletdefinition',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='tenant_slug',
                help_text='Tenant this record belongs to (for multi-tenant data isolation, FK to slug)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='dose.tenant',
            ),
        ),
        migrations.AlterField(
            model_name='promocode',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tenantapp',
            name='app_name',
            field=models.CharField(
                choices=[
                    ('mattermost', 'Mattermost'),
                    ('odoo', 'Odoo'),
                    ('nextcloud', 'Nextcloud'),
                    ('dolibarr', 'Dolibarr'),
                    ('wordpress', 'WordPress'),
                    ('liferay', 'Liferay'),
                    ('monitor_logger', 'Monitor Logger'),
                    ('polysysmon', 'PolySysMon'),
                    ('hubspot', 'HubSpot'),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='userhubspotportlet',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='tenant_slug',
                help_text='Tenant this record belongs to (for multi-tenant data isolation, FK to slug)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='dose.tenant',
            ),
        ),
    ]