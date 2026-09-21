"""Seed Odoo Control Panel → New contact consumer (OdooCreatePartner)."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import ODOO_CP_CONTACT_ACTION_PATH, ODOO_CP_CONTACT_EVENT_KEY


class Command(BaseCommand):
    help = "Create/update Odoo Control Panel New contact → OdooCreatePartner binding"

    def add_arguments(self, parser):
        parser.add_argument("--schema", required=True)

    def handle(self, *args, **options):
        schema = options["schema"].strip()
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
        tenant = Tenant.objects.filter(
            schema_name=schema,
            is_active=True,
        ).first()
        if not tenant or schema.lower() == "public":
            raise CommandError(f"Active tenant schema not found: {schema}")

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                raise CommandError(f"Could not select tenant schema: {schema}")
            instruction, created = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=ODOO_CP_CONTACT_ACTION_PATH,
                requestmethod="POST",
                direction="REQ",
                defaults={
                    "eventKey": ODOO_CP_CONTACT_EVENT_KEY,
                    "executescript": "OdooCreatePartner",
                    "description": "Odoo Control Panel New contact → OdooCreatePartner",
                    "save_callbackdata": True,
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb} OdooCreatePartner instruction #{instruction.pk}: "
                    f"{ODOO_CP_CONTACT_ACTION_PATH}"
                )
            )
