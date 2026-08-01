"""
MQ topic naming — local RabbitMQ (and later Pub/Sub) convention.

Topic = {REQ|RES}.{action_path}.{username}

Rules (keep consistent across every app):
  - Direction prepended: REQ (request) or RES (response), uppercase
  - Delimiter: '.' (AMQP routing-key style)
  - Action path: strip leading '/', replace '/' and ':' with '.', lowercase,
    drop characters that are not alphanumeric / '.' / '-' / '_'
  - Username: PolySaaS login, lowercase; fall back to 'anonymous'
  - Example: RES + /odoo/contacts + pso13 → RES.odoo.contacts.pso13
  - Example: REQ + /odoo/contacts + pso13 → REQ.odoo.contacts.pso13
"""
from __future__ import annotations

import re


def sanitize_direction(direction: str | None) -> str:
    """Normalize Instruction direction to REQ or RES."""
    raw = (direction or "").strip().upper()
    if raw in ("RES", "RESPONSE"):
        return "RES"
    if raw in ("REQ", "REQUEST"):
        return "REQ"
    # Default request-side when unspecified (live POST extractors, sniffer)
    return "REQ"


def sanitize_action_path(action_path: str) -> str:
    """Turn an orch-bar action path into a topic segment."""
    raw = (action_path or "").strip()
    if not raw:
        return "unknown"
    # Accept both UI form (/odoo/contacts) and orch-gate form (odoo:contacts)
    raw = raw.lstrip("/")
    raw = raw.replace("/", ".").replace(":", ".")
    raw = re.sub(r"[^a-zA-Z0-9.\-_]", "", raw)
    raw = re.sub(r"\.+", ".", raw).strip(".")
    return (raw or "unknown").lower()


def sanitize_username(username: str | None) -> str:
    """PolySaaS login → topic suffix."""
    name = (username or "").strip().lower()
    name = re.sub(r"[^a-z0-9.\-_]", "", name)
    return name or "anonymous"


def build_mq_topic(
    action_path: str,
    username: str | None,
    direction: str | None = "REQ",
) -> str:
    """
    Build routing key / topic: {REQ|RES}.{action_path}.{username}, max 255 chars.
    """
    dir_prefix = sanitize_direction(direction)
    path = sanitize_action_path(action_path)
    user = sanitize_username(username)
    return f"{dir_prefix}.{path}.{user}"[:255]


def topic_from_request(
    request,
    action_path: str | None = None,
    direction: str | None = None,
) -> str:
    """
    Convenience for request-time publish.

    Prefer explicit action_path, then request.path.
    Direction from argument, else instruction-like attrs if present, else REQ.
    Username from authenticated user when present.
    """
    path = action_path
    if not path:
        path = getattr(request, "path", "") or ""
    user = getattr(request, "user", None)
    username = None
    if user is not None and getattr(user, "is_authenticated", False):
        username = getattr(user, "username", None) or getattr(user, "get_username", lambda: None)()
    if direction is None:
        direction = getattr(request, "_orch_direction", None)
    return build_mq_topic(path, username, direction=direction)
