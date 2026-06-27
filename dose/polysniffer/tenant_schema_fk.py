"""Ensure tenant-schema FK targets exist for PolySniffer models."""
from __future__ import annotations

import logging

from django.db import connection

logger = logging.getLogger(__name__)


def ensure_auth_user_fk_row(user, schema_name: str) -> None:
    """
    Mirror public.auth_user into the tenant schema.

    polysniffer_trafficlog.user_id FK resolves against auth_user in the active
    search_path schema. PolySaaS users live in public.auth_user; each tenant schema
    has its own auth_user table (created by migrations) but lacks those rows.
    Without this mirror the insert fails with an FK violation.
    """
    if not user or not schema_name or schema_name == "public":
        return
    user_id = getattr(user, "pk", None)
    if not user_id:
        return
    try:
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema_name}", public')
            cur.execute(
                """
                INSERT INTO auth_user (
                    id, password, last_login, is_superuser, username,
                    first_name, last_name, email, is_staff, is_active, date_joined
                )
                SELECT id, password, last_login, is_superuser, username,
                       first_name, last_name, email, is_staff, is_active, date_joined
                FROM public.auth_user
                WHERE id = %s
                ON CONFLICT (id) DO NOTHING
                """,
                [user_id],
            )
    except Exception as exc:
        logger.warning(
            "ensure_auth_user_fk_row failed for user %s in %s: %s",
            user_id,
            schema_name,
            exc,
        )


def ensure_tenant_fk_row(tenant_slug: str, schema_name: str | None = None) -> None:
    """
    Mirror public.dose_tenant into the tenant schema.

    polysniffer_trafficcapture.tenant_id FK resolves against dose_tenant in the
    active search_path schema (e.g. olient), not public. Older tenants may lack
    that mirror row even when public.dose_tenant is correct.
    """
    slug = (tenant_slug or "").strip()
    if not slug:
        return

    schema = (schema_name or "").strip()
    if not schema:
        from dose.models import Tenant

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")
        tenant = Tenant.objects.filter(pk=slug).first()
        if not tenant:
            return
        schema = (tenant.schema_name or "").strip()
    if not schema or schema == "public":
        return

    try:
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}", public')
            cur.execute(
                """
                INSERT INTO dose_tenant (
                    slug, name, schema_name, description, tagline, primary_color,
                    logo, created_at, is_active
                )
                SELECT slug, name, schema_name, description, tagline, primary_color,
                       logo, created_at, is_active
                FROM public.dose_tenant
                WHERE slug = %s
                ON CONFLICT (slug) DO NOTHING
                """,
                [slug],
            )
    except Exception as exc:
        logger.warning("ensure_tenant_fk_row failed for %s/%s: %s", slug, schema, exc)
