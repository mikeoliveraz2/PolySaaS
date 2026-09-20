# Drop WebhookMailbox.tenant FK — isolation is by schema, Tenant lives in public only.
# Shadow dose_tenant tables in tenant schemas caused FK violations on insert.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0064_webhookmailbox_topic_dead_letter'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='webhookmailbox',
            unique_together=set(),
        ),
        migrations.RemoveIndex(
            model_name='webhookmailbox',
            name='mailbox_consumer_idx',
        ),
        migrations.RemoveField(
            model_name='webhookmailbox',
            name='tenant',
        ),
        migrations.AlterField(
            model_name='webhookmailbox',
            name='event_id',
            field=models.CharField(
                db_index=True,
                help_text='Stable hash for deduplication (unique within tenant schema)',
                max_length=64,
                unique=True,
            ),
        ),
        migrations.AddIndex(
            model_name='webhookmailbox',
            index=models.Index(fields=['status', 'expires_at'], name='mailbox_consumer_idx'),
        ),
    ]
