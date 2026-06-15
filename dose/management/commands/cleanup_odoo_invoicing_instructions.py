"""
Remove redundant Odoo invoicing path-fallback Instructions and optional duplicate CallBackData.

The subscribe provisioner used to create both /odoo/accounting/{menu_id} and /odoo/accounting
GET rules — both matched the same navigation and doubled CallBackData rows.

Usage:
  python manage.py cleanup_odoo_invoicing_instructions polysaasppd2
  python manage.py cleanup_odoo_invoicing_instructions polysaasppd2 --prune-callbacks
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.management.schema_utils import set_search_path
from dose.models import CallBackData, Instruction, Tenant


class Command(BaseCommand):
    help = "Drop duplicate Odoo invoicing GET Instructions (path fallback) for a tenant."

    def add_arguments(self, parser):
        parser.add_argument("slug", help="Tenant slug (e.g. polysaasppd2)")
        parser.add_argument(
            "--prune-callbacks",
            action="store_true",
            help="Delete duplicate odoo_invoicing_viewed CallBackData (keep newest per path).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report only; no deletes.",
        )

    def handle(self, *args, **options):
        slug = (options["slug"] or "").strip()
        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            raise CommandError(f"Tenant not found: {slug!r}")

        set_search_path(tenant.schema_name)
        fallback = Instruction.objects.filter(
            eventKey="odoo_invoicing_viewed",
            requestpath="/odoo/accounting",
            requestmethod="GET",
            match_type="path",
        )
        specific_exists = Instruction.objects.filter(
            eventKey="odoo_invoicing_viewed",
            requestpath__startswith="/odoo/accounting/",
            requestmethod="GET",
        ).exists()

        count = fallback.count()
        if count and specific_exists:
            self.stdout.write(
                f"Removing {count} redundant path-fallback instruction(s) in {tenant.schema_name}"
            )
            if not options["dry_run"]:
                fallback.delete()
        elif count:
            self.stdout.write("Path fallback exists but no /odoo/accounting/<id> rule — leaving as-is.")
        else:
            self.stdout.write("No redundant path-fallback instruction found.")

        if options["prune_callbacks"]:
            self._prune_callbacks(tenant, dry_run=options["dry_run"])

    def _prune_callbacks(self, tenant, *, dry_run: bool):
        rows = list(
            CallBackData.objects.filter(matchingEventKey="odoo_invoicing_viewed").order_by("-pub_date")
        )
        seen = set()
        to_delete = []
        for cb in rows:
            payload = cb.callbackdata if isinstance(cb.callbackdata, dict) else {}
            path = ((payload.get("path") or "").split("?")[0].rstrip("/") or "").lower()
            key = (cb.matchingEventKey, path, cb.description)
            if key in seen:
                to_delete.append(cb.pk)
            else:
                seen.add(key)
        self.stdout.write(f"Duplicate CallBackData to remove: {len(to_delete)}")
        if to_delete and not dry_run:
            CallBackData.objects.filter(pk__in=to_delete).delete()
