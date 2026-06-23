"""HubSpot User Context Manager — portlet catalog and per-user layout."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from .tenant_aware_model import TenantAwareModel

User = get_user_model()


class HubSpotPortletDefinition(TenantAwareModel):
    """Catalog of HubSpot feature portlets available in the User Context Manager."""

    slug = models.SlugField(max_length=64)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True, default='')
    hubspot_object_type = models.CharField(max_length=64, blank=True, default='')
    executescript = models.CharField(max_length=120, blank=True, default='')
    default_config = models.JSONField(blank=True, default=dict)
    is_active = models.BooleanField(default=True)
    default_sort_order = models.PositiveIntegerField(default=100)
    icon = models.CharField(max_length=32, blank=True, default='📊')

    class Meta:
        ordering = ['default_sort_order', 'slug']
        unique_together = ('tenant', 'slug')
        verbose_name = 'HubSpot portlet definition'
        verbose_name_plural = 'HubSpot portlet definitions'

    def __str__(self):
        return f'{self.title} ({self.slug})'


class UserHubSpotPortlet(TenantAwareModel):
    """Per-user portlet visibility, priority, and layout."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    definition = models.ForeignKey(
        HubSpotPortletDefinition,
        on_delete=models.CASCADE,
        related_name='user_layouts',
    )
    sort_order = models.PositiveIntegerField(default=100)
    is_visible = models.BooleanField(default=True)
    column_span = models.PositiveSmallIntegerField(default=1)
    config_json = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ['sort_order', 'id']
        unique_together = ('tenant', 'user', 'definition')
        verbose_name = 'User HubSpot portlet'
        verbose_name_plural = 'User HubSpot portlets'

    def __str__(self):
        return f'{self.user_id} — {self.definition.slug} (#{self.sort_order})'
