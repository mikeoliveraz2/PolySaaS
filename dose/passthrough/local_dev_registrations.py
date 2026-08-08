# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02 — see documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md
"""
Local-dev handler registration — OBSOLETE for discovery (2026-08-02).

Passthrough identity is the tenant PassThroughEndpoint.endpoint_url host.
Handler discovery is resolve_handler_for_endpoint(DB row) via matches_endpoint().
Upstream is always endpoint.endpoint_url from that row.

Previously this module mapped localhost:PORT → handler because the URL segment
was hostname:port ("trigger"). That concept is deleted. Kept as an empty
import side-effect module so existing `import local_dev_registrations` call
sites do not break.
"""
# Owner-approved 2026-08-02: no port→handler map; DB endpoint + slug only.
_LOCAL_DEV_TRIGGER_HANDLERS = {}
