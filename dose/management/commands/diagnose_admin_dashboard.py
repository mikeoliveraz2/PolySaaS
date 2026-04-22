"""
Compare admin index behaviour without changing templates.

Usage (local or Render shell):

  python manage.py diagnose_admin_dashboard --email you@example.com

Uses Django's test Client so the full middleware stack runs (same as a browser).
Reports HTTP status, resolved template, app_list length from context, Jazzmin
card count in HTML, and whether the PolySaaS orchestration strip is present.
"""

from __future__ import annotations

from django.contrib import admin
from django.core.management.base import BaseCommand, CommandError
from django.test import Client


class Command(BaseCommand):
    help = "GET /admin/ as a user and print admin index diagnostics (local vs Render)."

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

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = None
        email = (options.get("email") or "").strip()
        username = (options.get("username") or "").strip()
        if email:
            user = User.objects.filter(email__iexact=email).first()
        elif username:
            user = User.objects.filter(username=username).first()
        else:
            user = User.objects.filter(is_superuser=True).first()

        if not user:
            raise CommandError(
                "No user matched. Pass --email or --username, or create a superuser."
            )

        self.stdout.write(
            f"User: id={user.pk} username={user.get_username()!r} "
            f"is_superuser={user.is_superuser} is_staff={user.is_staff}"
        )
        self.stdout.write(
            f"admin.site.index_template (attr) = {admin.site.index_template!r}"
        )
        self.stdout.write(f"admin.site._registry size = {len(admin.site._registry)}")

        client = Client()
        client.force_login(user)
        response = client.get("/admin/")

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
