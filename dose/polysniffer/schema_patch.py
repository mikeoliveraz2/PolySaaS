"""
When migrate_all_schemas skips a tenant, polysniffer tables may be missing or legacy-shaped.
Ensure tenant-scoped PolySniffer tables exist and legacy public columns allow ORM inserts.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_REFERENCE_SCHEMA = "polysaast125"
_POLYSNIFFER_TABLES = ("polysniffer_trafficlog", "polysniffer_trafficcapture")
_LEGACY_VARCHAR_COLS = (
    "session_id",
    "capture_type",
    "error_message",
    "importance",
    "importance_reason",
)


def _safe_schema(name: str) -> str | None:
    if not name or not isinstance(name, str):
        return None
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        return None
    return name


def _resolve_schema(request=None, schema_name: str | None = None) -> str:
    if schema_name is not None:
        return _safe_schema(schema_name) or "public"
    if request is not None:
        from dose.utils import get_current_tenant

        tenant = get_current_tenant(request) or getattr(request, "tenant", None)
        raw = tenant.schema_name if tenant and getattr(tenant, "schema_name", None) else "public"
        return _safe_schema(raw) or "public"
    return "public"


def _table_exists(cur, schema_name: str, table_name: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        [schema_name, table_name],
    )
    return bool(cur.fetchone())


def _column_exists(cur, schema_name: str, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
        """,
        [schema_name, table_name, column_name],
    )
    return bool(cur.fetchone())


def _clone_table_if_missing(cur, dest_schema: str, table_name: str, ref_schema: str) -> None:
    if _table_exists(cur, dest_schema, table_name):
        return
    if not _table_exists(cur, ref_schema, table_name):
        logger.warning(
            "schema_patch: cannot clone %s — missing reference %s.%s",
            dest_schema,
            ref_schema,
            table_name,
        )
        return
    cur.execute(
        f'CREATE TABLE IF NOT EXISTS "{dest_schema}"."{table_name}" '
        f'(LIKE "{ref_schema}"."{table_name}" INCLUDING DEFAULTS INCLUDING IDENTITY INCLUDING INDEXES)'
    )


def _ensure_tenant_polysniffer_tables(cur, schema_name: str) -> None:
    if schema_name == "public":
        return
    for table_name in _POLYSNIFFER_TABLES:
        _clone_table_if_missing(cur, schema_name, table_name, _REFERENCE_SCHEMA)


def _relax_legacy_public_trafficlog(cur, schema_name: str) -> None:
    if schema_name != "public" or not _table_exists(cur, schema_name, "polysniffer_trafficlog"):
        return
    if not _column_exists(cur, schema_name, "polysniffer_trafficlog", "session_id"):
        return
    for col in _LEGACY_VARCHAR_COLS:
        if _column_exists(cur, schema_name, "polysniffer_trafficlog", col):
            cur.execute(
                f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
                f'ALTER COLUMN "{col}" DROP NOT NULL'
            )
            cur.execute(
                f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
                f"ALTER COLUMN \"{col}\" SET DEFAULT ''"
            )
    if _column_exists(cur, schema_name, "polysniffer_trafficlog", "repeat_count"):
        cur.execute(
            f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
            f'ALTER COLUMN "repeat_count" DROP NOT NULL'
        )
        cur.execute(
            f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
            f'ALTER COLUMN "repeat_count" SET DEFAULT 0'
        )


def _ensure_modern_capture_columns(cur, schema_name: str) -> None:
    if not _table_exists(cur, schema_name, "polysniffer_trafficlog"):
        return
    stmts = [
        f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
        f"ADD COLUMN IF NOT EXISTS capture_source VARCHAR(32) DEFAULT '' NOT NULL",
        f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
        f"ADD COLUMN IF NOT EXISTS client_path VARCHAR(500) DEFAULT '' NOT NULL",
        f'CREATE INDEX IF NOT EXISTS polysniffer_trafficlog_capture_source_idx '
        f'ON "{schema_name}".polysniffer_trafficlog (capture_source)',
    ]
    for stmt in stmts:
        cur.execute(stmt)


def ensure_trafficlog_capture_columns(request=None, schema_name: str | None = None) -> None:
    """
    Ensure PolySniffer tables/columns exist for the active tenant schema before ORM writes.
    """
    from django.db import connection

    schema_name = _resolve_schema(request, schema_name)

    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema_name}", public')
        _ensure_tenant_polysniffer_tables(cur, schema_name)
        _relax_legacy_public_trafficlog(cur, "public")
        _ensure_modern_capture_columns(cur, schema_name)
        if schema_name == "public":
            _ensure_modern_capture_columns(cur, "public")
