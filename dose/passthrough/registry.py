# dose/passthrough/registry.py
# SINGLE SOURCE OF TRUTH FOR ALL PASSTHROUGH HANDLERS
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

_HANDLER_REGISTRY = {}


def register_handler(trigger: str, handler_class):
    """Register a handler class by trigger name"""
    key = trigger.lower().strip()
    _HANDLER_REGISTRY[key] = handler_class
    logger.info(f"[OK] Handler registered: '{key}' -> {handler_class.__name__}")


def get_handler(trigger: str) -> Optional[object]:
    """Get instantiated handler for a trigger"""
    if not trigger:
        return None
    key = trigger.lower().strip()
    cls = _HANDLER_REGISTRY.get(key)
    if cls:
        try:
            return cls()
        except Exception as e:
            logger.error(f"Failed to instantiate handler '{key}': {e}")
    return None


def any_handler_exempts_csrf_for_path(path: str) -> bool:
    """Used by CSRF exemption middleware"""
    if not path or not path.startswith('/pt/'):
        return False

    try:
        parts = [p for p in path.strip('/').split('/') if p]
        if len(parts) >= 3 and parts[0] == 'pt' and parts[1] == 'admin':
            trigger = parts[2]
            handler = get_handler(trigger)
            if handler and hasattr(handler, 'exempts_csrf'):
                return bool(handler.exempts_csrf(path))
    except Exception as e:
        logger.warning(f"CSRF exemption check failed for {path}: {e}")

    return False


# URL helpers
def get_native_passthrough_prefixes() -> List[str]:
    return list(_HANDLER_REGISTRY.keys())


def native_passthrough_path_regex():
    prefixes = get_native_passthrough_prefixes()
    if not prefixes:
        return r'^/pt/admin/(?P<trigger>.*)/'
    pattern = '|'.join(p.replace('.', r'\.') for p in prefixes)
    return rf'^/pt/admin/(?P<trigger>{pattern})/.*$'


def get_handler_for_endpoint(trigger: str = None):
    return get_handler(trigger)


def pt_admin_core_delegated_to_urlconf(request, trigger):
    handler = get_handler(trigger)
    if handler and hasattr(handler, 'handle_request'):
        return handler.handle_request(request, None)
    return None


__all__ = [
    'register_handler',
    'get_handler',
    'any_handler_exempts_csrf_for_path',
    'get_native_passthrough_prefixes',
    'native_passthrough_path_regex',
    'get_handler_for_endpoint',
    'pt_admin_core_delegated_to_urlconf',
]