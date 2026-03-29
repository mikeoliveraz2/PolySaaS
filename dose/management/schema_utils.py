"""
PostgreSQL schema helpers for session-based multi-tenancy.
Tenant schemas must not use reserved names (e.g. public).
"""
import re

from django.db import connection

# Unquoted PostgreSQL identifiers: start with letter or underscore, then alnum/underscore.
_SAFE_SCHEMA = re.compile(r"^[a-z_][a-z0-9_]*$", re.IGNORECASE)


def assert_safe_schema_identifier(name: str) -> None:
    if not name or not _SAFE_SCHEMA.match(name):
        raise ValueError(f"Invalid PostgreSQL schema identifier: {name!r}")


def tenant_schema_disallowed_reason(schema_name: str) -> str | None:
    """Return a reason string if schema_name must not be used for a Tenant row, else None."""
    if not schema_name or not str(schema_name).strip():
        return "schema_name is empty"
    if not _SAFE_SCHEMA.match(schema_name):
        return "schema_name must be a simple identifier (letters, digits, underscore)"
    low = schema_name.lower()
    if low == "public":
        return (
            'schema "public" holds shared tables (e.g. dose_tenant); '
            "use a dedicated name such as your tenant slug"
        )
    if low in ("pg_catalog", "information_schema"):
        return f"schema {schema_name!r} is reserved by PostgreSQL"
    return None


def set_search_path(schema_name: str) -> None:
    """search_path = <schema>, public — fall back to public for shared models (runtime / admin)."""
    assert_safe_schema_identifier(schema_name)
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name},public;")


def set_search_path_for_migrations(schema_name: str) -> None:
    """
    search_path = <schema>, pg_catalog only (no public).
    Required for migrate: otherwise django_migrations resolves in public and Django skips applying
    migrations for empty tenant schemas.
    """
    assert_safe_schema_identifier(schema_name)
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name}, pg_catalog;")


def create_tenant_schema_if_missing(schema_name: str) -> None:
    """
    Create an empty tenant schema only. Do NOT copy table DDL from public:
    copying with LIKE creates tables without django_migrations rows, which breaks migrate.
    After creating a tenant, run: python manage.py migrate
    """
    reason = tenant_schema_disallowed_reason(schema_name)
    if reason:
        raise ValueError(reason)
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
