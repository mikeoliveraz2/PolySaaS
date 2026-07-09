from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0055_alter_promocode_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='user_count',
            field=models.PositiveIntegerField(default=1, help_text='Number of paid users included in this subscription'),
        ),
    ]