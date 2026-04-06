# dose/polysniffer/handlers/registry.py
# Map service name → PolySniffer embed handler class (add new services here only).

from .mattermost_handler import MattermostPassthroughHandler

HANDLER_REGISTRY = {
    "mattermost": MattermostPassthroughHandler,
    # "odoo": OdooPassthroughHandler,
    # "nextcloud": NextcloudPassthroughHandler,
}


def get_handler(service_name):
    """Return the handler class for a service name, or None if unsupported."""
    if not service_name:
        return None
    return HANDLER_REGISTRY.get(service_name.strip().lower())
