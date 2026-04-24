from django.db import models
from django.contrib.auth import get_user_model
from .tenant import Tenant

User = get_user_model()

class UserProfile(models.Model):
    """
    Links users to tenants for session-based multi-tenancy
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, to_field='slug', db_column='tenant_slug', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    dark_mode = models.BooleanField(default=False)
    theme = models.CharField(max_length=20, default='flatly', help_text="Jazzmin/Bootswatch theme name (e.g., 'flatly', 'cyborg', 'darkly')")
    last_selected_theme = models.CharField(max_length=50, default='flatly', help_text="Last selected theme (light or dark)")
    light_theme = models.CharField(max_length=50, default='flatly', help_text="Preferred light theme")
    dark_theme = models.CharField(max_length=50, default='darkly', help_text="Preferred dark theme")
    use_system_pref = models.BooleanField(default=False, help_text="Use system preference for light/dark mode")
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
