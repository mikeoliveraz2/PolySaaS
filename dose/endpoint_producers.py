"""Endpoint-home producers: allowlist + derived pairing (no new tables).

THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
BINGO: Slack producer/consumer home — 2026-08-24

Pairing persists on Instruction: eventKey + requestpath (mailbox match).
Slack producers are allowlisted only — no full webhook enumeration.
"""
from __future__ import annotations

from dose.webhook_events import SLACK_WIREFRAME_ACTIONS

# Phase-1 Slack producers only (spec). Paths must match mailbox envelope action_path.
PRODUCER_ALLOWLIST = (
    {
        "event_key": SLACK_WIREFRAME_ACTIONS["contact"][1],
        "action_path": SLACK_WIREFRAME_ACTIONS["contact"][0],
        "display_name": "Slack new contact",
        "method": "POST",
        "direction": "REQ",
    },
    {
        "event_key": SLACK_WIREFRAME_ACTIONS["sale"][1],
        "action_path": SLACK_WIREFRAME_ACTIONS["sale"][0],
        "display_name": "Slack new sale",
        "method": "POST",
        "direction": "REQ",
    },
)

_ALLOWLIST_BY_KEY = {row["event_key"]: row for row in PRODUCER_ALLOWLIST}
_SLACK_WEBHOOK_PREFIX = "slack.webhook."


def allowlist_entry(event_key: str) -> dict | None:
    return _ALLOWLIST_BY_KEY.get((event_key or "").strip())


def _endpoint_is_slack(endpoint) -> bool:
    slug = (getattr(endpoint, "slug", "") or "").strip().lower()
    title = ""
    if hasattr(endpoint, "get_menu_title"):
        try:
            title = (endpoint.get_menu_title() or "").strip().lower()
        except Exception:
            title = (getattr(endpoint, "menu_title", "") or "").strip().lower()
    host = (getattr(endpoint, "endpoint_url", "") or "").lower()
    blob = f"{slug} {title} {host}"
    return "slack" in blob


def consumer_matches_producer(consumer: dict, entry: dict) -> bool:
    """True when this consumer Instruction is paired to the producer."""
    key = (entry.get("event_key") or "").strip().lower()
    path = (entry.get("action_path") or "").strip().lower()
    ek = (consumer.get("event_key") or "").strip().lower()
    rp = (consumer.get("request_path") or "").strip().lower()
    if key and (ek == key or key in ek):
        return True
    if path and rp == path:
        return True
    if path and rp.endswith(path):
        return True
    return False


def list_producers(endpoint, consumers: list[dict]) -> list[dict]:
    """Build Producers for the home pane: allowlist + non-Slack derived keys."""
    producers: list[dict] = []
    claimed_keys: set[str] = set()
    is_slack = _endpoint_is_slack(endpoint)

    for entry in PRODUCER_ALLOWLIST:
        paired = [c for c in consumers if consumer_matches_producer(c, entry)]
        # Show when paired (e.g. Odoo home with wireframe consumers) or on Slack
        # home so unpaired allowlist rows can be Pair'd.
        if not paired and not is_slack:
            continue
        producers.append(
            {
                "event_key": entry["event_key"],
                "action_path": entry["action_path"],
                "display_name": entry["display_name"],
                "state": "Paired" if paired else "Unpaired",
                "paired_count": len(paired),
                "paired_consumer_ids": [c["id"] for c in paired],
                "allowlisted": True,
                "pairable": True,
            }
        )
        claimed_keys.add(entry["event_key"].lower())

    # Derived producers from consumer event keys that are not Slack webhooks.
    by_key: dict[str, list[dict]] = {}
    for consumer in consumers:
        ek = (consumer.get("event_key") or "").strip()
        if not ek:
            continue
        low = ek.lower()
        if low in claimed_keys or low.startswith(_SLACK_WEBHOOK_PREFIX):
            continue
        by_key.setdefault(ek, []).append(consumer)

    for event_key, paired in sorted(by_key.items(), key=lambda item: item[0].lower()):
        title = (paired[0].get("title") or event_key).strip()
        producers.append(
            {
                "event_key": event_key,
                "action_path": paired[0].get("request_path") or "",
                "display_name": title,
                "state": "Paired",
                "paired_count": len(paired),
                "paired_consumer_ids": [c["id"] for c in paired],
                "allowlisted": False,
                "pairable": False,
            }
        )

    return producers


def annotate_consumers_fed_by(consumers: list[dict], producers: list[dict]) -> None:
    """Attach fed_by producer display names onto each consumer dict."""
    for consumer in consumers:
        names = []
        for producer in producers:
            if consumer["id"] in producer.get("paired_consumer_ids", []):
                names.append(producer["display_name"])
        consumer["fed_by"] = names


def apply_pair(tenant, event_key: str, consumer_ids: list[int], *, pair: bool) -> dict:
    """Persist pair/unpair on Instruction rows (tenant schema already selected)."""
    from dose.models import Instruction

    entry = allowlist_entry(event_key)
    if entry is None:
        raise ValueError("producer is not allowlisted for pairing")

    ids = []
    for raw in consumer_ids:
        try:
            ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    if not ids:
        raise ValueError("consumer_ids required")

    rows = list(Instruction.objects.filter(pk__in=ids))
    if not rows:
        raise ValueError("no matching consumers")

    updated = []
    action_path = entry["action_path"]
    for row in rows:
        if pair:
            row.eventKey = entry["event_key"]
            row.requestpath = action_path
            row.requestmethod = entry["method"]
            row.direction = entry["direction"]
            row.save(
                update_fields=[
                    "eventKey",
                    "requestpath",
                    "requestmethod",
                    "direction",
                ]
            )
        else:
            # Break mailbox exact path match so unpaired producers do not fire orch.
            if (row.requestpath or "").strip() == action_path:
                row.requestpath = f"{action_path}#unpaired"
            if (row.eventKey or "").strip() == entry["event_key"]:
                row.eventKey = ""
            row.save(update_fields=["eventKey", "requestpath"])
        updated.append(row.pk)

    return {
        "success": True,
        "event_key": entry["event_key"],
        "action": "pair" if pair else "unpair",
        "updated": updated,
    }
