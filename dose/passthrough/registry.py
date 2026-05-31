# dose/passthrough/registry.py
# Generic handler discovery — no endpoint-specific names in this module.
import importlib
import inspect
import logging
import pkgutil
from typing import List, Optional, Type
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_HANDLER_REGISTRY = {}
_HANDLER_CLASSES: Optional[List[Type]] = None


def register_handler(trigger: str, handler_class):
    """Legacy explicit registration by trigger slug."""
    key = trigger.lower().strip()
    _HANDLER_REGISTRY[key] = handler_class
    logger.info("[OK] Handler registered: '%s' -> %s", key, handler_class.__name__)


def _discover_handler_classes() -> List[Type]:
    """Load all *PassthroughHandler classes that implement matches_endpoint."""
    global _HANDLER_CLASSES
    if _HANDLER_CLASSES is not None:
        return _HANDLER_CLASSES

    classes: List[Type] = []
    import dose.passthrough.handlers as handlers_pkg

    for modinfo in pkgutil.iter_modules(handlers_pkg.__path__):
        if not modinfo.name.endswith("_handler"):
            continue
        try:
            mod = importlib.import_module(f"dose.passthrough.handlers.{modinfo.name}")
        except Exception as exc:
            logger.warning("Could not import handler module %s: %s", modinfo.name, exc)
            continue
        for _name, obj in inspect.getmembers(mod, inspect.isclass):
            if not _name.endswith("PassthroughHandler"):
                continue
            if not callable(getattr(obj, "matches_endpoint", None)):
                continue
            if obj not in classes:
                classes.append(obj)
                logger.debug("Discovered passthrough handler: %s", obj.__name__)

    _HANDLER_CLASSES = classes
    return classes


def endpoint_match_blob(endpoint) -> str:
    url = getattr(endpoint, "endpoint_url", "") or ""
    host = urlparse(url).netloc.lower()
    slug = str(getattr(endpoint, "slug", "") or "").lower()
    trigger = str(getattr(endpoint, "trigger_path", "") or "").lower()
    return f"{host} {slug} {trigger}".strip()


def resolve_handler_for_endpoint(endpoint) -> Optional[object]:
    """Return handler instance whose matches_endpoint() claims this endpoint."""
    for cls in _discover_handler_classes():
        try:
            if cls.matches_endpoint(endpoint):
                return cls()
        except Exception:
            logger.exception("matches_endpoint failed for %s", cls.__name__)
    return None


def resolve_handler_for_pt_admin_trigger(trigger: str) -> Optional[object]:
    """Resolve handler from /pt/admin/<trigger>/ URL segment (hostname or slug)."""

    class _SimpleEndpoint:
        def __init__(self, seg: str):
            seg = (seg or "").strip("/")
            self.trigger_path = seg
            self.slug = seg
            self.endpoint_url = (
                seg if seg.startswith(("http://", "https://")) else f"https://{seg}"
            )

    legacy = get_handler(trigger)
    if legacy is not None:
        return legacy
    return resolve_handler_for_endpoint(_SimpleEndpoint(trigger))


def get_handler(trigger: str) -> Optional[object]:
    """Legacy registry lookup by trigger slug only."""
    if not trigger:
        return None
    key = trigger.lower().strip()
    cls = _HANDLER_REGISTRY.get(key)
    if cls:
        try:
            return cls()
        except Exception as e:
            logger.error("Failed to instantiate handler '%s': %s", key, e)
    return None


def any_handler_exempts_csrf_for_path(path: str) -> bool:
    """True if any handler exempts this path from Django CSRF."""
    if not path:
        return False

    for cls in _discover_handler_classes():
        try:
            handler = cls()
            if handler.should_exempt_csrf_for_path(path):
                return True
        except Exception as e:
            logger.warning("CSRF exemption check failed for %s on %s: %s", cls.__name__, path, e)

    if path.startswith("/pt/"):
        try:
            parts = [p for p in path.strip("/").split("/") if p]
            if len(parts) >= 3 and parts[0] == "pt" and parts[1] == "admin":
                handler = resolve_handler_for_pt_admin_trigger(parts[2])
                if handler and hasattr(handler, "exempts_csrf"):
                    return bool(handler.exempts_csrf(path))
        except Exception as e:
            logger.warning("CSRF exemption check failed for %s: %s", path, e)

    return False


def get_native_passthrough_prefixes() -> List[str]:
    return list(_HANDLER_REGISTRY.keys())


def native_passthrough_path_regex():
    prefixes = get_native_passthrough_prefixes()
    if not prefixes:
        return r"^/pt/admin/(?P<trigger>.*)/"
    pattern = "|".join(p.replace(".", r"\.") for p in prefixes)
    return rf"^/pt/admin/(?P<trigger>{pattern})/.*$"


def get_handler_for_endpoint(trigger: str = None, endpoint=None, request=None):
    if endpoint is not None:
        resolved = resolve_handler_for_endpoint(endpoint)
        if resolved is not None:
            return resolved
    if trigger:
        return resolve_handler_for_pt_admin_trigger(trigger)
    return None


def pt_admin_core_delegated_to_urlconf(request, path_info: str) -> bool:
    """
    True when a handler wants URLconf to serve the request (e.g. static proxy route).
    Aggregates should_delegate_pt_admin_core across all discovered handlers.
    """
    path = path_info or getattr(request, "path_info", "") or ""
    for cls in _discover_handler_classes():
        try:
            handler = cls()
            fn = getattr(handler, "should_delegate_pt_admin_core", None)
            if callable(fn) and fn(request, path):
                return True
        except Exception:
            logger.exception("should_delegate_pt_admin_core failed for %s", cls.__name__)
    return False


def apply_handler_incoming_path_referer_fallbacks(request) -> None:
    """Ask each handler's optional referer fallback hook (endpoint-specific logic)."""
    for cls in _discover_handler_classes():
        fn = getattr(cls, "try_rewrite_incoming_path_referer_fallback", None)
        if not callable(fn):
            continue
        try:
            if fn(request):
                return
        except Exception:
            logger.exception(
                "try_rewrite_incoming_path_referer_fallback failed for %s", cls.__name__
            )


__all__ = [
    "register_handler",
    "get_handler",
    "any_handler_exempts_csrf_for_path",
    "get_native_passthrough_prefixes",
    "native_passthrough_path_regex",
    "get_handler_for_endpoint",
    "resolve_handler_for_endpoint",
    "resolve_handler_for_pt_admin_trigger",
    "pt_admin_core_delegated_to_urlconf",
    "apply_handler_incoming_path_referer_fallbacks",
]
