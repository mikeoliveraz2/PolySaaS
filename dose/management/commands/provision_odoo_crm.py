"""
provision_odoo_crm — Ensure a tenant's admin user exists in Odoo and has the
CRM module enabled with the correct access groups.

What this does:
  1. Authenticates to Odoo as the platform admin
  2. Installs the 'crm' module if not already installed
  3. Creates or re-finds the tenant admin user (e.g. olientAdmin)
  4. Assigns CRM salesperson + manager groups to that user
  5. Updates TenantApp.extra_config with the user's Odoo uid

Usage (local dev):
    python manage.py provision_odoo_crm                     # default: olient
    python manage.py provision_odoo_crm <tenant_slug>
    python manage.py provision_odoo_crm olient --email olientAdmin --check-only
"""
from __future__ import annotations

import logging
import xmlrpc.client

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)

# CRM-related group XML IDs that olientAdmin should have
_CRM_GROUPS = [
    "base.group_user",                   # Internal User (required base)
    "crm.group_crm_salesman",            # CRM: User (salesperson)
    "crm.group_crm_manager",             # CRM: Manager (full access)
    "account.group_account_invoice",     # Invoicing (already assigned by tenant provisioner)
    "sales_team.group_sale_salesman",    # Sales: User (optional, enables pipeline view)
]


class Command(BaseCommand):
    help = (
        "Ensure a tenant admin user is provisioned in Odoo with CRM access. "
        "Installs the crm module if needed and assigns CRM groups to the user."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant_slug",
            nargs="?",
            default="olient",
            help="PolySaaS tenant slug (default: olient)",
        )
        parser.add_argument(
            "--email",
            default="",
            help="Odoo login email for this tenant's admin (overrides TenantApp.extra_config)",
        )
        parser.add_argument(
            "--password",
            default="",
            help="Odoo user password (overrides TenantApp.extra_config / POLYSAAS_APP_ADMIN_PASSWORD)",
        )
        parser.add_argument(
            "--check-only",
            action="store_true",
            help="Only check current state — make no changes",
        )
        parser.add_argument(
            "--skip-crm-install",
            action="store_true",
            help="Skip CRM module installation step (use if already installed)",
        )

    def handle(self, *args, **options):
        slug = options["tenant_slug"]
        check_only = options["check_only"]

        from dose.models import Tenant, TenantApp

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")

        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"Tenant not found: {slug}"))
            return

        self.stdout.write(f"Tenant: {tenant.name} (slug={slug} schema={tenant.schema_name})")

        # ── Resolve Odoo connection config ───────────────────────────────────
        config = {
            "url": getattr(settings, "ODOO_SHARED_URL", "https://polysaas-odoo2.onrender.com").rstrip("/"),
            "db": getattr(settings, "ODOO_SHARED_DB", "polysaas_odoo"),
            "admin_login": getattr(settings, "ODOO_XMLRPC_ADMIN_LOGIN", "odooAdmin"),
            "admin_password": getattr(settings, "POLYSAAS_APP_ADMIN_PASSWORD", "PolySaaS2026!"),
        }

        # Build tenant user login/password from options → TenantApp → convention
        tenant_login = options["email"].strip()
        tenant_password = options["password"].strip()

        if not tenant_login or not tenant_password:
            with connection.cursor() as cur:
                cur.execute(f'SET search_path TO "{tenant.schema_name}", public')
            ta = TenantApp.objects.filter(tenant=tenant, app_slug="odoo").first()
            if not ta:
                ta = TenantApp.objects.filter(tenant=tenant, app_name="odoo").first()

            if ta and isinstance(getattr(ta, "extra_config", None), dict):
                ec = ta.extra_config
                if not tenant_login:
                    tenant_login = ec.get("odoo_login", "")
                if not tenant_password:
                    tenant_password = ec.get("odoo_password", "")

        # Last resort: convention-based defaults
        if not tenant_login:
            tenant_login = f"{slug}Admin"
        if not tenant_password:
            tenant_password = getattr(settings, "POLYSAAS_APP_ADMIN_PASSWORD", "PolySaaS2026!")

        self.stdout.write(f"Odoo URL : {config['url']}")
        self.stdout.write(f"Odoo DB  : {config['db']}")
        self.stdout.write(f"User     : {tenant_login}")

        # ── Authenticate as platform admin ───────────────────────────────────
        try:
            common = xmlrpc.client.ServerProxy(
                f"{config['url']}/xmlrpc/2/common", allow_none=True
            )
            admin_uid = common.authenticate(
                config["db"], config["admin_login"], config["admin_password"], {}
            )
            if not admin_uid:
                self.stderr.write(self.style.ERROR(
                    f"Platform admin auth failed: login={config['admin_login']} url={config['url']}"
                ))
                return
            self.stdout.write(self.style.SUCCESS(f"Authenticated as platform admin (uid={admin_uid})"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Could not connect to Odoo: {exc}"))
            return

        models_proxy = xmlrpc.client.ServerProxy(
            f"{config['url']}/xmlrpc/2/object", allow_none=True
        )
        db = config["db"]
        admin_pw = config["admin_password"]

        # ── 1. Install CRM module ────────────────────────────────────────────
        if not options["skip_crm_install"]:
            self._ensure_crm_installed(models_proxy, db, admin_uid, admin_pw, check_only)
        else:
            self.stdout.write("Skipping CRM module install (--skip-crm-install)")

        # ── 2. Find or create tenant admin user ──────────────────────────────
        odoo_user_id = self._ensure_tenant_user(
            models_proxy, db, admin_uid, admin_pw,
            login=tenant_login,
            name=tenant.name,
            password=tenant_password,
            check_only=check_only,
        )
        if not odoo_user_id:
            self.stderr.write(self.style.ERROR("Could not find or create tenant user — aborting"))
            return

        # ── 3. Assign CRM groups ─────────────────────────────────────────────
        self._assign_crm_groups(
            models_proxy, db, admin_uid, admin_pw,
            user_id=odoo_user_id,
            check_only=check_only,
        )

        # ── 4. Update TenantApp.extra_config ─────────────────────────────────
        if not check_only:
            self._update_tenant_app(tenant, tenant_login, tenant_password, odoo_user_id, config)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. olientAdmin (Odoo uid={odoo_user_id}) is provisioned with CRM access."
        ))
        self.stdout.write(
            "Next: restart Django and open the Odoo passthrough. "
            "Run 'python manage.py seed_hubspot_odoo_orchestration' to wire the "
            "HubSpot → Odoo contact sync Instructions."
        )

    # ─────────────────────────────────────────────────────────────────────────

    def _ensure_crm_installed(self, models, db, uid, pw, check_only: bool) -> None:
        """Install the crm module in Odoo if it is not already installed."""
        try:
            rows = models.execute_kw(
                db, uid, pw, "ir.module.module", "search_read",
                [[["name", "=", "crm"]]],
                {"fields": ["name", "state"], "limit": 1},
            )
            if not rows:
                self.stdout.write(self.style.WARNING("CRM module not found in Odoo module list"))
                return

            state = rows[0].get("state", "")
            module_id = rows[0]["id"] if "id" in rows[0] else None

            if state == "installed":
                self.stdout.write(self.style.SUCCESS("CRM module: already installed"))
                return

            self.stdout.write(f"CRM module state: {state}")

            if check_only:
                self.stdout.write(self.style.WARNING("[check-only] Would install CRM module"))
                return

            if module_id:
                self.stdout.write("Installing CRM module (this may take 30–60 seconds)...")
                try:
                    models.execute_kw(
                        db, uid, pw, "ir.module.module", "button_immediate_install",
                        [[module_id]],
                    )
                    self.stdout.write(self.style.SUCCESS("CRM module installed"))
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(
                        f"button_immediate_install raised: {exc} — "
                        "module may still have installed (check Odoo Apps)"
                    ))
        except Exception as exc:
            self.stderr.write(self.style.WARNING(f"CRM install check failed: {exc}"))

    def _ensure_tenant_user(
        self, models, db, admin_uid, admin_pw,
        *, login: str, name: str, password: str, check_only: bool,
    ) -> int | None:
        """Find the tenant user in Odoo; create if absent. Returns Odoo user id."""
        try:
            existing = models.execute_kw(
                db, admin_uid, admin_pw, "res.users", "search_read",
                [[["login", "=", login]]],
                {"fields": ["id", "name", "login", "groups_id"], "limit": 1},
            )
            if existing:
                uid = existing[0]["id"]
                self.stdout.write(
                    self.style.SUCCESS(f"Tenant user found: {login} (uid={uid})")
                )
                return uid

            if check_only:
                self.stdout.write(
                    self.style.WARNING(f"[check-only] Would create user: {login}")
                )
                return None

            # Resolve base group
            base_group_ids = []
            for xml_id in ["base.group_user"]:
                module, xname = xml_id.split(".")
                found = models.execute_kw(
                    db, admin_uid, admin_pw, "ir.model.data", "search_read",
                    [[["module", "=", module], ["name", "=", xname]]],
                    {"fields": ["res_id"], "limit": 1},
                )
                if found:
                    base_group_ids.append((4, found[0]["res_id"]))

            new_id = models.execute_kw(
                db, admin_uid, admin_pw, "res.users", "create",
                [{
                    "name": name,
                    "login": login,
                    "email": login if "@" in login else f"{login}@polysaas.online",
                    "password": password,
                    "groups_id": base_group_ids or [(4, 1)],
                }],
            )
            self.stdout.write(self.style.SUCCESS(f"Created tenant user: {login} (uid={new_id})"))
            return new_id

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"User find/create failed: {exc}"))
            return None

    def _assign_crm_groups(
        self, models, db, admin_uid, admin_pw, *, user_id: int, check_only: bool,
    ) -> None:
        """Resolve CRM group IDs and assign them to the user."""
        group_ids_to_add = []
        for xml_id in _CRM_GROUPS:
            try:
                module, xname = xml_id.split(".")
                found = models.execute_kw(
                    db, admin_uid, admin_pw, "ir.model.data", "search_read",
                    [[["module", "=", module], ["name", "=", xname]]],
                    {"fields": ["res_id"], "limit": 1},
                )
                if found:
                    group_ids_to_add.append((4, found[0]["res_id"]))
                    self.stdout.write(f"  Group resolved: {xml_id} → res_id={found[0]['res_id']}")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  Group not found (module may not be installed): {xml_id}")
                    )
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  Group lookup failed ({xml_id}): {exc}"))

        if not group_ids_to_add:
            self.stdout.write(self.style.WARNING("No CRM groups resolved — check module installation"))
            return

        if check_only:
            self.stdout.write(
                self.style.WARNING(
                    f"[check-only] Would assign {len(group_ids_to_add)} group(s) to uid={user_id}"
                )
            )
            return

        try:
            models.execute_kw(
                db, admin_uid, admin_pw, "res.users", "write",
                [[user_id], {"groups_id": group_ids_to_add}],
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Assigned {len(group_ids_to_add)} CRM group(s) to uid={user_id}"
                )
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Group assignment failed: {exc}"))

    def _update_tenant_app(
        self, tenant, login: str, password: str, odoo_user_id: int, config: dict,
    ) -> None:
        """Persist Odoo credentials back to TenantApp.extra_config."""
        try:
            from dose.models import TenantApp

            with connection.cursor() as cur:
                cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

            ta = TenantApp.objects.filter(
                tenant=tenant, app_slug="odoo"
            ).first() or TenantApp.objects.filter(
                tenant=tenant, app_name="odoo"
            ).first()

            if not ta:
                self.stdout.write(
                    self.style.WARNING(
                        "No Odoo TenantApp found — skipping extra_config update. "
                        "Run the Odoo subscription flow or repair_tenant_odoo to create it."
                    )
                )
                return

            extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
            extra.update({
                "odoo_login": login,
                "odoo_password": password,
                "odoo_user_id": odoo_user_id,
                "odoo_url": config["url"],
                "odoo_db": config["db"],
                "crm_enabled": True,
            })
            ta.extra_config = extra
            ta.save(update_fields=["extra_config"])
            self.stdout.write(
                self.style.SUCCESS(f"TenantApp.extra_config updated (crm_enabled=True)")
            )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"TenantApp update failed (non-fatal): {exc}"))
