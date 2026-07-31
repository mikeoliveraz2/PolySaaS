"""
Local-dev-only explicit handler registrations.

Per documentation/LOCAL_STANDALONE_STACK.md, each bundled app runs on a fixed,
well-known port in the local docker-compose stack (Odoo=8086, Nextcloud=8888,
Mattermost=8065, Dolibarr=8083). Locally, the endpoint's own URL carries no
other app-identifying string (unlike production, where distinct onrender.com
subdomains exist for fuzzy hostname matching) -- the port is the only local
identity signal.

Rather than teaching handler.matches_endpoint() a second, locally-scoped
guessing heuristic, this uses the explicit registry entry point that already
exists in dose.passthrough.registry (register_handler / get_handler), which
resolve_handler_for_pt_admin_trigger() already checks first, before any
fuzzy matching. This is a direct trigger -> handler mapping, decided once
here -- not a runtime pattern match against the URL.

Owner-approved 2026-07-31: local dev only. Production endpoints continue to
resolve via each handler's existing matches_endpoint() (already correct
there, since e.g. polysaas-odoo2.onrender.com does contain "odoo").
"""
from dose.passthrough.registry import register_handler
from dose.passthrough.handlers.odoo_handler import OdooPassthroughHandler
from dose.passthrough.handlers.nextcloud_handler import NextcloudPassthroughHandler

_LOCAL_DEV_TRIGGER_HANDLERS = {
    "localhost:8086": OdooPassthroughHandler,
    "localhost:8888": NextcloudPassthroughHandler,
}

for _trigger, _handler_cls in _LOCAL_DEV_TRIGGER_HANDLERS.items():
    register_handler(_trigger, _handler_cls)
