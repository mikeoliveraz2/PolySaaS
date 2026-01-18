from django.db import models
from .tenant import Tenant

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Tenant this record belongs to (for multi-tenant data isolation)"
    )
    class Meta:
        abstract = True
