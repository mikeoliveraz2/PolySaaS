from django.db import models
from .tenant import Tenant
from .tenant_aware_model import TenantAwareModel

class Subscription(TenantAwareModel):
    PLAN_TIER_CHOICES = [
        ('polysaas-1', 'PolySaaS-1 (1 app)'),
        ('polysaas-3', 'PolySaaS-3 (3 apps)'),
        ('polysaas-unlimited', 'PolySaaS-Unlimited'),
    ]

    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE)
    plan_tier = models.CharField(max_length=30, choices=PLAN_TIER_CHOICES, default='polysaas-1')
    stripe_customer_id = models.CharField(max_length=128, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=128, blank=True, null=True)
    card_name = models.CharField(max_length=128, blank=True, null=True, help_text="Name on card")
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription for {self.tenant} ({self.get_plan_tier_display()}, Active: {self.active})"

    def is_active(self):
        return self.active

    def mark_active(self):
        self.active = True
        self.save()

    def mark_inactive(self):
        self.active = False
        self.save()

    def get_max_apps(self):
        from django.conf import settings
        return settings.PLAN_MAX_APPS.get(self.plan_tier)

    def can_add_app(self):
        max_apps = self.get_max_apps()
        if max_apps is None:
            return True
        from dose.models.tenant_app import TenantApp
        current_count = TenantApp.objects.filter(tenant=self.tenant).count()
        return current_count < max_apps

    def get_price_per_user(self):
        from django.conf import settings
        return settings.PLAN_PRICES.get(self.plan_tier, 29.99)
