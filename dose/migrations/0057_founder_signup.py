# Generated migration for FounderSignup model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dose', '0056_subscription_user_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='FounderSignup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=255)),
                ('company_slug', models.SlugField(db_index=True, max_length=50, unique=True)),
                ('admin_username', models.CharField(max_length=150)),
                ('admin_email', models.EmailField(max_length=254)),
                ('lemon_squeezy_order_id', models.CharField(blank=True, db_index=True, max_length=128, null=True, help_text='Lemon Squeezy order ID from webhook')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Payment'),
                        ('completed', 'Payment Completed'),
                        ('provisioned', 'Tenant Provisioned'),
                        ('failed', 'Failed'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment_completed_at', models.DateTimeField(blank=True, null=True)),
                ('admin_user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='founder_admin_for', to=settings.AUTH_USER_MODEL, help_text='Auto-created admin user for the tenant')),
                ('tenant', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='founder_signup', to='dose.tenant')),
            ],
            options={
                'verbose_name': 'Founder Signup',
                'verbose_name_plural': 'Founder Signups',
                'ordering': ['-created_at'],
            },
        ),
    ]
