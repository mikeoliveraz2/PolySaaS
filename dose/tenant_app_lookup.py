"""
Tenant-scoped TenantApp lookups — always in the tenant schema, never public.

Per tenant isolation rules, TenantApp rows (OAuth tokens, session cookies,
extra_config) are tenant-owned and must be read/written with search_path set
to that tenant's schema.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from django.db import connection


def _schema_name(tenant) -> str | None:
    schema = getattr(tenant, "schema_name", None) if tenant else None
    if not schema or schema == "public":
        return None
    return schema


@contextmanager
def tenant_schema_search_path(tenant) -> Iterator[bool]:
    """Set search_path to {tenant_schema},public for the block; restore after."""
    schema = _schema_name(tenant)
    if not schema:
        yield False
        return

    original_sp = None
    try:
        with connection.cursor() as cur:
            cur.execute("SHOW search_path")
            row = cur.fetchone()
            original_sp = row[0] if row else None
            cur.execute(f'SET search_path TO "{schema}", public;')
        yield True
    finally:
        if original_sp:
            try:
                with connection.cursor() as cur:
                    cur.execute(f"SET search_path TO {original_sp}")
            except Exception:
                pass


@contextmanager
def tenant_schema_search_path_by_name(schema: str) -> Iterator[bool]:
    """Same as tenant_schema_search_path but when only schema slug is known."""
    if not schema or schema == "public":
        yield False
        return

    original_sp = None
    try:
        with connection.cursor() as cur:
            cur.execute("SHOW search_path")
            row = cur.fetchone()
            original_sp = row[0] if row else None
            cur.execute(f'SET search_path TO "{schema}", public;')
        yield True
    finally:
        if original_sp:
            try:
                with connection.cursor() as cur:
                    cur.execute(f"SET search_path TO {original_sp}")
            except Exception:
                pass


def get_tenant_app_in_schema(tenant, app_name: str):
    """Load one TenantApp row from the tenant schema (not public)."""
    from dose.models import TenantApp

    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return None
        return (
            TenantApp.objects.filter(app_name=app_name).first()
            or TenantApp.objects.filter(app_name__icontains=app_name).first()
        )


def get_tenant_app_in_schema_by_name(schema: str, app_name: str):
    """Load TenantApp when only schema slug is available (no Tenant instance)."""
    from dose.models import TenantApp

    with tenant_schema_search_path_by_name(schema) as ok:
        if not ok:
            return None
        return (
            TenantApp.objects.filter(app_name=app_name).first()
            or TenantApp.objects.filter(app_name__icontains=app_name).first()
        )


def subscribed_app_names(tenant) -> set[str]:
    """Active/provisioning app_name values from the tenant schema."""
    from dose.models import TenantApp

    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return set()
        return set(
            TenantApp.objects.filter(
                status__in=("active", "provisioning"),
            ).values_list("app_name", flat=True)
        )


def ensure_tenant_app_in_schema(tenant, app_name: str, **defaults):
    """Get or create TenantApp in the tenant schema."""
    from dose.models import TenantApp

    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return None, False
        ta = TenantApp.objects.filter(app_name=app_name).first()
        if ta:
            return ta, False
        ta = TenantApp(tenant=tenant, app_name=app_name, **defaults)
        ta.save()
        return ta, True
