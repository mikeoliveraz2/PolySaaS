# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from .hubspot import HubspotEndpointActionAdapter
from .odoo import OdooEndpointActionAdapter
from .slack import SlackEndpointActionAdapter


_ADAPTERS = (
    SlackEndpointActionAdapter,
    OdooEndpointActionAdapter,
    HubspotEndpointActionAdapter,
)


def adapter_for_endpoint(endpoint):
    """Resolve provider behavior without putting app names in shared UI code."""
    for adapter_class in _ADAPTERS:
        if adapter_class.matches_endpoint(endpoint):
            return adapter_class()
    return None
