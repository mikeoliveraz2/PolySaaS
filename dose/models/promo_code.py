"""
Promo Code model for subscription discounts.
Integrates with Stripe for discount application.
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class PromoCode(models.Model):
    """
    Represents a promo/discount code that can be applied to subscriptions.
    Supports both percentage-based and fixed-amount discounts.
    Integrates with Stripe coupon codes.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Off'),
        ('fixed', 'Fixed Amount Off ($)'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Code that users enter (e.g., 'EARLY', 'BUILDER'). Case-insensitive in DB.",
        db_index=True,
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable description (e.g., 'Early Adopter 20% discount')",
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        help_text="Percentage-based or fixed dollar amount discount",
    )
    discount_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Discount amount (% if percentage, $ if fixed amount)",
    )
    stripe_coupon_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Stripe Coupon ID for applying discount (auto-synced or manual)",
        unique=True,
    )
    max_uses = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        help_text="Maximum number of times code can be used. Leave blank for unlimited.",
    )
    current_uses = models.IntegerField(
        default=0,
        help_text="Current number of times code has been used",
    )
    valid_from = models.DateTimeField(
        default=timezone.now,
        help_text="Date/time when promo code becomes active",
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date/time when promo code expires (leave blank for no expiry)",
    )
    applicable_plans = models.JSONField(
        default=list,
        blank=True,
        help_text="List of plan tiers this code applies to (leave empty for all plans)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this promo code",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code.upper()} ({self.get_discount_type_display()}: {self.discount_value})"

    def clean(self):
        """Validate promo code constraints."""
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError(
                "Expiry date must be after valid_from date."
            )
        if self.max_uses is not None and self.max_uses < 1:
            raise ValidationError(
                "Max uses must be at least 1 or blank (unlimited)."
            )
        if self.discount_value < 0:
            raise ValidationError(
                "Discount value must be positive."
            )
        if self.discount_type == 'percentage' and self.discount_value > 100:
            raise ValidationError(
                "Percentage discount cannot exceed 100%."
            )

    def save(self, *args, **kwargs):
        self.clean()
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if promo code has expired."""
        now = timezone.now()
        if self.valid_until and now > self.valid_until:
            return True
        return False

    def is_valid_now(self):
        """Check if promo code is currently valid (active, not expired, not exhausted)."""
        now = timezone.now()
        
        if not self.is_active:
            return False, "Promo code is not active"
        
        if now < self.valid_from:
            return False, "Promo code is not yet valid"
        
        if self.is_expired():
            return False, "Promo code has expired"
        
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False, "Promo code usage limit reached"
        
        return True, "Valid"

    def can_apply_to_plan(self, plan_tier):
        """
        Check if this promo code can be applied to a specific plan tier.
        If applicable_plans is empty, code works on all plans.
        """
        if not self.applicable_plans:
            return True
        return plan_tier in self.applicable_plans

    def calculate_discount(self, original_amount):
        """
        Calculate the discount amount based on original price.
        
        Args:
            original_amount: Float/Decimal of original price
        
        Returns:
            Decimal: Discount amount in dollars
        """
        from decimal import Decimal
        original = Decimal(str(original_amount))
        discount_val = Decimal(str(self.discount_value))
        
        if self.discount_type == 'percentage':
            return (original * discount_val) / Decimal('100')
        else:  # fixed
            return discount_val

    def increment_uses(self):
        """Increment the use counter for this promo code."""
        self.current_uses = (self.current_uses or 0) + 1
        self.save(update_fields=['current_uses', 'updated_at'])

    def get_stripe_coupon_create_params(self):
        """
        Generate parameters for creating a Stripe coupon.
        Returns dict suitable for stripe.Coupon.create().
        """
        params = {
            'id': self.stripe_coupon_id or self.code.upper(),
            'duration': 'forever',  # Or 'repeating' if you want monthly caps
        }
        
        if self.discount_type == 'percentage':
            params['percent_off'] = int(self.discount_value)
        else:  # fixed
            params['amount_off'] = int(self.discount_value * 100)  # Stripe uses cents
            params['currency'] = 'usd'
        
        if self.max_uses:
            params['max_redemptions'] = self.max_uses
        
        return params
