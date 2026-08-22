"""Bind the two live Slack wireframe webhooks in one tenant schema."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import SLACK_WIREFRAME_ACTIONS


class Command(BaseCommand):
    help = "Create/update the Slack contact and quotation consumer bindings"

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

        bindings = {
            "contact": "OdooCreatePartner",
            "sale": "OdooCreateQuotation",
        }
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                raise CommandError(f"Could not select tenant schema: {schema}")
            for kind, service in bindings.items():
                action_path, event_key = SLACK_WIREFRAME_ACTIONS[kind]
                instruction, created = Instruction.objects.update_or_create(
                    tenant=tenant,
                    requestpath=action_path,
                    requestmethod="POST",
                    direction="REQ",
                    defaults={
                        "eventKey": event_key,
                        "executescript": service,
                        "description": f"Slack wireframe {kind} consumer",
                        "save_callbackdata": True,
                    },
                )
                verb = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{verb} {service} instruction #{instruction.pk}: {action_path}"
                    )
                )
