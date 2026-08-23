from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = (
        "Create endpoint_bookmark in every existing tenant app schema. "
        "Recovery path for installations whose legacy migration history is stale."
    )

    def handle(self, *args, **options):
        from dose.models import EndpointBookmark

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
            cursor.execute(
                """
                SELECT n.nspname
                FROM pg_namespace n
                WHERE n.nspname <> 'public'
                  AND n.nspname NOT LIKE 'pg_%'
                  AND n.nspname <> 'information_schema'
                  AND to_regclass(format('%I.dose_passthroughendpoint', n.nspname)) IS NOT NULL
                ORDER BY n.nspname
                """
            )
            schemas = [row[0] for row in cursor.fetchall()]

        failures = []
        created = []
        existing = []
        for schema in schemas:
            try:
                qualified_table = f"{schema}.{EndpointBookmark._meta.db_table}"
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass(%s)", [qualified_table])
                    table_exists = cursor.fetchone()[0] is not None
                if table_exists:
                    existing.append(schema)
                    continue
                with connection.schema_editor() as schema_editor:
                    quoted_schema = connection.ops.quote_name(schema)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f"SET LOCAL search_path TO {quoted_schema}, public;"
                        )
                    schema_editor.create_model(EndpointBookmark)
                created.append(schema)
            except Exception as exc:
                failures.append((schema, str(exc)))

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
        self.stdout.write(
            self.style.SUCCESS(
                f"Endpoint bookmarks: created={len(created)}, existing={len(existing)}"
            )
        )
        if created:
            self.stdout.write("Created: " + ", ".join(created))
        if failures:
            for schema, error in failures:
                self.stderr.write(f"{schema}: {error}")
            raise CommandError(
                f"Endpoint bookmark bootstrap failed for {len(failures)} schema(s)"
            )
