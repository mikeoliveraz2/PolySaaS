"""
Store a HubSpot Private App access token for a given tenant.

A Private App token is a long-lived bearer token (does not expire the same
way OAuth tokens do).  It bypasses web-UI login entirely and is all we need
for API-driven orchestration (contacts list, webhooks, sync to Odoo).

Usage:
    python manage.py store_hubspot_token olient pat-na1-xxxx...
    python manage.py store_hubspot_token olient pat-na1-xxxx... --portal-id 12345
    python manage.py store_hubspot_token olient --show         # show current token (masked)
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Store a HubSpot Private App access token in TenantApp.extra_config."

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant_slug",
            help="Tenant schema slug (e.g. olient)",
        )
        parser.add_argument(
            "token",
            nargs="?",
            default=None,
            help="HubSpot Private App access token (pat-na1-...)",
        )
        parser.add_argument(
            "--portal-id",
            default="",
            help="HubSpot portal/hub ID (optional, looked up automatically if omitted)",
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="Print the currently stored token (masked) without changing anything",
        )

    def handle(self, *args, **options):
        slug = options["tenant_slug"]
        token = (options["token"] or "").strip()
        portal_id = (options["portal_id"] or "").strip()
        show_mode = options["show"]

        # Always resolve Tenant from public schema
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")

        from dose.models import Tenant, TenantApp

        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            raise CommandError(f"Tenant not found: {slug}")

        self.stdout.write(f"Tenant: {tenant.name}  (schema={tenant.schema_name})")

        # TenantApp rows for HubSpot live in public (PublicTenantAppBundleManager)
        ta = TenantApp.public_bundles.filter(tenant=tenant, app_name="hubspot").first()

        if show_mode:
            if not ta:
                self.stdout.write("  No HubSpot TenantApp record found.")
                return
            extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
            stored = extra.get("hs_access_token") or ""
            if stored:
                masked = stored[:12] + "..." + stored[-4:] if len(stored) > 16 else stored
                self.stdout.write(f"  hs_access_token : {masked}")
                self.stdout.write(f"  hs_portal_id    : {extra.get('hs_portal_id', '(none)')}")
                self.stdout.write(f"  hs_token_type   : {extra.get('hs_token_type', '(unset)')}")
            else:
                self.stdout.write("  No token stored yet.")
            return

        if not token:
            raise CommandError("Provide the access token as the second argument, or use --show.")

        if not token.startswith("pat-"):
            self.stdout.write(
                self.style.WARNING(
                    "  Warning: token does not start with 'pat-'. "
                    "HubSpot Private App tokens usually start with 'pat-na1-' or 'pat-eu1-'."
                )
            )

        # Create TenantApp row if it does not exist
        if ta is None:
            ta = TenantApp(
                tenant=tenant,
                app_name="hubspot",
                status="active",
                extra_config={},
            )
            self.stdout.write("  Creating new HubSpot TenantApp record.")
        else:
            self.stdout.write(f"  Updating existing HubSpot TenantApp (pk={ta.pk}, status={ta.status}).")
            ta.status = "active"

        extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}

        # Try to auto-fetch portal metadata via HubSpot token-info endpoint
        fetched_portal = ""
        if not portal_id:
            self.stdout.write("  Fetching token metadata from HubSpot (to get portal ID)...")
            try:
                import requests as http_req
                r = http_req.get(
                    "https://api.hubapi.com/oauth/v1/access-tokens/" + token,
                    timeout=10,
                )
                if r.ok:
                    meta = r.json()
                    fetched_portal = str(meta.get("hub_id") or meta.get("hubId") or "")
                    if fetched_portal:
                        self.stdout.write(
                            self.style.SUCCESS(f"  Portal ID auto-detected: {fetched_portal}")
                        )
                    else:
                        self.stdout.write(
                            "  Token info returned OK but no hub_id — this is normal for Private App tokens."
                        )
                else:
                    self.stdout.write(
                        f"  Token info endpoint returned {r.status_code} — skipping portal ID lookup."
                    )
            except Exception as exc:
                self.stdout.write(f"  Token info fetch failed ({exc}) — continuing without portal ID.")

        extra.update({
            "hs_access_token": token,
            "hs_token_type": "private_app",
            "hs_portal_id": portal_id or fetched_portal or extra.get("hs_portal_id", ""),
            # Private App tokens don't expire on a schedule — clear OAuth expiry fields
            "hs_refresh_token": "",
            "hs_token_expires_at": "",
        })
        ta.extra_config = extra

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")

        ta.save()
        self.stdout.write(self.style.SUCCESS(
            f"\n  Stored hs_access_token for tenant '{slug}'."
        ))
        self.stdout.write(
            f"  Run a quick API test:\n"
            f"    python manage.py shell -c \""
            f"from dose.services.hubspot_api import HubspotApiService; "
            f"from dose.models import Tenant; "
            f"t=Tenant.objects.get(slug='{slug}'); "
            f"print(HubspotApiService(t).list_contacts(limit=3))\""
        )
