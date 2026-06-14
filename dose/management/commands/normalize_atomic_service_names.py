"""
Normalize legacy atomic service names in tenant data.

Rewrites Instruction.executescript, Parameter.matchingKey, and (public)
AtomicService.service_name from old *Service class names to current registry
names (see LEGACY_ATOMIC_SERVICE_ALIASES in atomic_services_registry).

Usage:
  python manage.py normalize_atomic_service_names --dry-run
  python manage.py normalize_atomic_service_names
  python manage.py normalize_atomic_service_names --schema olient
"""
from django.core.management.base import BaseCommand
from django.db import connection

from dose.management.schema_utils import assert_safe_schema_identifier, set_search_path
from dose.models import Tenant
from dose.services.atomic_services_registry import LEGACY_ATOMIC_SERVICE_ALIASES


def _table_exists(schema: str, table: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            )
            """,
            [schema, table],
        )
        return cursor.fetchone()[0]


def _collect_schemas(schema_filter: str | None) -> list[str]:
    if schema_filter:
        assert_safe_schema_identifier(schema_filter)
        return [schema_filter]
    schemas = ["public"]
    set_search_path("public")
    for tenant in Tenant.objects.all().order_by("schema_name"):
        name = (tenant.schema_name or "").strip()
        if name and name.lower() != "public" and name not in schemas:
            schemas.append(name)
    return schemas


class Command(BaseCommand):
    help = "Rewrite legacy *Service executescript/matchingKey values to current atomic service class names."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without writing to the database.",
        )
        parser.add_argument(
            "--schema",
            default="",
            help="Limit to one PostgreSQL schema (e.g. olient, public).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        schema_filter = (options["schema"] or "").strip() or None
        schemas = _collect_schemas(schema_filter)

        totals = {
            "instruction_executescript": 0,
            "instruction_parameters_json": 0,
            "parameter_matching_key": 0,
            "atomic_service_name": 0,
            "parameter_skipped_collision": 0,
        }

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no database writes"))

        for schema in schemas:
            assert_safe_schema_identifier(schema)
            if not _table_exists(schema, "dose_instruction"):
                self.stdout.write(f"  [{schema}] dose_instruction missing — skip")
                continue

            set_search_path(schema)
            schema_counts = self._normalize_schema(schema, dry_run=dry_run)
            for key, count in schema_counts.items():
                totals[key] += count
            if any(schema_counts.values()):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [{schema}] "
                        + ", ".join(f"{k}={v}" for k, v in schema_counts.items() if v)
                    )
                )

        if schema_filter is None or schema_filter == "public":
            set_search_path("public")
            if _table_exists("public", "dose_atomicservice"):
                count = self._normalize_atomic_service_catalog(dry_run=dry_run)
                totals["atomic_service_name"] += count
                if count:
                    self.stdout.write(
                        self.style.SUCCESS(f"  [public] atomic_service_name={count}")
                    )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Done. "
                + ", ".join(f"{k}={v}" for k, v in totals.items() if v)
                + (" (dry run)" if dry_run else "")
            )
        )

    def _normalize_schema(self, schema: str, *, dry_run: bool) -> dict:
        from dose.models import Instruction

        counts = {
            "instruction_executescript": 0,
            "instruction_parameters_json": 0,
            "parameter_matching_key": 0,
            "parameter_skipped_collision": 0,
        }

        legacy_names = list(LEGACY_ATOMIC_SERVICE_ALIASES.keys())
        instructions = Instruction.objects.filter(executescript__in=legacy_names)
        for instruction in instructions:
            legacy = (instruction.executescript or "").strip()
            canonical = LEGACY_ATOMIC_SERVICE_ALIASES.get(legacy, legacy)
            self.stdout.write(
                f"    Instruction id={instruction.id}: executescript "
                f"{legacy!r} -> {canonical!r}"
            )
            counts["instruction_executescript"] += 1
            if not dry_run:
                instruction.executescript = canonical
                instruction.save(update_fields=["executescript"])

        for instruction in Instruction.objects.exclude(parameters_json__isnull=True):
            payload = instruction.parameters_json
            if not isinstance(payload, dict):
                continue
            for field in ("MatchingKey", "matchingKey"):
                legacy = (payload.get(field) or "").strip()
                if legacy not in LEGACY_ATOMIC_SERVICE_ALIASES:
                    continue
                canonical = LEGACY_ATOMIC_SERVICE_ALIASES[legacy]
                self.stdout.write(
                    f"    Instruction id={instruction.id}: parameters_json.{field} "
                    f"{legacy!r} -> {canonical!r}"
                )
                counts["instruction_parameters_json"] += 1
                if not dry_run:
                    payload[field] = canonical
                    instruction.parameters_json = payload
                    instruction.save(update_fields=["parameters_json"])
                break

        try:
            from parameters.models import Parameter
        except ImportError:
            Parameter = None

        if Parameter is not None and _table_exists(schema, "parameters_parameter"):
            params = Parameter.objects.filter(matchingKey__in=legacy_names)
            for param in params:
                legacy = (param.matchingKey or "").strip()
                canonical = LEGACY_ATOMIC_SERVICE_ALIASES.get(legacy, legacy)
                collision = Parameter.objects.filter(matchingKey=canonical).exclude(
                    pk=param.pk
                ).exists()
                if collision:
                    self.stdout.write(
                        self.style.WARNING(
                            f"    Parameter id={param.id}: skip {legacy!r} -> {canonical!r} "
                            f"(row with matchingKey={canonical!r} already exists)"
                        )
                    )
                    counts["parameter_skipped_collision"] += 1
                    continue
                self.stdout.write(
                    f"    Parameter id={param.id}: matchingKey "
                    f"{legacy!r} -> {canonical!r}"
                )
                counts["parameter_matching_key"] += 1
                if not dry_run:
                    param.matchingKey = canonical
                    param.save(update_fields=["matchingKey"])

        return counts

    def _normalize_atomic_service_catalog(self, *, dry_run: bool) -> int:
        from dose.models import AtomicService

        count = 0
        legacy_names = list(LEGACY_ATOMIC_SERVICE_ALIASES.keys())
        for row in AtomicService.objects.filter(service_name__in=legacy_names):
            legacy = (row.service_name or "").strip()
            canonical = LEGACY_ATOMIC_SERVICE_ALIASES.get(legacy, legacy)
            collision = (
                AtomicService.objects.filter(service_name=canonical)
                .exclude(pk=row.pk)
                .exists()
            )
            if collision:
                self.stdout.write(
                    self.style.WARNING(
                        f"    AtomicService id={row.id}: skip {legacy!r} -> {canonical!r} "
                        f"(service_name={canonical!r} already exists)"
                    )
                )
                continue
            self.stdout.write(
                f"    AtomicService id={row.id}: service_name "
                f"{legacy!r} -> {canonical!r}"
            )
            count += 1
            if not dry_run:
                row.service_name = canonical
                row.save(update_fields=["service_name"])
        return count
