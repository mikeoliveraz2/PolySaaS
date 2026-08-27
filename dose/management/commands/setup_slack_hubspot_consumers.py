"""Bind Slack wireframe contact/sale events to HubSpot write consumers."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import SLACK_WIREFRAME_ACTIONS


class Command(BaseCommand):
    help = (
        "Create/update HubSpot consumers for Slack contact + sale "
        "(dual-feed alongside OdooCreatePartner / OdooCreateQuotation)"
    )

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
            "contact": (
                "HubSpotCreateContact",
                "Slack wireframe contact → HubSpot consumer",
            ),
            "sale": (
                "HubSpotCreateDeal",
                "Slack wireframe sale → HubSpot consumer",
            ),
        }
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                raise CommandError(f"Could not select tenant schema: {schema}")
            for kind, (service, description) in bindings.items():
                action_path, event_key = SLACK_WIREFRAME_ACTIONS[kind]
                # Prefer update by executescript so we do not overwrite Odoo consumers
                # that share the same mailbox path.
                existing = Instruction.objects.filter(
                    tenant=tenant,
                    requestpath=action_path,
                    requestmethod="POST",
                    direction="REQ",
                    executescript=service,
                ).first()
                if existing:
                    existing.eventKey = event_key
                    existing.description = description
                    existing.save_callbackdata = True
                    existing.save(
                        update_fields=[
                            "eventKey",
                            "description",
                            "save_callbackdata",
                        ]
                    )
                    instruction, created = existing, False
                else:
                    instruction = Instruction.objects.create(
                        tenant=tenant,
                        requestpath=action_path,
                        requestmethod="POST",
                        direction="REQ",
                        eventKey=event_key,
                        executescript=service,
                        description=description,
                        save_callbackdata=True,
                    )
                    created = True
                verb = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{verb} {service} instruction #{instruction.pk}: {action_path}"
                    )
                )
