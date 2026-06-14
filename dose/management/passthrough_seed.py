"""
Seed PassThroughEndpoint rows into a new tenant schema from public or another donor schema.

Every tenant schema gets the full endpoint catalog; sidebar filters by TenantApp subscription.
"""
from __future__ import annotations

import logging

from django.db import connection

from dose.models import PassThroughEndpoint, Tenant

logger = logging.getLogger(__name__)


def seed_passthrough_endpoints(tenant, *, log=None) -> int:
    """
    Copy passthrough endpoint rows into tenant.schema_name when empty.

    Returns number of rows created (0 if skipped or no donor).
    """
    emit = log or logger.info
    target_schema = (getattr(tenant, 'schema_name', None) or '').strip()
    if not target_schema or target_schema.lower() == 'public':
        return 0

    fields_to_copy = [
        f.name
        for f in PassThroughEndpoint._meta.fields
        if f.name not in {'id', 'created_at'}
    ]

    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{target_schema}",public;')
    target_count = PassThroughEndpoint.objects.count()
    if target_count > 0:
        emit(f"Passthrough endpoints already present in {target_schema} ({target_count}); skip seed.")
        return 0

    source_rows = []
    source_schema = None
    candidate_schemas = ['public']
    candidate_schemas += list(
        Tenant.objects.exclude(schema_name__in=['public', target_schema]).values_list(
            'schema_name', flat=True
        )
    )

    for schema in candidate_schemas:
        if not schema:
            continue
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}",public;')
        rows = list(PassThroughEndpoint.objects.all().values(*fields_to_copy))
        if rows:
            source_rows = rows
            source_schema = schema
            break

    if not source_rows:
        emit(f"No donor passthrough endpoints found; left {target_schema} empty.")
        return 0

    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{target_schema}",public;')
    for row in source_rows:
        PassThroughEndpoint.objects.create(**row)

    emit(f"Seeded {len(source_rows)} passthrough endpoints from {source_schema} -> {target_schema}")
    return len(source_rows)
