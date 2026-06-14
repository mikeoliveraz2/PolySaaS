"""
Management command to set up cross-app sync Instructions.
Creates the Instruction rows that wire:
  1. Bundled app API calls → EndpointDataExtractor → Pub/Sub
  2. Pub/Sub topics → OdooCustomerSync (and other handlers)

Usage:
  python manage.py setup_crossapp_sync
  python manage.py setup_crossapp_sync --list-topics
  python manage.py setup_crossapp_sync --dry-run
"""
from django.core.management.base import BaseCommand
from dose.models import Instruction
from dose.services.app_endpoint_catalog import APP_ENDPOINT_CATALOG, get_all_topics
import logging

logger = logging.getLogger(__name__)


# Extractor instructions: intercept bundled app API calls
EXTRACTOR_INSTRUCTIONS = [
    {
        "eventKey": "dolibarr.api.post",
        "requestpath": "/admin/dolibarr/api/index.php",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "EndpointDataExtractor",
        "description": "Extract entity data from Dolibarr API POST and publish to Pub/Sub",
        "save_callbackdata": True,
    },
    {
        "eventKey": "odoo.api.post",
        "requestpath": "/admin/odoo/web/dataset/call_kw",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "EndpointDataExtractor",
        "description": "Extract entity data from Odoo API POST and publish to Pub/Sub",
        "save_callbackdata": True,
    },
    {
        "eventKey": "nextcloud.api.post",
        "requestpath": "/admin/nextcloud/ocs",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "EndpointDataExtractor",
        "description": "Extract entity data from Nextcloud API POST and publish to Pub/Sub",
        "save_callbackdata": True,
    },
    {
        "eventKey": "mattermost.api.post",
        "requestpath": "/admin/mattermost/api/v4",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "EndpointDataExtractor",
        "description": "Extract entity data from Mattermost API POST and publish to Pub/Sub",
        "save_callbackdata": True,
    },
    {
        "eventKey": "wordpress.api.post",
        "requestpath": "/admin/wordpress/wp-json/wp/v2",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "EndpointDataExtractor",
        "description": "Extract entity data from WordPress API POST and publish to Pub/Sub",
        "save_callbackdata": True,
    },
    {
        "eventKey": "liferay.api.post",
        "requestpath": "/admin/liferay/o/headless",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "EndpointDataExtractor",
        "description": "Extract entity data from Liferay API POST and publish to Pub/Sub",
        "save_callbackdata": True,
    },
]

# Handler instructions: consume from Pub/Sub topics and sync to target apps
HANDLER_INSTRUCTIONS = [
    {
        "eventKey": "sync.dolibarr.customer.to.odoo",
        "requestpath": "/mq/polysaas.dolibarr.customer",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "OdooCustomerSync",
        "description": "Sync Dolibarr customer → Odoo partner (create/update)",
        "save_callbackdata": True,
    },
    {
        "eventKey": "sync.dolibarr.contact.to.odoo",
        "requestpath": "/mq/polysaas.dolibarr.contact",
        "requestmethod": "POST",
        "direction": "REQ",
        "executescript": "OdooCustomerSync",
        "description": "Sync Dolibarr contact → Odoo partner (create/update)",
        "save_callbackdata": True,
    },
]


class Command(BaseCommand):
    help = "Set up cross-app sync Instructions for EndpointDataExtractor and handler services"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Show what would be created without doing it")
        parser.add_argument('--list-topics', action='store_true', help="List all Pub/Sub topics from the catalog")
        parser.add_argument('--clear', action='store_true', help="Remove existing cross-app sync instructions first")

    def handle(self, *args, **options):
        if options['list_topics']:
            self.stdout.write("\nAll Pub/Sub topics in the endpoint catalog:\n")
            for topic in sorted(get_all_topics()):
                self.stdout.write(f"  {topic}")
            self.stdout.write(f"\nTotal: {len(get_all_topics())} topics\n")
            return

        if options['clear']:
            deleted, _ = Instruction.objects.filter(
                executescript__in=['EndpointDataExtractor', 'OdooCustomerSync']
            ).delete()
            self.stdout.write(f"Cleared {deleted} existing cross-app sync instructions")

        all_instructions = EXTRACTOR_INSTRUCTIONS + HANDLER_INSTRUCTIONS
        created = 0
        skipped = 0

        for instr_data in all_instructions:
            exists = Instruction.objects.filter(
                eventKey=instr_data["eventKey"],
                executescript=instr_data["executescript"],
            ).exists()

            if exists:
                skipped += 1
                if options['dry_run']:
                    self.stdout.write(f"  SKIP (exists): {instr_data['eventKey']}")
                continue

            if options['dry_run']:
                self.stdout.write(
                    f"  WOULD CREATE: {instr_data['eventKey']} "
                    f"→ {instr_data['requestpath']} "
                    f"→ {instr_data['executescript']}"
                )
            else:
                Instruction.objects.create(**instr_data)
                created += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  Created: {instr_data['eventKey']} → {instr_data['executescript']}"
                ))

        action = "Would create" if options['dry_run'] else "Created"
        self.stdout.write(f"\n{action} {created} instructions, skipped {skipped} (already exist)")

        if not options['dry_run']:
            self.stdout.write(self.style.SUCCESS("\nCross-app sync instructions are ready."))
            self.stdout.write(
                "\nFlow: Bundled app POST → EndpointDataExtractor → Pub/Sub → "
                "OdooCustomerSync → Odoo partner created/updated"
            )
