"""
Shared helpers for Phase 1 (and future) atomic services.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit PENDING
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def filter_parameters(parameters, key):
    """Return Parameter row(s) or dict matching matchingKey == key."""
    if isinstance(parameters, dict):
        return parameters if parameters.get('MatchingKey') == key else None
    if isinstance(parameters, list):
        return [
            p for p in parameters
            if (isinstance(p, dict) and p.get('MatchingKey') == key)
            or (hasattr(p, 'matchingKey') and getattr(p, 'matchingKey', None) == key)
        ]
    return None


def instruction_config(instruction_row):
    """Merged config from Instruction.parameters_json (dict)."""
    raw = getattr(instruction_row, 'parameters_json', None) if instruction_row else None
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def tenant_from_request(request):
    return getattr(request, 'tenant', None)


def request_snapshot(request):
    """Lightweight request metadata for payloads."""
    user = getattr(request, 'user', None)
    tenant = tenant_from_request(request)
    body = getattr(request, 'body', b'') or b''
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='replace')[:8000]
    return {
        'path': getattr(request, 'path', ''),
        'method': getattr(request, 'method', 'GET'),
        'user': str(user) if user and getattr(user, 'is_authenticated', False) else 'anonymous',
        'user_email': getattr(user, 'email', '') if user else '',
        'tenant': str(tenant) if tenant else '',
        'body_preview': body[:2000] if body else '',
    }


def maybe_save_callback(request, instruction_row, payload, description=None):
    """Persist CallBackData when instruction.save_callbackdata is True."""
    if not instruction_row or not getattr(instruction_row, 'save_callbackdata', False):
        return None
    try:
        from dose.models import CallBackData
        tenant = tenant_from_request(request)
        cb = CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=getattr(instruction_row, 'eventKey', None) or '',
            description=description or getattr(instruction_row, 'description', None) or 'Atomic service result',
            parameters_json=payload,
            callbackdata=payload,
        )
        return cb
    except Exception as exc:
        logger.error('[AtomicService] CallBackData save failed: %s', exc)
        return None


def service_result(service_name, status='success', **extra):
    """Standard result dict returned by execute_and_save."""
    data = {
        'service_name': service_name,
        'status': status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    data.update(extra)
    return data
