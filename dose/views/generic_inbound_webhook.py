"""
Generic inbound webhook receiver.

ONE URL handles ALL inbound SaaS webhooks:
    POST /dose/webhook/<source>/<tenant_slug>/

Routing is fully data-driven via Instruction matching — no per-app URL entries,
no per-app view files.  Adding a new SaaS integration never touches urls.py.

How it works
------------
1.  Resolve tenant by slug (public schema).
2.  Set tenant schema.
3.  Find Instructions for this tenant whose ``source_app`` matches ``source``
    and whose ``executescript`` points to an AtomicServiceBase subclass.
4.  Call ``AtomicServiceBase.execute_and_save(fake_req, instruction)`` for each.
5.  Return 200 with a JSON results summary.

AtomicService contract
-----------------------
Each service is responsible for normalising *its own* payload format inside
``_extract_contact_props`` (or equivalent).  The generic receiver passes the
raw request body unchanged — no source-specific logic here.

Supported ``source`` values (determined by seeded Instructions, not hardcoded):
    hubspot, stripe, github, salesforce, zapier, …
"""
from __future__ import annotations

import json
import logging

from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# Registry: maps executescript name → importable dotted path.
# Add new AtomicService subclasses here as they are built.
_ATOMIC_SERVICE_REGISTRY: dict[str, str] = {
    "HubSpotToOdooContactSync": "dose.services.hubspot_to_odoo_contact_sync.HubSpotToOdooContactSync",
}


def _resolve_service(executescript: str):
    """Import and return the AtomicService class for the given executescript name."""
    dotted = _ATOMIC_SERVICE_REGISTRY.get(executescript)
    if not dotted:
        return None
    module_path, class_name = dotted.rsplit(".", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name, None)


@csrf_exempt
def generic_inbound_webhook(request, source: str, tenant_slug: str):
    """
    POST /dose/webhook/<source>/<tenant_slug>/

    Generic inbound webhook dispatcher — routes by Instruction matching.
    Always returns 200 so the caller (HubSpot, Stripe, etc.) does not retry
    on business-logic failures.
    """
    # HubSpot and some others issue a GET probe when the workflow is saved
    if request.method in ("GET", "HEAD"):
        return HttpResponse(
            f"PolySaaS inbound webhook endpoint [{source}/{tenant_slug}] is alive.",
            status=200,
        )

    if request.method != "POST":
        return HttpResponse("OK", status=200)

    # ── 1. Resolve tenant (public schema) ────────────────────────────────────
    with connection.cursor() as cur:
        cur.execute("SET search_path TO public")

    from dose.models import Tenant
    tenant = Tenant.objects.filter(slug=tenant_slug).first()
    if not tenant:
        logger.warning(
            "[WebhookReceiver] Unknown tenant slug '%s' for source '%s'",
            tenant_slug, source,
        )
        return JsonResponse({"status": "ignored", "reason": "unknown_tenant"}, status=200)

    # ── 2. Set tenant schema ──────────────────────────────────────────────────
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

    logger.info(
        "[WebhookReceiver] source=%s tenant=%s body_len=%d",
        source, tenant_slug, len(request.body),
    )

    # ── 3. Find matching Instructions ─────────────────────────────────────────
    from dose.models import Instruction

    # Instructions are matched by source_app field if it exists,
    # otherwise fall back to filtering executescript names known for this source.
    instructions = _find_instructions_for_source(tenant, source)

    if not instructions:
        logger.info(
            "[WebhookReceiver] No Instructions found for source='%s' tenant='%s'. "
            "Run the appropriate seed command to register Instructions.",
            source, tenant_slug,
        )
        return JsonResponse({"status": "no_instruction"}, status=200)

    # ── 4. Build a minimal fake request ──────────────────────────────────────
    # execute_and_save reads request.body and request.tenant — that is all it needs.
    class _FakeRequest:
        body = request.body          # raw bytes — let the service parse them
        tenant = None
        user = None
        method = "POST"

    fake_req = _FakeRequest()
    fake_req.tenant = tenant

    # ── 5. Dispatch ───────────────────────────────────────────────────────────
    results = []
    for instruction in instructions:
        script_name = instruction.executescript or ""
        service_cls = _resolve_service(script_name)
        if not service_cls:
            logger.warning(
                "[WebhookReceiver] No AtomicService registered for executescript='%s'",
                script_name,
            )
            results.append({
                "instruction": instruction.pk,
                "status": "error",
                "error": f"No service registered for '{script_name}'",
            })
            continue

        try:
            result = service_cls.execute_and_save(fake_req, instruction)
            logger.info(
                "[WebhookReceiver] instruction pk=%s result=%s",
                instruction.pk, result,
            )
            results.append({"instruction": instruction.pk, **result})
        except Exception as exc:
            logger.error(
                "[WebhookReceiver] execute_and_save failed for instruction pk=%s: %s",
                instruction.pk, exc,
            )
            results.append({
                "instruction": instruction.pk,
                "status": "error",
                "error": str(exc),
            })

    return JsonResponse({"status": "processed", "results": results})


# ── Instruction lookup ────────────────────────────────────────────────────────

# Maps source name → executescript names that handle it.
# Driven by seeded Instructions; this dict only controls the fallback lookup
# when Instructions don't carry an explicit source_app field.
_SOURCE_TO_EXECUTESCRIPTS: dict[str, list[str]] = {
    "hubspot": ["HubSpotToOdooContactSync"],
}


def _find_instructions_for_source(tenant, source: str):
    """
    Return active Instructions for this tenant that match the incoming source.

    Lookup order:
    1.  Instructions with source_app == source (explicit, preferred).
    2.  Instructions whose executescript is in _SOURCE_TO_EXECUTESCRIPTS[source]
        (implicit fallback, avoids migration until source_app field is added).
    """
    from dose.models import Instruction
    from django.db import models as dm

    # Try explicit source_app field first (may not exist yet)
    try:
        qs = Instruction.objects.filter(tenant=tenant, source_app=source)
        if qs.exists():
            return list(qs)
    except Exception:
        pass

    # Fallback: match by known executescript names for this source
    script_names = _SOURCE_TO_EXECUTESCRIPTS.get(source.lower(), [])
    if not script_names:
        return []

    return list(
        Instruction.objects.filter(
            tenant=tenant,
            executescript__in=script_names,
        )
    )
