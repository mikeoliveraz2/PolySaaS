"""
Load or update ``parameters.Parameter`` rows from a CSV file on disk (no admin UI).

Typical usage::

    python manage.py import_parameters_from_csv --path ./data/params.csv
    python manage.py import_parameters_from_csv --path ./data/params.csv --schema olient --dry-run

CSV format (first row = headers). Required column: ``matchingKey`` (or ``matching_key``).
Optional: ``sequence``, ``description``, ``param1`` … ``param10``, ``param_kwargs_json`` (JSON object as a single cell).

``--schema`` sets PostgreSQL ``search_path`` before writes (default ``public``). Use your tenant
schema name for tenant-scoped parameters.

This command does not upload files; pass a path readable by the process (local dev, Render Shell
with a file under ``/tmp``, etc.).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from dose.management.schema_utils import assert_safe_schema_identifier, tenant_schema_disallowed_reason
from parameters.models import Parameter

# Header aliases → model field names
ALIASES = {
    "matching_key": "matchingKey",
    "matchingkey": "matchingKey",
    "param_kwargs": "param_kwargs_json",
    "kwargs_json": "param_kwargs_json",
    "json": "param_kwargs_json",
}


class Command(BaseCommand):
    help = "Import/update Parameter rows from a CSV file path (no UI)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Filesystem path to UTF-8 CSV (header row required).",
        )
        parser.add_argument(
            "--schema",
            type=str,
            default="public",
            help='PostgreSQL schema for parameters.Parameter (default: "public").',
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate only; do not write the database.",
        )
        parser.add_argument(
            "--merge-kwargs",
            action="store_true",
            help="When param_kwargs_json is present, deep-merge into existing param_kwargs_json instead of replacing.",
        )
        parser.add_argument(
            "--delimiter",
            type=str,
            default=",",
            help="Single-character CSV delimiter (default: comma).",
        )

    def handle(self, *args, **options):
        path = Path(options["path"]).expanduser()
        if not path.is_file():
            raise CommandError(f"Not a file or missing: {path}")

        schema = (options["schema"] or "public").strip()
        if schema.lower() != "public":
            bad = tenant_schema_disallowed_reason(schema)
            if bad:
                raise CommandError(bad)
            assert_safe_schema_identifier(schema)

        delim = (options["delimiter"] or ",")[:1]
        if not delim:
            raise CommandError("--delimiter must be non-empty")

        dry = options["dry_run"]
        merge_kwargs = options["merge_kwargs"]

        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh, delimiter=delim)
            if not reader.fieldnames:
                raise CommandError("CSV has no header row.")
            headers_canon = {ALIASES.get(h.strip().lower(), h.strip()) for h in reader.fieldnames}
            if "matchingKey" not in headers_canon:
                raise CommandError(
                    'CSV header must include a matchingKey column (or matching_key / matchingkey).'
                )

            rows = []
            for raw in reader:
                row = {}
                for k, v in raw.items():
                    if k is None:
                        continue
                    key = ALIASES.get(k.strip().lower(), k.strip())
                    row[key] = (v or "").strip() if isinstance(v, str) else v
                if not any(row.values()):
                    continue
                rows.append(row)

        if not rows:
            raise CommandError("No data rows after header.")

        created = 0
        updated = 0
        skipped = 0

        def norm_key(d, *names):
            for n in names:
                if n in d and d[n]:
                    return d[n]
                low = {k.lower(): v for k, v in d.items()}
                for n in names:
                    if n.lower() in low and low[n.lower()]:
                        return low[n.lower()]
            return ""

        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}", public;')

        for i, row in enumerate(rows, start=2):
            mk = norm_key(row, "matchingKey", "matching_key")
            if not mk:
                self.stdout.write(self.style.WARNING(f"Row {i}: skip (no matchingKey)"))
                skipped += 1
                continue

            seq_s = norm_key(row, "sequence") or "1"
            try:
                seq = int(seq_s)
            except ValueError:
                raise CommandError(f"Row {i}: invalid sequence {seq_s!r}")

            desc = norm_key(row, "description") or "N/A"
            pdata = {}
            for n in range(1, 11):
                key = f"param{n}"
                val = norm_key(row, key)
                if val:
                    pdata[key] = val
                else:
                    pdata[key] = "N/A"

            kwargs_cell = norm_key(row, "param_kwargs_json", "param_kwargs", "kwargs_json")
            kwargs_obj = None
            if kwargs_cell:
                try:
                    kwargs_obj = json.loads(kwargs_cell)
                except json.JSONDecodeError as e:
                    raise CommandError(f"Row {i}: param_kwargs_json is not valid JSON: {e}") from e
                if not isinstance(kwargs_obj, dict):
                    raise CommandError(f"Row {i}: param_kwargs_json must be a JSON object.")

            if dry:
                self.stdout.write(f"[dry-run] row {i}: {mk!r} seq={seq} desc={desc!r}")
                continue

            with transaction.atomic():
                obj, was_created = Parameter.objects.get_or_create(
                    matchingKey=mk,
                    sequence=seq,
                    defaults={
                        "description": desc,
                        "param_kwargs_json": kwargs_obj,
                        **{f"param{n}": pdata[f"param{n}"] for n in range(1, 11)},
                    },
                )
                if was_created:
                    created += 1
                    continue
                # update existing
                obj.description = desc
                for n in range(1, 11):
                    setattr(obj, f"param{n}", pdata[f"param{n}"])
                if kwargs_obj is not None:
                    if merge_kwargs and obj.param_kwargs_json and isinstance(obj.param_kwargs_json, dict):
                        merged = {**obj.param_kwargs_json, **kwargs_obj}
                        obj.param_kwargs_json = merged
                    else:
                        obj.param_kwargs_json = kwargs_obj
                obj.save()
                updated += 1

        if dry:
            self.stdout.write(self.style.WARNING(f"[dry-run] {len(rows)} row(s) validated (schema={schema})."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Done (schema={schema}): created={created}, updated={updated}, skipped={skipped}"
            )
        )
