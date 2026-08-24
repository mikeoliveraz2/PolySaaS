"""Shared orchestration-bar copy for instruction-match messaging."""


def describe_instruction_match(result: dict | None) -> str:
    """Return the green-bar match line from a mailbox/orchestration result."""
    payload = result if isinstance(result, dict) else {}
    first = {}
    rows = payload.get("results") or []
    if rows and isinstance(rows[0], dict):
        first = rows[0]
    method = (first.get("method") or payload.get("method") or "POST").upper()
    direction = (first.get("direction") or payload.get("direction") or "REQ").upper()
    path = (
        first.get("path")
        or payload.get("action_path")
        or payload.get("path")
        or ""
    )
    consumer = (first.get("executescript") or payload.get("executescript") or "").strip()
    matched = payload.get("matched")
    if payload.get("status") == "no_instruction" or matched == 0:
        return f"No instruction match for {method} {path or 'this action'}"
    if consumer:
        return f"{method} {direction} {path} → {consumer}"
    event_key = (first.get("eventKey") or payload.get("event_key") or "").strip()
    if event_key:
        return f"{method} {direction} {path} · {event_key}"
    if path:
        return f"{method} {direction} {path}"
    return ""
