from django.db import models
from .tenant import Tenant
from .tenant_aware_model import TenantAwareModel

class Subscription(TenantAwareModel):
    PLAN_TIER_CHOICES = [
        ('starter', 'Starter (1 user)'),
        ('team', 'Team (3 users)'),
        ('unlimited', 'Unlimited'),
    ]

    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE)
    plan_tier = models.CharField(max_length=20, choices=PLAN_TIER_CHOICES, default='starter')
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

    def get_max_users(self):
        from django.conf import settings
        return settings.PLAN_MAX_USERS.get(self.plan_tier)

    def can_add_user(self):
        max_users = self.get_max_users()
        if max_users is None:
            return True
        current_count = self.tenant.userprofile_set.count()
        return current_count < max_users

    def get_price(self):
        from django.conf import settings
        return settings.PLAN_PRICES.get(self.plan_tier, 29.99)
