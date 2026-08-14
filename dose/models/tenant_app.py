from django.apps import apps
from django.db import models


class TenantApp(models.Model):
    """
    Tracks which apps are provisioned for each tenant, with their OAuth2 config.

    Tenant-owned data — lives ONLY in the tenant's own schema, never in public
    (see .cursor/rules/tenant-isolation.mdc). Always look this up with search_path
    set to the tenant's schema, e.g. dose.tenant_app_lookup.tenant_schema_search_path.
    A "public_bundles" manager that forced search_path=public used to exist here;
    it was removed 2026-07-30 because it leaked tenant credentials (Odoo/Mattermost
    passwords, tokens, session ids) across every tenant. Do not re-add it.
    """

    APP_CHOICES = [
        ('mattermost', 'Mattermost'),
        ('odoo', 'Odoo'),
        ('nextcloud', 'Nextcloud'),
        ('dolibarr', 'Dolibarr'),
        ('wordpress', 'WordPress'),
        ('liferay', 'Liferay'),
        ('monitor_logger', 'Monitor Logger'),
        ('polysysmon', 'PolySysMon'),
        ('hubspot', 'HubSpot'),
        ('slack', 'Slack'),
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
    if apps.is_installed('oauth2_provider'):
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
    extra_config = models.JSONField(blank=True, default=dict, help_text='App-specific config (tokens, team IDs, etc.)')

    objects = models.Manager()

    class Meta:
        unique_together = ('tenant', 'app_name')
        verbose_name = 'Tenant App'
        verbose_name_plural = 'Tenant Apps'

    def __str__(self):
        return f"{self.tenant.name} — {self.get_app_name_display()} ({self.status})"
