"""
Compare admin index behaviour without changing templates.

Usage (local or Hostinger shell):

  python manage.py diagnose_admin_dashboard --email you@example.com

Uses Django's test Client so the full middleware stack runs (same as a browser).
Reports HTTP status, resolved template, app_list length from context, Jazzmin
card count in HTML, and whether the PolySaaS orchestration strip is present.

The test client defaults to Host: testserver, which is not in typical production
ALLOWED_HOSTS. This command picks a valid Host automatically, or use
``--http-host`` to override.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import admin
from django.core.management.base import BaseCommand, CommandError
from django.test import Client


def _http_host_for_test_client(explicit: str = "") -> str:
    if (explicit or "").strip():
        return explicit.strip()

    # Prefer public app URL when set (Hostinger / Dokploy).
    for env_key in ("POLYSAAS_PUBLIC_URL", "APP_PUBLIC_URL", "SITE_URL"):
        raw = os.environ.get(env_key, "").strip()
        if raw:
            host = urlparse(raw).hostname
            if host:
                return host

    hosts = list(getattr(settings, "ALLOWED_HOSTS", []) or [])
    if "*" in hosts:
        return "testserver"
    for cand in ("localhost", "127.0.0.1", "app.prod-polysaas.cloud"):
        if cand in hosts:
            return cand
    for h in hosts:
        hs = str(h)
        if hs and not hs.startswith("."):
            return hs
    for h in hosts:
        hs = str(h)
        if hs.startswith("."):
            # e.g. ".prod-polysaas.cloud" → any subdomain is accepted by Django
            return f"shell-diagnostic{hs}"
    return "localhost"


class Command(BaseCommand):
    help = "GET /admin/ as a user and print admin index diagnostics (local vs Hostinger)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="",
            help="Select user by email (case-insensitive).",
        )
        parser.add_argument(
            "--username",
            default="",
            help="Select user by username.",
        )
        parser.add_argument(
            "--http-host",
            dest="http_host",
            default="",
            help="Host header for the test request (default: derived from ALLOWED_HOSTS / POLYSAAS_PUBLIC_URL).",
        )

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = None
        email = (options.get("email") or "").strip()
        username = (options.get("username") or "").strip()
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                try:
                    from allauth.account.models import EmailAddress

                    ea = (
                        EmailAddress.objects.filter(email__iexact=email)
                        .select_related("user")
                        .order_by("-primary", "-verified", "id")
                        .first()
                    )
                    if ea is not None and ea.user_id:
                        user = ea.user
                except Exception:
                    pass
        elif username:
            user = User.objects.filter(
                **{f"{User.USERNAME_FIELD}__iexact": username}
            ).first()
        else:
            user = User.objects.filter(is_superuser=True).first()

        if not user:
            raise CommandError(
                "No user matched. Pass --email or --username, or create a superuser."
            )

        http_host = _http_host_for_test_client(options.get("http_host") or "")

        self.stdout.write(
            f"User: id={user.pk} username={user.get_username()!r} "
            f"is_superuser={user.is_superuser} is_staff={user.is_staff}"
        )
        self.stdout.write(
            f"admin.site.index_template (attr) = {admin.site.index_template!r}"
        )
        self.stdout.write(f"admin.site._registry size = {len(admin.site._registry)}")
        self.stdout.write(f"Using HTTP_HOST={http_host!r} for test Client GET /admin/")

        client = Client()
        client.force_login(user)
        response = client.get("/admin/", HTTP_HOST=http_host)

        self.stdout.write(f"GET /admin/ -> HTTP {response.status_code}")

        if hasattr(response, "templates") and response.templates:
            names = [getattr(t, "name", str(t)) for t in response.templates]
            self.stdout.write(f"templates_used = {names}")
        else:
            self.stdout.write("templates_used = (none — non-template response?)")

        ctx = getattr(response, "context", None)
        app_list = None
        avail = None
        if ctx is not None:
            try:
                flat = ctx.flatten()
            except Exception as exc:
                self.stdout.write(f"context.flatten failed: {exc}")
                flat = []
            for d in flat:
                if not isinstance(d, dict):
                    continue
                if "app_list" in d:
                    app_list = d["app_list"]
                if "available_apps" in d:
                    avail = d["available_apps"]

        if isinstance(app_list, list):
            self.stdout.write(f"app_list len = {len(app_list)}")
            for app in app_list[:12]:
                if isinstance(app, dict):
                    models = app.get("models") or []
                    self.stdout.write(
                        f"  app {app.get('app_label')!r}: {len(models)} models"
                    )
            if len(app_list) > 12:
                self.stdout.write(f"  ... and {len(app_list) - 12} more apps")
        else:
            self.stdout.write(f"app_list = {app_list!r} (missing or wrong type)")

        if isinstance(avail, list):
            self.stdout.write(f"available_apps len = {len(avail)}")
        else:
            self.stdout.write(f"available_apps = {avail!r}")

        body = b""
        if hasattr(response, "content"):
            body = response.content
        text = body.decode("utf-8", errors="replace")
        cards = text.count('class="card mb-3"')
        self.stdout.write(f'HTML count of class="card mb-3" (Jazzmin cards) = {cards}')
        self.stdout.write(
            "HTML contains orchestration CTA section = "
            f"{('Orchestration workspace' in text or 'Dynamic Orchestration Dashboard' in text)}"
        )
