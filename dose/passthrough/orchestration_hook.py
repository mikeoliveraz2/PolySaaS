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


def _extract_odoo_ids(upstream_path):
    """Extract action_id and menu_id from an Odoo URL (path, query, or fragment)."""
    import re
    action_id = None
    menu_id = None
    # Odoo 17/18: /odoo/accounting → action in path; also ?action=..., #action=...
    combined = upstream_path  # search the full string including query/fragment
    m = re.search(r'(?:[?&#]|^)action=([^&# ]+)', combined)
    if m:
        action_id = m.group(1)
    m = re.search(r'(?:[?&#]|^)menu_id=(\d+)', combined)
    if m:
        menu_id = m.group(1)
    return action_id, menu_id


def _instruction_matches(instr, upstream_path, method):
    """Return True if the instruction matches this request.

    Primary match is controlled by match_type + requestpath.
    match_extra can add AND conditions:
      - {"method": "POST"}  — restrict HTTP method
      - {"menu_id": "116"}  — require menu_id in URL
      - {"action_id": "account.action_move_out_invoice_type"} — require action in URL
    """
    import re
    mt = getattr(instr, 'match_type', 'path') or 'path'
    mv = (instr.requestpath or '').strip()
    if not mv:
        return False

    extra = getattr(instr, 'match_extra', {}) or {}

    # AND: optional method restriction
    if extra.get('method') and extra['method'].upper() != method.upper():
        return False

    # AND: optional menu_id restriction
    if extra.get('menu_id'):
        _, menu_id = _extract_odoo_ids(upstream_path)
        if not (menu_id and str(extra['menu_id']) == menu_id):
            return False

    # AND: optional action_id restriction
    if extra.get('action_id'):
        action_id, _ = _extract_odoo_ids(upstream_path)
        if not (action_id and extra['action_id'].lower() in action_id.lower()):
            return False

    norm = upstream_path.lower()

    if mt in ('path', 'contains'):
        return mv.lower() in norm
    elif mt == 'action_id':
        action_id, _ = _extract_odoo_ids(upstream_path)
        return bool(action_id and mv.lower() in action_id.lower())
    elif mt == 'menu_id':
        _, menu_id = _extract_odoo_ids(upstream_path)
        return bool(menu_id and mv == menu_id)
    elif mt == 'regex':
        try:
            return bool(re.search(mv, upstream_path))
        except re.error:
            logger.warning("[ORCHESTRATION HOOK] Invalid regex in instruction id=%s: %s", instr.id, mv)
            return False
    return False


def check_orchestration_trigger(request, upstream_path, app_name, tenant,
                               direction='REQ', upstream_response=None):
    """
    Check if the captured upstream_path matches any Instruction and fire it.

    Args:
        request: Django HttpRequest (with .user, .tenant, .body)
        upstream_path: The path on the upstream app (e.g. /odoo/accounting?menu_id=116)
        app_name: Name of the bundled app (e.g. 'odoo')
        tenant: Tenant model instance or None
        direction: 'REQ' (before upstream call) or 'RES' (after response received)
        upstream_response: requests.Response object, only set when direction='RES'
    """
    if not tenant:
        return

    method = request.method.upper()

    # Ensure we're in the right schema
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

    from dose.models import Instruction
    # search_path is already set to the tenant schema above — no FK filter needed.
    instructions = Instruction.objects.filter(direction=direction)
    print(f"[ORCHESTRATION HOOK] direction={direction} found {instructions.count()} instruction(s), path={upstream_path}, method={method}")

    matched = [instr for instr in instructions if _instruction_matches(instr, upstream_path, method)]
    print(f"[ORCHESTRATION HOOK] matched {len(matched)} instruction(s) for {method} {upstream_path}")

    if not matched:
        return

    print(f"[ORCHESTRATION HOOK] Matched {len(matched)} instruction(s) for {method} {upstream_path}")
    logger.info("[ORCHESTRATION HOOK] Matched %d instruction(s) for %s %s", len(matched), method, upstream_path)

    from dose.services.atomic_services_registry import ATOMIC_SERVICE_REGISTRY, init_atomic_services_registry
    init_atomic_services_registry()

    for instruction_row in matched:
        executescript_name = getattr(instruction_row, 'executescript', None) or ''
        atomic_result = {
            'status': 'success', 'path': upstream_path, 'method': method,
            'direction': direction,
        }

        if executescript_name:
            cls = ATOMIC_SERVICE_REGISTRY.get(executescript_name)
            if not cls or not hasattr(cls, 'execute_and_save'):
                logger.warning("[ORCHESTRATION HOOK] No service class for '%s'", executescript_name)
            else:
                print(f"[ORCHESTRATION HOOK] Executing {executescript_name} for instruction id={instruction_row.id} direction={direction}")
                # Attach upstream_response to request so atomic service can access response body
                if upstream_response is not None:
                    request._upstream_response = upstream_response
                try:
                    atomic_result = cls.execute_and_save(request, instruction_row)
                except Exception as exc:
                    logger.error("[ORCHESTRATION HOOK] %s failed: %s", executescript_name, exc)
                    atomic_result = {'status': 'error', 'error': str(exc)}
        else:
            print(f"[ORCHESTRATION HOOK] Instruction id={instruction_row.id} matched (no executescript) direction={direction} — recording event")

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
        print(f"[ORCHESTRATION HOOK] _save_callback_data FAILED: {exc}")


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
        msg_text = f"Orchestration: {service_name} executed ({event_key})" if event_key else f"Orchestration: {service_name} executed"
        if isinstance(atomic_result, dict):
            if atomic_result.get('invoice_ref'):
                msg_text = f"Invoice {atomic_result['invoice_ref']} detected — orchestration triggered"
            elif atomic_result.get('event') == 'navigation':
                ch = atomic_result.get('channel') or 'Mattermost'
                ok = atomic_result.get('status') == 'sent'
                msg_text = f"Invoices page viewed — {'Mattermost notified ✓' if ok else 'Mattermost notify failed'}"

        DoseMessage.objects.create(
            user=user,
            message=msg_text,
            level=status,
        )
        logger.info("[ORCHESTRATION HOOK] DoseMessage created: %s", msg_text)
    except Exception as exc:
        logger.error("[ORCHESTRATION HOOK] Failed to create DoseMessage: %s", exc)
        print(f"[ORCHESTRATION HOOK] _create_dose_message FAILED: {exc}")
