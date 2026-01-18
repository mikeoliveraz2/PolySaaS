from django.db import models
from .tenant_aware_model import TenantAwareModel

class IgnorePath(TenantAwareModel):
    """
    Model to define URL paths that should be ignored by the external passthrough middleware
    """
    url = models.CharField(
        max_length=500,
        help_text="URL path pattern to ignore (e.g., '/admin/', '/api/v1/*', '*.css')"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description of what this path is used for"
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional parameters or configuration in JSON format"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this ignore path is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.url} - {self.description[:50]}"
    
    class Meta:
        verbose_name = "Ignore Path"
        verbose_name_plural = "Ignore Paths"
        ordering = ['url']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['url']),
        ]
