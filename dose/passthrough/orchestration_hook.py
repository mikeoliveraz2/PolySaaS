"""
Orchestration Hook — bridges PolySniffer traffic capture and dynamic orchestration.

Called from forwarding.py after every passthrough request is captured. Checks if
the upstream path matches any Instruction for the current tenant. If matched,
executes the corresponding atomic service and records CallBackData + DoseMessage.

Architecture (user's design):
  1. PolySniffer captures traffic (TrafficLog) — already done in forwarding.py
  2. This hook detects matching Instructions by path substring match
  3. Executes the atomic service (e.g. EndpointDataExtractorService)
  4. Records CallBackData for audit/visibility
  5. Creates DoseMessage so the display shell toast can show it

This module does NOT bypass the MQ architecture — EndpointDataExtractorService
still publishes to MQ topics. This hook is the "signal" that triggers it.
"""
import json
import logging

from django.db import connection

logger = logging.getLogger(__name__)


def check_orchestration_trigger(request, upstream_path, app_name, tenant):
    """
    Check if the captured upstream_path matches any Instruction and fire it.

    Args:
        request: Django HttpRequest (with .user, .tenant, .body)
        upstream_path: The path on the upstream app (e.g. /web/dataset/call_kw/account.move/create)
        app_name: Name of the bundled app (e.g. 'odoo')
        tenant: Tenant model instance or None
    """
    if not tenant:
        return

    method = request.method.upper()
    normalized_path = upstream_path.rstrip('/').lower()

    # Ensure we're in the right schema
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

    from dose.models import Instruction
    instructions = Instruction.objects.filter(
        requestmethod=method, direction='REQ', tenant=tenant
    )

    matched = [
        instr for instr in instructions
        if normalized_path == instr.requestpath.rstrip('/').lower()
    ]

    if not matched:
        return

    print(f"[ORCHESTRATION HOOK] Matched {len(matched)} instruction(s) for {method} {upstream_path}")
    logger.info("[ORCHESTRATION HOOK] Matched %d instruction(s) for %s %s", len(matched), method, upstream_path)

    from dose.services.atomic_services_registry import ATOMIC_SERVICE_REGISTRY, init_atomic_services_registry
    init_atomic_services_registry()

    for instruction_row in matched:
        executescript_name = getattr(instruction_row, 'executescript', None) or ''
        atomic_result = {'status': 'success', 'path': upstream_path, 'method': method}

        if executescript_name:
            cls = ATOMIC_SERVICE_REGISTRY.get(executescript_name)
            if not cls or not hasattr(cls, 'execute_and_save'):
                logger.warning("[ORCHESTRATION HOOK] No service class for '%s'", executescript_name)
            else:
                print(f"[ORCHESTRATION HOOK] Executing {executescript_name} for instruction id={instruction_row.id}")
                try:
                    atomic_result = cls.execute_and_save(request, instruction_row)
                except Exception as exc:
                    logger.error("[ORCHESTRATION HOOK] %s failed: %s", executescript_name, exc)
                    atomic_result = {'status': 'error', 'error': str(exc)}
        else:
            print(f"[ORCHESTRATION HOOK] Instruction id={instruction_row.id} matched (no executescript) — recording event")

        # Save CallBackData
        _save_callback_data(request, instruction_row, atomic_result, tenant)

        # Create DoseMessage for display shell toast
        _create_dose_message(request, instruction_row, atomic_result, executescript_name or 'OrchestratedEvent')


def _save_callback_data(request, instruction_row, atomic_result, tenant):
    """Persist orchestration result to CallBackData for audit trail."""
    try:
        from dose.models import CallBackData
        description = getattr(instruction_row, 'description', '') or f"{instruction_row.executescript} executed"
        result_json = json.dumps(atomic_result) if not isinstance(atomic_result, str) else atomic_result

        CallBackData.objects.create(
            matchingEventKey=getattr(instruction_row, 'eventKey', None),
            description=description,
            callbackdata=result_json,
            parameters_json='[]',
            tenant=tenant,
        )
        logger.info("[ORCHESTRATION HOOK] CallBackData saved for eventKey=%s", instruction_row.eventKey)
    except Exception as exc:
        logger.error("[ORCHESTRATION HOOK] Failed to save CallBackData: %s", exc)


def _create_dose_message(request, instruction_row, atomic_result, service_name):
    """Create a DoseMessage so the display shell toast poller picks it up."""
    try:
        from dose.models import DoseMessage
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            user = None

        status = 'success'
        if isinstance(atomic_result, dict):
            if atomic_result.get('status') in ('error', 'failed'):
                status = 'error'

        event_key = getattr(instruction_row, 'eventKey', '') or ''
        msg_text = f"Orchestration: {service_name} executed ({event_key})"
        if isinstance(atomic_result, dict) and atomic_result.get('invoice_ref'):
            msg_text = f"Invoice {atomic_result['invoice_ref']} detected — orchestration triggered"

        DoseMessage.objects.create(
            user=user,
            message=msg_text,
            level=status,
        )
        logger.info("[ORCHESTRATION HOOK] DoseMessage created: %s", msg_text)
    except Exception as exc:
        logger.error("[ORCHESTRATION HOOK] Failed to create DoseMessage: %s", exc)
