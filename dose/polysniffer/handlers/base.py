# File: polysniffer/handlers/base.py
# Purpose: Base class for clean server-side passthrough handlers

import logging

import requests
from django.http import HttpResponse
from django.utils.html import escape

from dose.polysniffer.views.core import get_endpoint_any_schema

logger = logging.getLogger(__name__)


class BasePassthroughHandler:
    """
    Base class for clean passthrough handlers.
    Uses server-side fetch → process → return pattern.
    Resolves PassThroughEndpoint in the active tenant schema (not public-only ORM).
    """

    def __init__(self, endpoint_id, request):
        if request is None:
            raise ValueError("request is required for tenant-scoped endpoint lookup")
        self.request = request
        self.endpoint = get_endpoint_any_schema(endpoint_id, request)

    def _endpoint_label(self):
        ep = self.endpoint
        return (
            (getattr(ep, "menu_title", None) or "").strip()
            or (getattr(ep, "trigger_path", None) or "").strip()
            or f"endpoint {ep.pk}"
        )

    def get_upstream_cookies(self, request):
        """Override in subclass if special cookies are needed."""
        return {}

    def process_html_response(
        self,
        html_str,
        request,
        endpoint_url=None,
        inject_toolbar=True,
        rewrite_assets=True,
    ):
        """
        Main processing method.
        Subclasses should override this for URL rewriting and toolbar injection.
        inject_toolbar=False when the captured HTML already includes a toolbar.
        rewrite_assets=False on a second pass over already-rewritten HTML (building pen).
        """
        return html_str, None

    def embed(self, request):
        """
        Main entry point: fetch real target on server, process it, return HTML.
        """
        label = escape(self._endpoint_label())
        try:
            cookies = self.get_upstream_cookies(request) or {}
            headers = {
                "User-Agent": request.META.get(
                    "HTTP_USER_AGENT", "Mozilla/5.0"
                ),
            }

            response = requests.get(
                self.endpoint.endpoint_url,
                cookies=cookies,
                headers=headers,
                timeout=20,
                allow_redirects=True,
            )

            html_content = response.text

            processed_html, django_response = self.process_html_response(
                html_content,
                request,
                endpoint_url=self.endpoint.endpoint_url,
                inject_toolbar=True,
                rewrite_assets=True,
            )

            if django_response is not None:
                return django_response

            return HttpResponse(
                processed_html,
                content_type="text/html; charset=utf-8",
                status=response.status_code if response.status_code else 200,
            )

        except Exception as exc:
            logger.exception(
                "[BasePassthroughHandler] embed failed for %s: %s",
                self._endpoint_label(),
                exc,
            )
            return HttpResponse(
                f"<h1>Error loading {label}</h1><pre>{escape(str(exc))}</pre>",
                status=500,
                content_type="text/html; charset=utf-8",
            )
