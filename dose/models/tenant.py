from django.core.exceptions import ValidationError
from django.db import models

from dose.utils import create_schema_and_copy_tables


class Tenant(models.Model):
    slug = models.SlugField(
        max_length=50,
        primary_key=True,
        help_text="Unique identifier for the tenant (primary key)",
        default="default"
    )
    name = models.CharField(max_length=100, help_text="Tenant organization name")
    schema_name = models.CharField(
        max_length=63, 
        unique=True,
        help_text="PostgreSQL schema name for this tenant (auto-generated from slug)",
        blank=True
    )
    primary_color = models.CharField(
        max_length=20,
        blank=True,
        default="#007bff",
        help_text="Primary color for this tenant's admin theme (e.g., #007bff)"
    )
    description = models.TextField(
        blank=True, 
        default="",
        help_text="Tenant description or details"
    )
    tagline = models.CharField(
        max_length=200, 
        blank=True, 
        default="",
        help_text="Tenant tagline or slogan"
    )
    logo = models.ImageField(
        upload_to='tenant_logos/', 
        blank=True, 
        null=True,
        help_text="Tenant logo image"
    )
    created_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this tenant was created"
    )
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        from dose.management.schema_utils import tenant_schema_disallowed_reason

        sn = (self.schema_name or "").strip()
        if sn:
            msg = tenant_schema_disallowed_reason(sn)
            if msg:
                raise ValidationError({"schema_name": msg})

    def save(self, *args, **kwargs):
        # --- PATCHED: schema_name from slug; never use reserved PostgreSQL schema "public" as a tenant. ---
        if not self.schema_name and self.slug:
            self.schema_name = self.slug.replace("-", "_").lower()
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.schema_name:
            create_schema_and_copy_tables(self.schema_name)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
