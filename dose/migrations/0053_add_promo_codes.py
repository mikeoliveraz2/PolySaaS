# Generated migration for PromoCode model and Subscription updates
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0052_hubspot_portlet_models'),
    ]

    operations = [
        # Create PromoCode model
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, help_text="Code that users enter (e.g., 'EARLY', 'BUILDER'). Case-insensitive in DB.", max_length=50, unique=True)),
                ('description', models.CharField(blank=True, help_text='Human-readable description (e.g., \'Early Adopter 20% discount\')', max_length=255)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage Off'), ('fixed', 'Fixed Amount Off ($)')], default='percentage', help_text='Percentage-based or fixed dollar amount discount', max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='Discount amount (% if percentage, $ if fixed amount)', max_digits=8)),
                ('stripe_coupon_id', models.CharField(blank=True, help_text='Stripe Coupon ID for applying discount (auto-synced or manual)', max_length=128, null=True, unique=True)),
                ('max_uses', models.IntegerField(blank=True, default=None, help_text='Maximum number of times code can be used. Leave blank for unlimited.', null=True)),
                ('current_uses', models.IntegerField(default=0, help_text='Current number of times code has been used')),
                ('valid_from', models.DateTimeField(default=django.utils.timezone.now, help_text='Date/time when promo code becomes active')),
                ('valid_until', models.DateTimeField(blank=True, help_text='Date/time when promo code expires (leave blank for no expiry)', null=True)),
                ('applicable_plans', models.JSONField(blank=True, default=list, help_text='List of plan tiers this code applies to (leave empty for all plans)')),
                ('is_active', models.BooleanField(default=True, help_text='Enable/disable this promo code')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Promo Code',
                'verbose_name_plural': 'Promo Codes',
            },
        ),
        # Add promo_code and discount fields to Subscription
        migrations.AddField(
            model_name='subscription',
            name='promo_code',
            field=models.ForeignKey(blank=True, help_text='Promo code applied to this subscription', null=True, on_delete=django.db.models.deletion.SET_NULL, to='dose.promocode'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Discount amount in dollars applied to first invoice', max_digits=10),
        ),
    ]
