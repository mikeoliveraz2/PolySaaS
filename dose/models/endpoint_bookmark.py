import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import models


_REGISTRY_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class EndpointBookmark(models.Model):
    """Tenant-schema navigation/action shortcut for one passthrough endpoint."""

    MOCK_SURFACE = "mock_surface"
    POPUP_FORM = "popup_form"
    DIRECT_EVENT = "direct_event"
    PASSTHROUGH_PATH = "passthrough_path"
    EXTERNAL_PATH = "external_path"
    DESTINATION_CHOICES = [
        (MOCK_SURFACE, "Mock or screenshot surface"),
        (POPUP_FORM, "Popup form"),
        (DIRECT_EVENT, "Direct event"),
        (PASSTHROUGH_PATH, "Passthrough path"),
        (EXTERNAL_PATH, "Real application path"),
    ]
    KEY_DESTINATIONS = {MOCK_SURFACE, POPUP_FORM, DIRECT_EVENT}
    PATH_DESTINATIONS = {PASSTHROUGH_PATH}

    endpoint = models.ForeignKey(
        "dose.PassThroughEndpoint",
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    key = models.SlugField(
        max_length=100,
        help_text="Stable endpoint-local bookmark key.",
    )
    title = models.CharField(max_length=120)
    destination_type = models.CharField(
        max_length=30,
        choices=DESTINATION_CHOICES,
    )
    target = models.CharField(
        max_length=500,
        help_text="Allowlisted registry key or validated relative path.",
    )
    description = models.CharField(max_length=240, blank=True, default="")
    icon = models.CharField(max_length=100, blank=True, default="🔖")
    sort_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "endpoint_bookmark"
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("endpoint", "key"),
                name="endpoint_bookmark_unique_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=("endpoint", "is_active", "sort_order"),
                name="endpoint_bookmark_list_idx",
            ),
        ]

    def clean(self):
        super().clean()
        target = (self.target or "").strip()
        errors = {}
        if self.destination_type in self.KEY_DESTINATIONS:
            if not _REGISTRY_KEY_RE.fullmatch(target):
                errors["target"] = (
                    "Mock, form, and event targets must be registered lowercase keys."
                )
        elif self.destination_type in self.PATH_DESTINATIONS:
            parsed = urlsplit(target)
            if (
                not target.startswith("/")
                or target.startswith("//")
                or parsed.scheme
                or parsed.netloc
                or "\\" in target
                or any(ord(char) < 32 for char in target)
            ):
                errors["target"] = (
                    "Passthrough and external targets must be safe relative paths."
                )
        elif self.destination_type == self.EXTERNAL_PATH:
            parsed = urlsplit(target)
            if parsed.scheme:
                endpoint_url = urlsplit(
                    getattr(getattr(self, "endpoint", None), "endpoint_url", "") or ""
                )
                same_host = (
                    parsed.hostname
                    and endpoint_url.hostname
                    and parsed.netloc.lower() == endpoint_url.netloc.lower()
                )
                scheme_allowed = parsed.scheme == "https" or (
                    parsed.scheme == "http" and endpoint_url.scheme == "http"
                )
                if (
                    not same_host
                    or not scheme_allowed
                    or parsed.username
                    or parsed.password
                    or "\\" in target
                    or any(ord(char) < 32 for char in target)
                ):
                    errors["target"] = (
                        "Absolute application URLs must use the endpoint's allowlisted "
                        "host and HTTP(S) scheme."
                    )
            elif (
                not target.startswith("/")
                or target.startswith("//")
                or "\\" in target
                or any(ord(char) < 32 for char in target)
            ):
                errors["target"] = "External targets must be safe relative paths or allowlisted URLs."
        else:
            errors["destination_type"] = "Unsupported bookmark destination type."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.key = (self.key or "").strip().lower()
        self.target = (self.target or "").strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.endpoint.get_menu_title()}: {self.title}"
