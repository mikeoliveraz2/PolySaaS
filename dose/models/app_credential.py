from django.db import models

class AppCredential(models.Model):
    """Stores admin credentials for passthrough apps so the dashboard card stays current."""
    app_name = models.CharField(max_length=50, unique=True, help_text="e.g. odoo, nextcloud, dolibarr")
    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True, help_text="Optional direct login URL")
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['app_name']

    def __str__(self):
        return f"{self.app_name} — {self.username or 'no user'}"
