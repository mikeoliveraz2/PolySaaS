"""
Structured logging for dynamic orchestration (Instruction match → atomic service → CallBackData).

All messages use the [ORCH] prefix so they are easy to grep in runserver output.
"""
import json
import logging
import traceback

from django.db import connection

logger = logging.getLogger(__name__)


def ensure_tenant_search_path(tenant, label=''):
    """Set PostgreSQL search_path before tenant-scoped ORM writes."""
    if not tenant or not getattr(tenant, 'schema_name', None):
        logger.warning("[ORCH] ensure_tenant_search_path skipped — no tenant (%s)", label)
        return False
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{tenant.schema_name}", public')
    orch_log('search_path_set', schema=tenant.schema_name, label=label)
    return True


def orch_log(step, **fields):
    """Print + logger.info with consistent [ORCH] prefix."""
    parts = [f"[ORCH] {step}"]
    for key, val in fields.items():
        try:
            if isinstance(val, (dict, list)):
                val = json.dumps(val, default=str)[:500]
            parts.append(f"{key}={val!r}")
        except Exception:
            parts.append(f"{key}=<?>")
    msg = ' | '.join(parts)
    print(msg)
    logger.info(msg)


def orch_log_exception(step, exc, **fields):
    tb = traceback.format_exc()
    orch_log(step, error=str(exc), **fields)
    logger.error("[ORCH] %s exception: %s\n%s", step, exc, tb)
    print(f"[ORCH] {step} TRACEBACK:\n{tb}")


def log_request_trace(request, tenant, upstream_path, app_name, direction):
    user = getattr(request, 'user', None)
    orch_log(
        'trace_start',
        direction=direction,
        app=app_name,
        path=upstream_path,
        method=getattr(request, 'method', '?'),
        tenant=getattr(tenant, 'schema_name', None),
        user=getattr(user, 'username', None) if user else None,
    )


def log_instruction_catalog(instructions, upstream_path, method, direction):
    orch_log(
        'instruction_catalog',
        direction=direction,
        count=len(instructions),
        path=upstream_path,
        method=method,
    )
    for instr in instructions[:25]:
        orch_log(
            'instruction_candidate',
            id=getattr(instr, 'id', None),
            requestpath=instr.requestpath,
            match_type=getattr(instr, 'match_type', 'path'),
            requestmethod=instr.requestmethod,
            executescript=instr.executescript,
            save_callbackdata=getattr(instr, 'save_callbackdata', False),
            eventKey=getattr(instr, 'eventKey', ''),
        )


def match_failure_reason(instr, upstream_path, method):
    """Human-readable reason an instruction did not match (for debug logs)."""
    from dose.passthrough.orchestration_hook import _instruction_matches, _extract_odoo_ids

    extra = getattr(instr, 'match_extra', {}) or {}
    if extra.get('method') and extra['method'].upper() != method.upper():
        return f"match_extra.method wants {extra['method']}, got {method}"
    if extra.get('menu_id'):
        _, menu_id = _extract_odoo_ids(upstream_path)
        if not (menu_id and str(extra['menu_id']) == menu_id):
            return f"menu_id wants {extra['menu_id']}, got {menu_id!r} from path"
    if extra.get('action_id'):
        action_id, _ = _extract_odoo_ids(upstream_path)
        if not (action_id and extra['action_id'].lower() in (action_id or '').lower()):
            return f"action_id wants {extra['action_id']}, got {action_id!r}"
    req_method = getattr(instr, 'requestmethod', None) or 'GET'
    if req_method.upper() != method.upper():
        return f"requestmethod wants {req_method}, got {method}"
    if not _instruction_matches(instr, upstream_path, method):
        return f"path rule {instr.match_type!r}:{instr.requestpath!r} not in {upstream_path!r}"
    return 'matched'


def write_request_log(request, tenant, upstream_path, note):
    """Optional RequestLog row for orchestration audit (non-blocking)."""
    try:
        from dose.models import RequestLog
        if not ensure_tenant_search_path(tenant, 'request_log'):
            return
        RequestLog.objects.create(
            user=getattr(request, 'user', None) if getattr(request, 'user', None) and request.user.is_authenticated else None,
            path=upstream_path[:255],
            method=getattr(request, 'method', 'GET')[:10],
            body={'orchestration_note': note},
            tenant=tenant,
        )
        orch_log('request_log_saved', path=upstream_path, note=note)
    except Exception as exc:
        orch_log('request_log_skipped', error=str(exc))
