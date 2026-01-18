from django.db import models
from .tenant import Tenant
from .tenant_aware_model import TenantAwareModel

class Subscription(TenantAwareModel):
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=128, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=128, blank=True, null=True)
    card_name = models.CharField(max_length=128, blank=True, null=True, help_text="Name on card")
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription for {self.tenant} (Active: {self.active})"

    def is_active(self):
        return self.active

    def mark_active(self):
        self.active = True
        self.save()

    def mark_inactive(self):
        self.active = False
        self.save()

    # Add more Stripe logic as needed
