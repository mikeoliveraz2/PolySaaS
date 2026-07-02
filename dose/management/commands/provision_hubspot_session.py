"""
Provision a HubSpot web session for a tenant using a real Playwright browser.

Playwright uses headless Chromium with a genuine browser TLS fingerprint,
bypassing Cloudflare and HubSpot bot detection that blocks plain server-side
HTTP login POSTs.

After successful login, all cookies are stored in TenantApp.extra_config so
the HubspotSessionService can replay them on every proxied request — exactly
the same Mattermost/Odoo pattern.

Usage
-----
    python manage.py provision_hubspot_session olient \\
        --email michael.oliver@polysaas.online \\
        --password "YourHubSpotPassword"

    # Debug: show browser window so you can handle 2FA
    python manage.py provision_hubspot_session olient \\
        --email michael.oliver@polysaas.online \\
        --password "YourHubSpotPassword" \\
        --headful

    # Validate existing stored cookies without re-provisioning
    python manage.py provision_hubspot_session olient --validate-only
"""
from __future__ import annotations

import json
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Provision HubSpot session cookies via Playwright (real browser, bypasses bot detection)."

    def add_arguments(self, parser):
        parser.add_argument("tenant_slug", type=str, help="Tenant slug (e.g. olient)")
        parser.add_argument("--email", type=str, default="", help="HubSpot login email")
        parser.add_argument("--password", type=str, default="", help="HubSpot password")
        parser.add_argument(
            "--headful",
            action="store_true",
            default=False,
            help="Show browser window (useful for 2FA / CAPTCHA)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=120,
            help="Max seconds to wait for login to complete (default 120)",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            default=False,
            help="Only validate existing stored cookies; do not launch browser",
        )

    def handle(self, *args, **options):
        slug = options["tenant_slug"]
        email = options["email"].strip()
        password = options["password"].strip()
        headless = not options["headful"]
        timeout_s = options["timeout"]
        validate_only = options["validate_only"]

        # ── Resolve tenant ────────────────────────────────────────────────────
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")
        from dose.models import Tenant
        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            raise CommandError(f"Tenant not found: {slug!r}")
        self.stdout.write(f"Tenant: {tenant.name} (slug={slug})")

        # ── Ensure HubSpot TenantApp exists in public ─────────────────────────
        ta = self._ensure_hubspot_tenant_app(tenant, email)

        # ── Validate-only mode ────────────────────────────────────────────────
        if validate_only:
            return self._validate_stored_cookies(ta)

        # ── Credential check ──────────────────────────────────────────────────
        if not email:
            email = (ta.extra_config or {}).get("hs_login_email", "")
        if not email:
            raise CommandError("--email is required (no stored email found in TenantApp)")

        if not password:
            password = (ta.extra_config or {}).get("hs_password", "")
        if not password:
            raise CommandError("--password is required (no stored password found in TenantApp)")

        # ── Run Playwright ────────────────────────────────────────────────────
        self.stdout.write(f"\nLaunching {'headful' if not headless else 'headless'} Chromium...")
        cookies = self._playwright_login(
            email=email,
            password=password,
            headless=headless,
            timeout_s=timeout_s,
        )

        if not cookies:
            raise CommandError("Login failed — no cookies extracted. Use --headful to debug.")

        self.stdout.write(self.style.SUCCESS(
            f"Login succeeded — captured {len(cookies)} cookies: {sorted(cookies.keys())}"
        ))

        # ── Persist to TenantApp.extra_config ─────────────────────────────────
        extra = dict(ta.extra_config or {})
        extra["hs_web_cookies"] = cookies
        extra["hs_web_cookies_at"] = time.time()
        extra["hs_web_cookies_source"] = "playwright_provision"
        extra["hs_login_email"] = email
        # Never store password in plaintext permanently — only for re-provision hint
        # (omit hs_password for security)
        ta.extra_config = extra
        ta.save(update_fields=["extra_config"])
        self.stdout.write(self.style.SUCCESS(f"Stored cookies in TenantApp pk={ta.pk}"))

        # ── Validate the stored cookies ────────────────────────────────────────
        self._validate_stored_cookies(ta)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _ensure_hubspot_tenant_app(self, tenant, email: str):
        """Get or create the HubSpot TenantApp in the public schema."""
        from dose.models import TenantApp

        ta = TenantApp.public_bundles.filter(tenant=tenant, app_name="hubspot").first()
        if ta:
            self.stdout.write(f"HubSpot TenantApp: pk={ta.pk} status={ta.status}")
            return ta

        self.stdout.write("No HubSpot TenantApp found — creating one...")
        ta = TenantApp(
            tenant=tenant,
            app_name="hubspot",
            status="active",
            extra_config={"hs_login_email": email} if email else {},
        )
        ta.save()
        self.stdout.write(self.style.SUCCESS(f"Created HubSpot TenantApp pk={ta.pk}"))
        return ta

    def _playwright_login(
        self,
        *,
        email: str,
        password: str,
        headless: bool,
        timeout_s: int,
    ) -> dict[str, str]:
        """
        Use Playwright Chromium to log in to app.hubspot.com and return all cookies.
        Real browser fingerprint — bypasses Cloudflare bot detection.
        """
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

        login_url = "https://app.hubspot.com/login/"
        timeout_ms = timeout_s * 1000

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = context.new_page()

            # Navigate to login
            self.stdout.write(f"  Navigating to {login_url} ...")
            page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
            self.stdout.write(f"  Page title: {page.title()!r}")

            # Fill email
            self.stdout.write("  Filling email...")
            try:
                page.wait_for_selector('input[type="email"], input[name="email"], #username', timeout=15000)
            except PlaywrightTimeout:
                self.stdout.write(self.style.WARNING("  Email field not found — check page"))
                if not headless:
                    input("  Press Enter after you've handled the page manually...")
                else:
                    raise CommandError("Login page email field not found")

            email_sel = 'input[type="email"], input[name="email"], #username'
            page.fill(email_sel, email)
            page.keyboard.press("Enter")

            # Wait for password field (some flows show email then password separately)
            self.stdout.write("  Waiting for password field...")
            try:
                page.wait_for_selector('input[type="password"]', timeout=10000)
                page.fill('input[type="password"]', password)
                self.stdout.write("  Filled password, submitting...")
                page.keyboard.press("Enter")
            except PlaywrightTimeout:
                if not headless:
                    self.stdout.write("  Password field not found. Handle manually in browser window.")
                    input("  Press Enter after you've submitted the login form...")
                else:
                    raise CommandError("Login page password field not found")

            # Wait for successful login — URL moves away from /login/
            self.stdout.write(f"  Waiting for login to complete (up to {timeout_s}s)...")
            self.stdout.write("  (If 2FA is required, use --headful to interact)")
            try:
                # Wait for URL that doesn't contain "/login"
                page.wait_for_url(
                    lambda url: "/login" not in url and "app.hubspot.com" in url,
                    timeout=timeout_ms,
                )
                self.stdout.write(f"  Login success! URL: {page.url!r}")
            except PlaywrightTimeout:
                current = page.url
                self.stdout.write(self.style.WARNING(
                    f"  Timed out waiting for post-login redirect. Current URL: {current!r}"
                ))
                if "/login" in current:
                    if not headless:
                        input("  Still on login page. Handle 2FA or CAPTCHA then press Enter...")
                    else:
                        # Try to extract whatever cookies we have
                        self.stdout.write("  Extracting available cookies anyway...")

            # Extract all cookies from the browser context
            raw_cookies = context.cookies()
            browser.close()

        # Convert to simple dict — keep HubSpot auth cookies
        hs_cookie_names = {
            "hubspotapi", "csrf.app", "hubspotutk", "hubspotulk", "hs",
            "hubspotapi-csrf", "hubspotapi-prefs", "__hsmem",
            "__hssc", "__hssrc", "__hstc", "__hsfp", "__hstcn",
        }
        cookies: dict[str, str] = {}
        for c in raw_cookies:
            name = c.get("name", "")
            value = c.get("value", "")
            if name and value and (name in hs_cookie_names or "hubspot" in name.lower()):
                cookies[name] = value

        # Fallback: include any cookie from hubspot.com if none matched
        if not cookies:
            for c in raw_cookies:
                name = c.get("name", "")
                value = c.get("value", "")
                domain = c.get("domain", "")
                if name and value and "hubspot" in domain.lower():
                    cookies[name] = value

        return cookies

    def _validate_stored_cookies(self, ta) -> None:
        """Validate stored cookies by probing HubSpot portal API."""
        import requests as http_requests

        extra = ta.extra_config or {}
        cookies = extra.get("hs_web_cookies") or {}
        if not cookies:
            self.stdout.write(self.style.WARNING("No stored cookies to validate."))
            return

        stored_at = extra.get("hs_web_cookies_at", 0)
        age_h = (time.time() - float(stored_at)) / 3600 if stored_at else None
        source = extra.get("hs_web_cookies_source", "unknown")

        self.stdout.write(
            f"\nValidating {len(cookies)} stored cookies "
            f"(source={source}, age={age_h:.1f}h)..."
        )

        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        try:
            resp = http_requests.get(
                "https://api.hubspot.com/home/v2/api/portal",
                headers={
                    "Cookie": cookie_header,
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0",
                },
                timeout=15,
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Validation request failed: {exc}"))
            return

        if resp.status_code == 200:
            try:
                data = resp.json()
                portal_id = data.get("portalId") or data.get("hubId") or data.get("id")
                self.stdout.write(self.style.SUCCESS(
                    f"VALID — portalId={portal_id}. Passthrough will use these cookies."
                ))
                # Update TenantApp with validated portal_id
                extra = dict(ta.extra_config or {})
                if portal_id:
                    extra["hs_portal_id"] = portal_id
                    ta.extra_config = extra
                    ta.save(update_fields=["extra_config"])
                    self.stdout.write(f"  Saved hs_portal_id={portal_id} to TenantApp.")
            except Exception:
                self.stdout.write(self.style.SUCCESS("VALID (portal API returned 200)"))
        else:
            self.stdout.write(self.style.ERROR(
                f"INVALID — portal API returned HTTP {resp.status_code}. "
                f"Re-run without --validate-only to provision fresh cookies."
            ))
            self.stdout.write(f"  Response: {resp.text[:200]}")
