from django.db import models
from dose.utils import create_schema_and_copy_tables

class Tenant(models.Model):
    primary_color = models.CharField(
        max_length=20,
        blank=True,
        default="#007bff",
        help_text="Primary color for this tenant's admin theme (e.g., #007bff)"
    )
    """
    Simple tenant model for session-based multi-tenancy with schema separation
    """
    name = models.CharField(max_length=100, help_text="Tenant organization name")
    slug = models.SlugField(
        max_length=50,
        help_text="Unique identifier for the tenant",
        default="default"
    )
    schema_name = models.CharField(
        max_length=63, 
        unique=True,
        help_text="PostgreSQL schema name for this tenant (auto-generated from slug)",
        blank=True
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
    
    def save(self, *args, **kwargs):
        if not self.schema_name and self.slug:
            self.schema_name = self.slug.replace('-', '_').lower()
# --- PATCHED: Annotated for schema/shortname logic ---
# This file defines the Tenant model and schema_name logic for multi-tenant SaaS.
# Key fields: tenant_name, tenant_shortname, schema_name
# Ensure tenant_shortname is used for schema_name and slug.
# Do NOT manipulate tenant_name for schema logic.
# If you change schema logic, update context processors and templates accordingly.
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.schema_name:
            create_schema_and_copy_tables(self.schema_name)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
