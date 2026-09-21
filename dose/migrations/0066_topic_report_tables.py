# Topic report tables — permanent store after Consume drains a typed topic.

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0065_webhookmailbox_drop_tenant_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryProductReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(db_index=True, max_length=500)),
                ('source_event_id', models.CharField(db_index=True, max_length=64)),
                ('source_mailbox_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('odoo_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('default_code', models.CharField(blank=True, default='', max_length=128)),
                ('list_price', models.DecimalField(blank=True, decimal_places=4, max_digits=16, null=True)),
                ('raw_record', models.JSONField(blank=True, default=dict)),
                ('consumed_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Inventory product (report)',
                'verbose_name_plural': 'Inventory products (report)',
                'db_table': 'report_inventory_product',
                'ordering': ['-consumed_at', '-id'],
                'indexes': [models.Index(fields=['topic', 'consumed_at'], name='inv_prod_topic_idx')],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceEquipmentReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(db_index=True, max_length=500)),
                ('source_event_id', models.CharField(db_index=True, max_length=64)),
                ('source_mailbox_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('equipment_name', models.CharField(blank=True, default='', max_length=255)),
                ('serial_no', models.CharField(blank=True, db_index=True, default='', max_length=128)),
                ('category', models.CharField(blank=True, default='', max_length=128)),
                ('anomaly', models.BooleanField(default=False)),
                ('request_name', models.CharField(blank=True, default='', max_length=255)),
                ('raw_record', models.JSONField(blank=True, default=dict)),
                ('consumed_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Maintenance equipment (report)',
                'verbose_name_plural': 'Maintenance equipment (report)',
                'db_table': 'report_maintenance_equipment',
                'ordering': ['-consumed_at', '-id'],
                'indexes': [models.Index(fields=['topic', 'consumed_at'], name='maint_eq_topic_idx')],
            },
        ),
        migrations.CreateModel(
            name='SnmpTelemetryReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(db_index=True, max_length=500)),
                ('source_event_id', models.CharField(db_index=True, max_length=64)),
                ('source_mailbox_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('device_mac', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('device_name', models.CharField(blank=True, default='', max_length=255)),
                ('ip_address', models.CharField(blank=True, default='', max_length=64)),
                ('status', models.CharField(blank=True, default='', max_length=32)),
                ('cpu_utilization', models.FloatField(blank=True, null=True)),
                ('temperature_c', models.FloatField(blank=True, null=True)),
                ('raw_record', models.JSONField(blank=True, default=dict)),
                ('consumed_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'SNMP telemetry (report)',
                'verbose_name_plural': 'SNMP telemetry (report)',
                'db_table': 'report_snmp_telemetry',
                'ordering': ['-consumed_at', '-id'],
                'indexes': [
                    models.Index(fields=['topic', 'consumed_at'], name='snmp_tel_topic_idx'),
                    models.Index(fields=['device_mac', 'consumed_at'], name='snmp_tel_mac_idx'),
                ],
            },
        ),
    ]
