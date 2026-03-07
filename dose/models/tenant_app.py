from django.db import models


class TenantApp(models.Model):
    """Tracks which apps are provisioned for each tenant, with their OAuth2 config."""

    APP_CHOICES = [
        ('mattermost', 'Mattermost'),
        ('odoo', 'Odoo'),
        ('nextcloud', 'Nextcloud'),
        ('liferay', 'Liferay'),
        ('polysysmon', 'PolySysMon'),
    ]

    STATUS_CHOICES = [
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('error', 'Error'),
        ('disabled', 'Disabled'),
    ]

    tenant = models.ForeignKey(
        'dose.Tenant',
        on_delete=models.CASCADE,
        related_name='apps',
    )
    app_name = models.CharField(max_length=50, choices=APP_CHOICES)
    app_url = models.URLField(blank=True, default='')
    oauth_application = models.OneToOneField(
        'oauth2_provider.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_app',
        help_text='The OAuth2 application registered in DOT for this tenant+app pair',
    )
    provisioned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='provisioning')
    last_error = models.TextField(blank=True, default='', help_text='Last provisioning error message')

    class Meta:
        unique_together = ('tenant', 'app_name')
        verbose_name = 'Tenant App'
        verbose_name_plural = 'Tenant Apps'

    def __str__(self):
        return f"{self.tenant.name} — {self.get_app_name_display()} ({self.status})"
