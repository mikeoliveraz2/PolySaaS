# Generated manually for mailbox topic + dead_letter retention pattern

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0063_endpoint_bookmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhookmailbox',
            name='topic',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text='MQ/routing topic (e.g. RES.odoo.action-384.user)',
                max_length=500,
            ),
        ),
        migrations.AlterField(
            model_name='webhookmailbox',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('claimed', 'Claimed'),
                    ('processed', 'Processed'),
                    ('failed', 'Failed'),
                    ('expired', 'Expired'),
                    ('dead_letter', 'Dead letter'),
                ],
                db_index=True,
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AlterModelOptions(
            name='webhookmailbox',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Webhook mailbox',
                'verbose_name_plural': 'Webhook mailboxes',
            },
        ),
    ]
