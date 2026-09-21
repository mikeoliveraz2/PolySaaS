# Rename report → history (tables + model names).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0066_topic_report_tables'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='InventoryProductReport',
            new_name='InventoryProductHistory',
        ),
        migrations.RenameModel(
            old_name='MaintenanceEquipmentReport',
            new_name='MaintenanceEquipmentHistory',
        ),
        migrations.RenameModel(
            old_name='SnmpTelemetryReport',
            new_name='SnmpTelemetryHistory',
        ),
        migrations.AlterModelTable(
            name='inventoryproducthistory',
            table='history_inventory_product',
        ),
        migrations.AlterModelTable(
            name='maintenanceequipmenthistory',
            table='history_maintenance_equipment',
        ),
        migrations.AlterModelTable(
            name='snmptelemetryhistory',
            table='history_snmp_telemetry',
        ),
        migrations.AlterModelOptions(
            name='inventoryproducthistory',
            options={
                'ordering': ['-consumed_at', '-id'],
                'verbose_name': 'Inventory product (history)',
                'verbose_name_plural': 'Inventory products (history)',
            },
        ),
        migrations.AlterModelOptions(
            name='maintenanceequipmenthistory',
            options={
                'ordering': ['-consumed_at', '-id'],
                'verbose_name': 'Maintenance equipment (history)',
                'verbose_name_plural': 'Maintenance equipment (history)',
            },
        ),
        migrations.AlterModelOptions(
            name='snmptelemetryhistory',
            options={
                'ordering': ['-consumed_at', '-id'],
                'verbose_name': 'SNMP telemetry (history)',
                'verbose_name_plural': 'SNMP telemetry (history)',
            },
        ),
        # Recreate indexes with history names (drop old report index names if present)
        migrations.RemoveIndex(
            model_name='inventoryproducthistory',
            name='inv_prod_topic_idx',
        ),
        migrations.RemoveIndex(
            model_name='maintenanceequipmenthistory',
            name='maint_eq_topic_idx',
        ),
        migrations.RemoveIndex(
            model_name='snmptelemetryhistory',
            name='snmp_tel_topic_idx',
        ),
        migrations.RemoveIndex(
            model_name='snmptelemetryhistory',
            name='snmp_tel_mac_idx',
        ),
        migrations.AddIndex(
            model_name='inventoryproducthistory',
            index=models.Index(fields=['topic', 'consumed_at'], name='inv_prod_hist_topic_idx'),
        ),
        migrations.AddIndex(
            model_name='maintenanceequipmenthistory',
            index=models.Index(fields=['topic', 'consumed_at'], name='maint_eq_hist_topic_idx'),
        ),
        migrations.AddIndex(
            model_name='snmptelemetryhistory',
            index=models.Index(fields=['topic', 'consumed_at'], name='snmp_tel_hist_topic_idx'),
        ),
        migrations.AddIndex(
            model_name='snmptelemetryhistory',
            index=models.Index(fields=['device_mac', 'consumed_at'], name='snmp_tel_hist_mac_idx'),
        ),
    ]
