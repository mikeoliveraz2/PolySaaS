from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0057_founder_signup'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='free_period_ends_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Date/time when a promotional free access period ends',
                null=True,
            ),
        ),
    ]