"""
PolySniffer Models - Store captured HTTP traffic
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TrafficCapture(models.Model):
    """Named capture session for comparing native vs passthrough traffic."""
    tenant = models.ForeignKey(
        'dose.Tenant', on_delete=models.CASCADE,
        related_name='traffic_captures', null=True, blank=True
    )
    capture_name = models.CharField(max_length=120, help_text="e.g. mattermost-native-2026-05-16")
    is_active = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Traffic Capture"
        verbose_name_plural = "Traffic Captures"

    def __str__(self):
        return f"{self.capture_name} ({'ACTIVE' if self.is_active else 'inactive'})"

    def save(self, *args, **kwargs):
        if self.tenant_id:
            from dose.polysniffer.tenant_schema_fk import ensure_tenant_fk_row

            schema = getattr(self.tenant, "schema_name", None) if self.tenant else None
            ensure_tenant_fk_row(str(self.tenant_id), schema)
        if not self.expires_at or self.expires_at <= timezone.now():
            self.expires_at = timezone.now() + timezone.timedelta(hours=8)
        super().save(*args, **kwargs)


class TrafficLog(models.Model):
    """Store captured HTTP request/response pairs"""

    # How this row was recorded (for filtering PolySniffer UI)
    CAPTURE_PASSTHROUGH = "passthrough"
    CAPTURE_BROWSER_EXT = "browser_extension"
    CAPTURE_NATIVE = "native"
    CAPTURE_SOURCE_CHOICES = (
        (CAPTURE_PASSTHROUGH, "Passthrough (/pt/admin/… via Django forwarder)"),
        (CAPTURE_BROWSER_EXT, "Browser extension / silent capture JSON"),
        (CAPTURE_NATIVE, "Native / direct (server middleware)"),
    )
    capture_source = models.CharField(
        max_length=32,
        blank=True,
        default="",
        db_index=True,
        help_text="passthrough = forwarder; browser_extension = extension; native = server middleware",
    )
    # Browser-visible path when request went through PolySaaS (e.g. /pt/admin/nextcloud/login)
    client_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Django path_info for passthrough requests; empty for native-only captures",
    )

    # Request info
    method = models.CharField(max_length=10)  # GET, POST, etc.
    url = models.URLField(max_length=500)
    path = models.CharField(max_length=500)
    headers = models.JSONField(default=dict, help_text="Request headers")
    cookies = models.JSONField(default=dict, help_text="Request cookies")
    query_params = models.JSONField(default=dict, help_text="Query string parameters")
    body = models.TextField(blank=True, help_text="Request body (POST data)")

    # Response info
    status_code = models.IntegerField()
    response_headers = models.JSONField(default=dict, help_text="Response headers")
    response_body = models.TextField(blank=True, help_text="Response body")
    response_size = models.IntegerField(default=0, help_text="Response size in bytes")

    # Metadata
    endpoint_name = models.CharField(max_length=200, blank=True, help_text="Name of endpoint being debugged")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    captured_at = models.DateTimeField(default=timezone.now)
    duration_ms = models.FloatField(default=0, help_text="Request duration in milliseconds")

    # New server-side capture fields
    service = models.CharField(
        max_length=50, blank=True, default='',
        help_text="mattermost, odoo, nextcloud, etc."
    )
    correlation_id = models.CharField(
        max_length=64, blank=True, default='', db_index=True,
        help_text="Links related requests in a capture session"
    )
    capture_session = models.ForeignKey(
        TrafficCapture, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='logs'
    )

    # HAR export
    har_data = models.JSONField(null=True, blank=True, help_text="Full HAR format data")

    class Meta:
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['-captured_at']),
            models.Index(fields=['url']),
            models.Index(fields=['endpoint_name']),
            models.Index(fields=['service', 'capture_source']),
            models.Index(fields=['capture_session', '-captured_at']),
        ]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} ({self.captured_at})"

    def save(self, *args, **kwargs):
        # Mirror the request user into the tenant schema so the FK resolves.
        # PolySaaS users live in public.auth_user; each tenant schema has its own
        # auth_user table (from migrations) but those rows are absent → FK violation.
        if self.user_id:
            try:
                from django.db import connection as _conn
                from dose.polysniffer.tenant_schema_fk import ensure_auth_user_fk_row

                with _conn.cursor() as _cur:
                    _cur.execute("SHOW search_path")
                    sp = (_cur.fetchone() or [""])[0]
                for part in sp.replace('"', "").split(","):
                    part = part.strip().strip("$").strip()
                    if part and part != "public" and not part.startswith("$"):
                        ensure_auth_user_fk_row(self.user, part)
                        break
            except Exception:
                pass
        try:
            super().save(*args, **kwargs)
        except Exception as exc:
            # If a FK / IntegrityError still fires (e.g. auth_user mirror failed),
            # retry without the user reference rather than surfacing a 500 to the browser.
            if self.user_id is not None and (
                "IntegrityError" in type(exc).__name__
                or "ForeignKey" in str(exc)
                or "auth_user" in str(exc)
                or "violates foreign key" in str(exc).lower()
            ):
                self.user = None
                self.user_id = None
                super().save(*args, **kwargs)
            else:
                raise

    def to_har_entry(self):
        """Convert to HAR format entry"""
        import time
        from datetime import datetime

        # Convert datetime to timestamp
        timestamp = self.captured_at.timestamp()

        return {
            "startedDateTime": self.captured_at.isoformat(),
            "time": self.duration_ms,
            "request": {
                "method": self.method,
                "url": self.url,
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in self.headers.items()],
                "cookies": [{"name": k, "value": v} for k, v in self.cookies.items()],
                "queryString": [{"name": k, "value": str(v)} for k, v in self.query_params.items()],
                "postData": {
                    "mimeType": self.headers.get("Content-Type", "application/octet-stream"),
                    "text": self.body
                } if self.body else None,
                "headersSize": -1,
                "bodySize": len(self.body.encode('utf-8')) if self.body else 0
            },
            "response": {
                "status": self.status_code,
                "statusText": self._get_status_text(),
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in self.response_headers.items()],
                "cookies": [],
                "content": {
                    "size": self.response_size,
                    "mimeType": self.response_headers.get("Content-Type", "text/html"),
                    "text": self.response_body[:10000]  # Limit size for storage
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": self.response_size
            },
            "cache": {},
            "timings": {
                "blocked": -1,
                "dns": -1,
                "connect": -1,
                "send": 0,
                "wait": self.duration_ms,
                "receive": 0
            }
        }

    def _get_status_text(self):
        """Get HTTP status text"""
        status_texts = {
            200: "OK",
            302: "Found",
            404: "Not Found",
            422: "Unprocessable Entity",
            500: "Internal Server Error"
        }
        return status_texts.get(self.status_code, "Unknown")


class TrafficEntry(models.Model):
    """
    Store individual browser-captured network entries (fetch, XHR, WebSocket, navigation).
    
    This model captures client-side network activity from browser extensions or 
    JavaScript instrumentation, storing detailed request/response data for analysis
    and comparison with server-side logs.
    """
    
    # Entry type choices
    ENTRY_TYPE_FETCH = 'fetch'
    ENTRY_TYPE_XHR = 'xhr'
    ENTRY_TYPE_WEBSOCKET = 'websocket'
    ENTRY_TYPE_NAVIGATION = 'navigation'
    ENTRY_TYPE_OTHER = 'other'
    
    ENTRY_TYPE_CHOICES = [
        (ENTRY_TYPE_FETCH, 'Fetch API'),
        (ENTRY_TYPE_XHR, 'XMLHttpRequest'),
        (ENTRY_TYPE_WEBSOCKET, 'WebSocket'),
        (ENTRY_TYPE_NAVIGATION, 'Navigation'),
        (ENTRY_TYPE_OTHER, 'Other'),
    ]
    
    # Core identification
    tenant = models.ForeignKey(
        'dose.Tenant',
        on_delete=models.CASCADE,
        related_name='traffic_entries',
        help_text="Tenant that owns this traffic entry"
    )
    capture = models.ForeignKey(
        TrafficCapture,
        on_delete=models.CASCADE,
        related_name='entries',
        help_text="The capture session this entry belongs to"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this network entry was captured"
    )
    
    # Entry classification
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPE_CHOICES,
        db_index=True,
        help_text="Type of network request (fetch, xhr, websocket, navigation)"
    )
    
    # Request details
    url = models.URLField(
        max_length=1000,
        help_text="Full URL of the request"
    )
    method = models.CharField(
        max_length=10,
        default='GET',
        help_text="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    
    # Response details
    status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code (200, 404, 500, etc.)"
    )
    duration_ms = models.FloatField(
        default=0,
        help_text="Request duration in milliseconds"
    )
    
    # Headers (stored as JSON for flexibility)
    request_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Request headers as key-value pairs"
    )
    response_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Response headers as key-value pairs"
    )
    
    # Body content
    request_body = models.TextField(
        blank=True,
        default='',
        help_text="Request body content (may be truncated for large payloads)"
    )
    response_body_preview = models.TextField(
        blank=True,
        default='',
        help_text="Preview of response body (truncated to avoid storage bloat)"
    )
    
    # Raw data preservation
    raw_entry = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete original entry data as captured from browser"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Traffic Entry"
        verbose_name_plural = "Traffic Entries"
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['tenant', '-timestamp']),
            models.Index(fields=['capture', '-timestamp']),
            models.Index(fields=['entry_type', '-timestamp']),
            models.Index(fields=['tenant', 'capture', '-timestamp']),
            models.Index(fields=['url']),
        ]
    
    def __str__(self):
        status = f"{self.status_code}" if self.status_code else "N/A"
        return f"[{self.entry_type}] {self.method} {self.url[:50]} - {status} @ {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.tenant_id:
            from dose.polysniffer.tenant_schema_fk import ensure_tenant_fk_row

            schema = getattr(self.tenant, "schema_name", None) if self.tenant else None
            ensure_tenant_fk_row(str(self.tenant_id), schema)
        super().save(*args, **kwargs)
    
    def get_entry_type_display_icon(self):
        """Return an icon/emoji for the entry type"""
        icons = {
            self.ENTRY_TYPE_FETCH: '🔄',
            self.ENTRY_TYPE_XHR: '📡',
            self.ENTRY_TYPE_WEBSOCKET: '🔌',
            self.ENTRY_TYPE_NAVIGATION: '🧭',
        }
        return icons.get(self.entry_type, '📊')

