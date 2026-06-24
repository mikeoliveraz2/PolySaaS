"""
When migrate_all_schemas skips a tenant, polysniffer.0002 may exist only on public.
Ensure TrafficLog columns exist on the active tenant schema before ORM queries.
"""
from __future__ import annotations

import re


def _safe_schema(name: str) -> str | None:
    if not name or not isinstance(name, str):
        return None
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        return None
    return name


def ensure_trafficlog_capture_columns(request=None, schema_name: str | None = None) -> None:
    """
    ADD COLUMN IF NOT EXISTS for capture_source / client_path on polysniffer_trafficlog.
    No-op if table missing (raises — caller should handle) or columns already there.
    """
    from django.db import connection
    from dose.utils import get_current_tenant

    if schema_name is None:
        if request is not None:
            tenant = get_current_tenant(request) or getattr(request, "tenant", None)
            raw = (
                tenant.schema_name
                if tenant and getattr(tenant, "schema_name", None)
                else "public"
            )
        else:
            raw = "public"
        schema_name = _safe_schema(raw) or "public"
    else:
        schema_name = _safe_schema(schema_name) or "public"

    stmts = [
        f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
        f"ADD COLUMN IF NOT EXISTS capture_source VARCHAR(32) DEFAULT '' NOT NULL",
        f'ALTER TABLE "{schema_name}".polysniffer_trafficlog '
        f"ADD COLUMN IF NOT EXISTS client_path VARCHAR(500) DEFAULT '' NOT NULL",
        f'CREATE INDEX IF NOT EXISTS polysniffer_trafficlog_capture_source_idx '
        f'ON "{schema_name}".polysniffer_trafficlog (capture_source)',
    ]
    try:
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema_name}", public')
            for stmt in stmts:
                cur.execute(stmt)
    except Exception:
        # Table may not exist in this schema yet; let the real error surface
        raise
