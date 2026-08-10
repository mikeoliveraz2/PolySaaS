# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# ROUTE IDENTITY SUPERSEDED 2026-08-09: unique endpoint_url only; no ID/offset or slug routing.
# BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02 — see documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md
from django.db import models

class PassThroughEndpoint(models.Model):
    PROVIDER_CHOICES = [
        ('github', 'GitHub'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('custom', 'Custom'),
    ]

    PASSTHROUGH_TYPE_CHOICES = [
        ('api', 'API - REST/GraphQL endpoints (e.g., Gmail API)'),
        ('scraper', 'Scraper - HTML screen scraping (e.g., Nextcloud)'),
    ]

    INTEGRATION_MODE_CHOICES = [
        ('web_only', 'Web UI Only - No API'),
        ('web_api', 'Web UI + API - Both available (e.g., Gmail)'),
        ('api_only', 'API Only - Custom Dose UI via atomic services'),
    ]

    AUTH_TYPE_CHOICES = [
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Auth (base64)'),
        ('api_key', 'API Key (custom header)'),
        ('oauth2', 'OAuth2'),
    ]

    is_enabled = models.BooleanField(default=True, help_text="Enable or disable passthrough for this endpoint")
    bypass_middleware = models.BooleanField(
        default=False,
        help_text="If True, this endpoint will NOT be processed by passthrough middleware (use for dedicated views like Gmail that handle their own routing)"
    )
    starting_uri = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Starting URI path for this endpoint (e.g., /web for Odoo, / for Mattermost)"
    )
    passthrough_type = models.CharField(
        max_length=20,
        choices=PASSTHROUGH_TYPE_CHOICES,
        default='scraper',
        help_text="Type of passthrough: 'api' for REST APIs (Gmail), 'scraper' for HTML content"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='custom', help_text="OAuth2 provider or passthrough method")
    endpoint_url = models.CharField(
        max_length=300,
        unique=True,
        help_text=(
            "Unique canonical URL for this tenant endpoint and the sole source "
            "of passthrough identity"
        ),
    )
    description = models.CharField(max_length=200, blank=True, default="", help_text="Description or purpose of this endpoint")
    created_at = models.DateTimeField(auto_now_add=True)
    # Legacy metadata only. Passthrough identity is always endpoint_url's host.
    slug = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=(
            "Optional application label. Passthrough routing does not use this field; "
            "the endpoint_url record is the sole source of truth."
        ),
    )
    discovered_subpaths = models.JSONField(default=dict, blank=True, help_text="Auto-discovered subpaths for this endpoint")

    # Menu Integration Fields
    show_in_menu = models.BooleanField(
        default=True,
        help_text="Show this passthrough endpoint as a menu item in the top navigation"
    )
    menu_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Title to display in the menu (defaults to extracted title from description or URL)"
    )
    menu_icon = models.CharField(
        max_length=100,
        blank=True,
        default="🔗",
        help_text="Icon to display in the menu (emoji, Font Awesome class, etc.)"
    )
    menu_sort_order = models.PositiveIntegerField(
        default=100,
        help_text="Sort order for menu display (lower numbers appear first)"
    )

    # Integration Configuration
    integration_mode = models.CharField(
        max_length=20,
        choices=INTEGRATION_MODE_CHOICES,
        default='web_only',
        help_text="How this service integrates: web UI only, web UI + API, or API only"
    )

    # API Configuration (optional, depends on integration_mode)
    api_endpoint = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="API base URL for programmatic access (e.g., https://api.gmail.com/v1 or http://service-name:port)"
    )
    api_auth_type = models.CharField(
        max_length=20,
        choices=AUTH_TYPE_CHOICES,
        default='bearer',
        help_text="API authentication method"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="API key or token (encrypted storage recommended for production)"
    )
    api_key_header = models.CharField(
        max_length=100,
        blank=True,
        default="Authorization",
        help_text="Header name for API key (e.g., 'Authorization', 'X-API-Key')"
    )

    # Credentials for auto-login (simple auth, future: OAuth2)
    # TODO: Migrate to OAuth2 for multi-user support (future enhancement)
    auth_username = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Username for auto-login (e.g., Odoo email). NOTE: For demo only - future use OAuth2 for multi-user support"
    )
    auth_password = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Password for auto-login (encrypted storage recommended). NOTE: For demo only - future use OAuth2"
    )

    # SPA/JavaScript Configuration
    inject_proxy_script = models.BooleanField(
        default=False,
        help_text="If True, inject PolySaaS API interceptor script to capture XHR/Fetch calls from SPAs (e.g., Airtable, Notion)"
    )
    passthrough_stream_debug = models.BooleanField(
        default=False,
        help_text=(
            "If True, log passthrough stream diagnostics (upstream + final HTML snippets, "
            "asset URLs, Set-Cookie samples) to the server console. Or set "
            "POLYSNIFFER_PASSTHROUGH_DEBUG in settings for all endpoints."
        ),
    )

    def __str__(self):

        return f"Endpoint: {self.endpoint_url}"

    def get_menu_title(self):
        """Get the title to use in the menu, with fallback logic"""
        if self.menu_title:
            return self.menu_title
        elif self.description:
            return self.description
        else:
            # Fallback to domain from URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.endpoint_url)
                domain = parsed.netloc.replace('www.', '')
                return domain.split('.')[0].title()
            except:
                return "External Service"

    def get_proxy_prefix(self, surface: str = "admin") -> str:
        """Return /pt/<surface>/<host> derived only from the stored endpoint_url."""
        from urllib.parse import urlparse

        if surface not in ("admin", "dose"):
            raise ValueError("Passthrough surface must be 'admin' or 'dose'")
        host = (urlparse(self.endpoint_url or "").netloc or "").strip()
        prefix = f"/pt/{surface}"
        return f"{prefix}/{host}" if host else prefix

    def get_menu_url(self, surface: str = "admin"):
        """Return /pt/<surface>/<host>/<starting_uri> without changing endpoint_url."""
        prefix = self.get_proxy_prefix(surface).rstrip("/")
        if prefix == f"/pt/{surface}":
            return "/"
        start = (self.starting_uri or "").strip()
        if start and start not in ("/", ""):
            if not start.startswith("/"):
                start = f"/{start}"
            return f"{prefix}{start}"
        return f"{prefix}/"

    def clean(self):
        """Validate the model fields"""
        from django.core.exceptions import ValidationError
        errors = {}

        if self.show_in_menu:
            if not self.endpoint_url:
                errors['endpoint_url'] = "Endpoint URL is required when 'Show in menu' is enabled"
            else:
                from urllib.parse import urlparse
                if not urlparse(self.endpoint_url).netloc:
                    errors['endpoint_url'] = "Endpoint URL must include a scheme and host"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        # Run model validation
        self.full_clean()

        super().save(*args, **kwargs)

