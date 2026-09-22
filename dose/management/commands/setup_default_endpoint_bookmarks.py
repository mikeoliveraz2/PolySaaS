from django.core.management.base import BaseCommand, CommandError
from django.db import connection, models

from dose.endpoint_actions import adapter_for_endpoint
from dose.management.schema_utils import assert_safe_schema_identifier

# Superseded by key=contacts → *.capture_contacts (shared Captured Topics queue).
OBSOLETE_BOOKMARK_KEYS = frozenset({"capture-contacts"})
OBSOLETE_CONTACT_TARGETS = frozenset(
    {
        "odoo.list_contacts",
        "hubspot.list_contacts",
        "mattermost.list_contacts",
        "slack.list_contacts",
    }
)


class Command(BaseCommand):
    help = "Publish registered default bookmarks into one tenant schema."

    def add_arguments(self, parser):
        parser.add_argument("--schema", required=True)

    def handle(self, *args, **options):
        schema = options["schema"].strip()
        assert_safe_schema_identifier(schema)
        if schema.lower() == "public":
            raise CommandError("Bookmarks are tenant-owned and cannot be seeded in public.")

        from dose.models import EndpointBookmark, PassThroughEndpoint

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = %s)",
                [schema],
            )
            if not cursor.fetchone()[0]:
                raise CommandError(f"Tenant schema does not exist: {schema}")
            cursor.execute(
                "SELECT to_regclass(%s), to_regclass(%s)",
                [
                    f"{schema}.{PassThroughEndpoint._meta.db_table}",
                    f"{schema}.{EndpointBookmark._meta.db_table}",
                ],
            )
            endpoint_table, bookmark_table = cursor.fetchone()
            if endpoint_table is None or bookmark_table is None:
                raise CommandError(
                    f"Tenant schema {schema} is missing endpoint/bookmark tables."
                )
            cursor.execute(f'SET search_path TO "{schema}",public;')
        created_count = 0
        updated_count = 0
        for endpoint in PassThroughEndpoint.objects.filter(is_enabled=True):
            adapter = adapter_for_endpoint(endpoint)
            for order, definition in enumerate(
                getattr(adapter, "default_bookmarks", ()) or (),
                start=1,
            ):
                _bookmark, created = EndpointBookmark.objects.update_or_create(
                    endpoint=endpoint,
                    key=definition["key"],
                    defaults={
                        "title": definition["title"],
                        "destination_type": definition["destination_type"],
                        "target": definition["target"],
                        "icon": definition.get("icon", "🔖"),
                        "description": definition.get("description", ""),
                        "sort_order": order * 10,
                        "is_active": True,
                    },
                )
                created_count += int(created)
                updated_count += int(not created)
            retired = EndpointBookmark.objects.filter(
                endpoint=endpoint,
                is_active=True,
            ).filter(
                models.Q(key__in=OBSOLETE_BOOKMARK_KEYS)
                | models.Q(target__in=OBSOLETE_CONTACT_TARGETS)
            ).update(is_active=False)
            if retired:
                self.stdout.write(
                    f"  {endpoint.get_menu_title()}: deactivated {retired} obsolete Contacts bookmark(s)"
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"{schema}: created={created_count}, updated={updated_count}"
            )
        )
