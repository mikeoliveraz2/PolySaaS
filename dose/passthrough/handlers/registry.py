import logging
import re
from importlib import import_module

from dose.passthrough.utils import normalize_trigger_segment

logger = logging.getLogger(__name__)


_BUNDLED_HANDLER_SPECS = (
    {
        "key": "gmail",
        "module": "dose.passthrough.handlers.gmail_handler",
        "class_name": "GmailPassthroughHandler",
        "matches": lambda trigger_path: trigger_path.lower() == "gmail",
    },
    {
        "key": "monitor_logger",
        "module": "dose.passthrough.handlers.monitor_logger_handler",
        "class_name": "MonitorLoggerPassthroughHandler",
        "matches": lambda trigger_path: normalize_trigger_segment(trigger_path) == "monitor_logger",
    },
    {
        "key": "aiaspeers",
        "module": "dose.passthrough.handlers.aiaspeers_handler",
        "class_name": "AiaspeersPassthroughHandler",
        "matches": lambda trigger_path: trigger_path.lower() == "aiaspeers",
    },
    {
        "key": "nextcloud",
        "module": "dose.passthrough.handlers.nextcloud_handler",
        "class_name": "NextcloudPassthroughHandler",
        "matches": lambda trigger_path: trigger_path == "nextcloud",
    },
    {
        "key": "polysysmon",
        "module": "dose.passthrough.handlers.polysysmon_handler",
        "class_name": "PolysysmonPassthroughHandler",
        "matches": lambda trigger_path: trigger_path == "polysysmon",
    },
    {
        "key": "wordpress",
        "module": "dose.passthrough.handlers.wordpress_handler",
        "class_name": "WordPressPassthroughHandler",
        "matches": lambda trigger_path: trigger_path.lower() == "wordpress",
    },
    {
        "key": "odoo",
        "module": "dose.passthrough.handlers.odoo_handler",
        "class_name": "OdooPassthroughHandler",
        "matches": lambda trigger_path: normalize_trigger_segment(trigger_path) == "odoo",
    },
    {
        "key": "liferay",
        "module": "dose.passthrough.handlers.liferay_handler",
        "class_name": "LiferayPassthroughHandler",
        "matches": lambda trigger_path: trigger_path.lower() == "liferay",
    },
    {
        "key": "mattermost",
        "module": "dose.passthrough.handlers.mattermost_handler",
        "class_name": "MattermostPassthroughHandler",
        "matches": lambda trigger_path: trigger_path.lower() == "mattermost",
    },
    {
        "key": "dolibarr",
        "module": "dose.passthrough.handlers.dolibarr_handler",
        "class_name": "DolibarrPassthroughHandler",
        "matches": lambda trigger_path: trigger_path.lower() == "dolibarr",
    },
)


def _instantiate_bundled_handler(spec):
    module = import_module(spec["module"])
    handler_cls = getattr(module, spec["class_name"])
    return handler_cls()


def iter_bundled_handler_specs():
    """Yield bundled shared handler specs in stable order."""
    yield from _BUNDLED_HANDLER_SPECS


def iter_registered_handler_instances():
    """Yield one instance of each shared bundled passthrough handler."""
    for spec in iter_bundled_handler_specs():
        yield _instantiate_bundled_handler(spec)


def get_native_passthrough_prefixes():
    prefixes = []
    seen = set()
    for handler in iter_registered_handler_instances():
        fn = getattr(handler, "native_passthrough_prefixes", None)
        if not callable(fn):
            continue
        for prefix in fn() or ():
            if not prefix or prefix in seen:
                continue
            seen.add(prefix)
            prefixes.append(prefix)
    return tuple(sorted(prefixes, key=lambda value: (-len(value), value)))


def native_passthrough_path_regex():
    prefixes = [p.strip("/") for p in get_native_passthrough_prefixes() if p.strip("/")]
    if not prefixes:
        return None
    parts = [f"{re.escape(prefix)}(?:/.*)?" for prefix in prefixes]
    return r'^(?P<path>(?:' + "|".join(parts) + r'))$'


def any_handler_exempts_csrf_for_path(path_info: str) -> bool:
    for handler in iter_registered_handler_instances():
        fn = getattr(handler, "should_exempt_csrf_for_path", None)
        if not callable(fn):
            continue
        try:
            if fn(path_info):
                return True
        except Exception:
            logger.exception("handler csrf path check failed for %s", handler.__class__.__name__)
    return False


def pt_admin_core_delegated_to_urlconf(request, path_info: str) -> bool:
    """
    If True, run_pt_admin_passthrough_core returns None so Django URLconf handles the path.

    Endpoint-specific delegation (e.g. Mattermost /static/ proxy) must be implemented on
    the handler via should_delegate_pt_admin_core — never hardcoded in middleware.
    """
    for handler in iter_registered_handler_instances():
        fn = getattr(handler, "should_delegate_pt_admin_core", None)
        if not callable(fn):
            continue
        try:
            if fn(request, path_info):
                return True
        except Exception:
            logger.exception(
                "should_delegate_pt_admin_core failed for %s", handler.__class__.__name__
            )
    return False


def get_handler_for_endpoint(endpoint, request=None):
    """
    Returns the correct handler instance based on trigger_path
    """
    trigger_path = endpoint.trigger_path or ""
    for spec in iter_bundled_handler_specs():
        try:
            if spec["matches"](trigger_path):
                return _instantiate_bundled_handler(spec)
        except Exception:
            logger.exception("bundled handler match failed for %s", spec["key"])
            return None

    logger.info(f"No specific handler found for {trigger_path}")
    return None