# Generated manually — proxy model only (no new tables).

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dose', '0066_topic_report_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='CapturedTopic',
            fields=[],
            options={
                'verbose_name': 'Captured Topic',
                'verbose_name_plural': 'Captured Topics',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('dose.webhookmailbox',),
        ),
    ]
