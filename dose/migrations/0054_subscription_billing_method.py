from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0053_add_promo_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='billing_method',
            field=models.CharField(
                choices=[('card', 'Card'), ('invoice', 'Invoice')],
                default='card',
                max_length=20,
            ),
        ),
    ]
