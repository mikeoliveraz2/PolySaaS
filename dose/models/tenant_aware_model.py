from django.db import models
from .tenant import Tenant

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(
        'Tenant',
        to_field='slug',
        db_column='tenant_slug',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Tenant this record belongs to (for multi-tenant data isolation, FK to slug)"
    )
    class Meta:
        abstract = True
