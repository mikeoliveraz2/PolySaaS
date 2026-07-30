from django.db import models
from .tenant import Tenant
from .tenant_aware_model import TenantAwareModel
from dose.services.subscription_pricing import build_subscription_pricing, get_volume_discount_percent

class Subscription(TenantAwareModel):
    PLAN_TIER_CHOICES = [
        ('polysaas-1', 'PolySaaS-1 (1 app)'),
        ('polysaas-3', 'PolySaaS-3 (3 apps)'),
        ('polysaas-unlimited', 'PolySaaS-Unlimited'),
    ]
    BILLING_METHOD_CHOICES = [
        ('card', 'Card'),
        ('invoice', 'Invoice'),
    ]

    # Use inherited tenant FK from TenantAwareModel, enforce uniqueness for one-to-one behavior
    # The unique constraint will be set in the migration
    plan_tier = models.CharField(max_length=30, choices=PLAN_TIER_CHOICES, default='polysaas-1')
    stripe_customer_id = models.CharField(max_length=128, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=128, blank=True, null=True)
    billing_method = models.CharField(max_length=20, choices=BILLING_METHOD_CHOICES, default='card')
    user_count = models.PositiveIntegerField(default=1, help_text='Number of paid users included in this subscription')
    card_name = models.CharField(max_length=128, blank=True, null=True, help_text="Name on card")
    selected_apps = models.JSONField(default=list, blank=True, help_text="App keys selected at subscribe time")
    active = models.BooleanField(default=False)
    free_period_ends_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date/time when a promotional free access period ends",
    )
    promo_code = models.ForeignKey(
        'PromoCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Promo code applied to this subscription"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Discount amount in dollars applied to first invoice"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription for {self.tenant} ({self.get_plan_tier_display()}, Active: {self.active})"

    def is_active(self):
        if self.free_period_ends_at:
            from django.utils import timezone
            if timezone.now() >= self.free_period_ends_at:
                return False
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

    def get_bundled_app_slots_used(self):
        """Sum of plan slots consumed by provisioned bundled apps (WP & PolySysMon = 2 each)."""
        from django.conf import settings
        from dose.models.tenant_app import TenantApp

        weights = getattr(settings, 'TENANT_APP_BUNDLED_SLOTS', {})
        total = 0
        for ta in TenantApp.objects.filter(tenant=self.tenant):
            total += weights.get(ta.app_name, 1)
        return total

    def can_add_app(self, slots_needed=1):
        max_apps = self.get_max_apps()
        if max_apps is None:
            return True
        return self.get_bundled_app_slots_used() + slots_needed <= max_apps

    def get_price_per_user(self):
        from django.conf import settings
        return settings.PLAN_PRICES.get(self.plan_tier, 26.00)

    def get_volume_discount_percent(self):
        return get_volume_discount_percent(self.user_count)

    def get_pricing_breakdown(self, promo_code=None):
        return build_subscription_pricing(
            self.plan_tier,
            user_count=self.user_count,
            promo_code=promo_code if promo_code is not None else self.promo_code,
        )

    def get_promo_code_info(self):
        """Return promo code details and discount amount for this subscription."""
        if not self.promo_code:
            return None
        
        return {
            'code': self.promo_code.code,
            'description': self.promo_code.description,
            'discount_type': self.promo_code.get_discount_type_display(),
            'discount_value': str(self.promo_code.discount_value),
            'discount_amount': str(self.discount_amount),
        }

    def get_discounted_price(self, base_price=None):
        """
        Calculate the discounted price after applying promo code.
        
        Args:
            base_price: Optional override for base price (uses get_price_per_user if not provided)
        
        Returns:
            Decimal: Discounted price
        """
        pricing = self.get_pricing_breakdown()
        return pricing['effective_price_per_user']
