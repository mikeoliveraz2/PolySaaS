"""
Founder Beta Circle signup and order tracking model.
Stores founder application details and Lemon Squeezy order linkage.
"""
from django.db import models
from django.contrib.auth import get_user_model
from .tenant import Tenant


User = get_user_model()


class FounderSignup(models.Model):
    """
    Tracks founder beta circle applications and payments via Lemon Squeezy.
    One signup per company/tenant.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('completed', 'Payment Completed'),
        ('provisioned', 'Tenant Provisioned'),
        ('failed', 'Failed'),
    ]

    # Application info
    company_name = models.CharField(max_length=255)
    company_slug = models.SlugField(max_length=50, unique=True, db_index=True)
    admin_username = models.CharField(max_length=150)
    admin_email = models.EmailField()
    
    # Payment tracking
    lemon_squeezy_order_id = models.CharField(
        max_length=128, 
        blank=True, 
        null=True,
        db_index=True,
        help_text="Lemon Squeezy order ID from webhook"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    
    # Tenant linkage (populated after successful provisioning)
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='founder_signup'
    )
    admin_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='founder_admin_for',
        help_text="Auto-created admin user for the tenant"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Founder Signup'
        verbose_name_plural = 'Founder Signups'

    def __str__(self):
        return f"{self.company_name} ({self.company_slug}) - {self.get_status_display()}"

    def mark_payment_completed(self, order_id):
        """Called when Lemon Squeezy webhook confirms payment."""
        from django.utils import timezone
        self.status = 'completed'
        self.lemon_squeezy_order_id = order_id
        self.payment_completed_at = timezone.now()
        self.save()

    def mark_provisioned(self, tenant, admin_user):
        """Called after successful tenant + subscriptions provisioning."""
        self.status = 'provisioned'
        self.tenant = tenant
        self.admin_user = admin_user
        self.save()

    def mark_failed(self):
        """Mark this signup as failed."""
        self.status = 'failed'
        self.save()
