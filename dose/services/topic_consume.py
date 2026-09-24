# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Captured Topics Consume to History — 2026-09-21
# Owner-approved 2026-09-21: FAMILY_CONTACTS + ContactHistory consume.
# Owner-approved 2026-09-22: one shared Contacts label (not per-app).
# Owner-approved 2026-09-22: Captured Topics lists only typed families — hide Odoo action-noise.
"""
Topic consume — drain typed temporary mailbox topics into history tables.

Admin Topic browser lists topics; Consume writes envelopes into the matching
history table, then deletes those mailbox rows so they leave the topic queue.
"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)

FAMILY_INVENTORY = "inventory_product"
FAMILY_SNMP = "snmp_telemetry"
FAMILY_MAINTENANCE = "maintenance_equipment"
FAMILY_CONTACTS = "contacts"
FAMILY_VENDORS = "vendors"
FAMILY_UNKNOWN = "unknown"

FAMILY_LABELS = {
    FAMILY_INVENTORY: "Inventory products",
    FAMILY_SNMP: "SNMP telemetry",
    FAMILY_MAINTENANCE: "Maintenance equipment",
    FAMILY_CONTACTS: "Contacts",
    FAMILY_VENDORS: "Vendors",
    FAMILY_UNKNOWN: "Other captured traffic",
}

FAMILY_DESCRIPTIONS = {
    FAMILY_INVENTORY: "Odoo inventory / product list captures in this topic queue.",
    FAMILY_SNMP: "SNMP device telemetry captures in this topic queue.",
    FAMILY_MAINTENANCE: "Maintenance equipment captures in this topic queue.",
    FAMILY_CONTACTS: "Contact list captures from any subscribed app (shared topic).",
    FAMILY_VENDORS: "Vendor company captures in this topic queue.",
    FAMILY_UNKNOWN: "Captured traffic with no Consume handler yet.",
}


def topic_display_name(topic: str, family: str) -> str:
    """Short human name for the Captured Topics list."""
    t = (topic or "").strip().lower()
    if family == FAMILY_CONTACTS:
        # One queue for every app — do not prefix with Odoo/Mattermost/etc.
        return "Contacts"
    if family == FAMILY_VENDORS:
        return "Vendors"
    if family == FAMILY_INVENTORY and "product.product" in t:
        return "Inventory variants"
    if family == FAMILY_INVENTORY:
        return "Inventory products"
    if family == FAMILY_SNMP:
        return "SNMP telemetry"
    if family == FAMILY_MAINTENANCE:
        return "Maintenance equipment"
    if "action-" in t:
        return "Odoo action capture"
    return FAMILY_LABELS.get(family, "Captured topic")


def topic_description(topic: str, family: str) -> str:
    """Tooltip: short description plus full topic key."""
    base = FAMILY_DESCRIPTIONS.get(family, "Captured topic.")
    return f"{base} Topic key: {topic}"


def classify_topic(topic: str, *, source: str = "", action_path: str = "") -> str:
    t = (topic or "").lower()
    s = (source or "").lower()
    ap = (action_path or "").lower()
    blob = f"{t} {s} {ap}"
    if "snmp" in blob:
        return FAMILY_SNMP
    if "maintenance" in blob:
        return FAMILY_MAINTENANCE
    if any(
        x in blob
        for x in (
            ".vendors.",
            "vendor.created",
            "/events/polysaas/vendor",
            "vendor_created",
        )
    ):
        return FAMILY_VENDORS
    # Contacts before inventory: ".contacts." must not match product. paths.
    if any(
        x in blob
        for x in (
            ".contacts.",
            "capture_contacts",
            "contact_list",
            "/contacts",
        )
    ):
        return FAMILY_CONTACTS
    if any(
        x in blob
        for x in (
            "product.template",
            "product.product",
            "stock.quant",
            "odoo_inventory",
            "inventory",
            "product.",
        )
    ):
        return FAMILY_INVENTORY
    return FAMILY_UNKNOWN


def list_topic_history(topic: str, *, limit: int = 100) -> dict:
    """
    History rows for one topic (after Consume). Returns family + column headers + rows.
    """
    from dose.models.topic_history import (
        ContactHistory,
        InventoryProductHistory,
        MaintenanceEquipmentHistory,
        SnmpTelemetryHistory,
        VendorHistory,
    )

    topic = (topic or "").strip()
    family = classify_topic(topic)
    limit = max(1, int(limit))

    if family == FAMILY_INVENTORY:
        qs = InventoryProductHistory.objects.filter(topic=topic).order_by("-consumed_at")[
            :limit
        ]
        columns = ["name", "default_code", "list_price", "odoo_id", "consumed_at"]
        rows = [
            [
                r.name,
                r.default_code,
                str(r.list_price) if r.list_price is not None else "",
                r.odoo_id,
                r.consumed_at,
            ]
            for r in qs
        ]
    elif family == FAMILY_SNMP:
        qs = SnmpTelemetryHistory.objects.filter(topic=topic).order_by("-consumed_at")[
            :limit
        ]
        columns = [
            "device_name",
            "device_mac",
            "status",
            "temperature_c",
            "cpu_utilization",
            "consumed_at",
        ]
        rows = [
            [
                r.device_name,
                r.device_mac,
                r.status,
                r.temperature_c,
                r.cpu_utilization,
                r.consumed_at,
            ]
            for r in qs
        ]
    elif family == FAMILY_MAINTENANCE:
        qs = MaintenanceEquipmentHistory.objects.filter(topic=topic).order_by(
            "-consumed_at"
        )[:limit]
        columns = [
            "equipment_name",
            "serial_no",
            "category",
            "anomaly",
            "request_name",
            "consumed_at",
        ]
        rows = [
            [
                r.equipment_name,
                r.serial_no,
                r.category,
                r.anomaly,
                r.request_name,
                r.consumed_at,
            ]
            for r in qs
        ]
    elif family == FAMILY_VENDORS:
        qs = VendorHistory.objects.filter(topic__icontains=".vendors.").order_by(
            "-consumed_at"
        )[:limit]
        columns = [
            "name",
            "email",
            "region",
            "odoo_vendor_id",
            "odoo_contact_id",
            "consumed_at",
        ]
        rows = [
            [
                r.name,
                r.email,
                r.region,
                r.odoo_vendor_id,
                r.odoo_contact_id,
                r.consumed_at,
            ]
            for r in qs
        ]
    elif family == FAMILY_CONTACTS:
        # Shared Contacts history — include legacy per-app topic keys.
        qs = ContactHistory.objects.filter(topic__icontains=".contacts.").order_by(
            "-consumed_at"
        )[:limit]
        columns = [
            "source_app",
            "name",
            "email",
            "phone",
            "company",
            "username",
            "consumed_at",
        ]
        rows = [
            [
                r.source_app,
                r.name,
                r.email,
                r.phone,
                r.company,
                r.username,
                r.consumed_at,
            ]
            for r in qs
        ]
    else:
        return {
            "topic": topic,
            "family": family,
            "family_label": FAMILY_LABELS.get(family, family),
            "columns": [],
            "rows": [],
            "count": 0,
            "supported": False,
        }

    return {
        "topic": topic,
        "family": family,
        "family_label": FAMILY_LABELS.get(family, family),
        "columns": columns,
        "rows": rows,
        "count": len(rows),
        "supported": True,
    }


def _contact_topic_filter():
    """Q for every contacts-family mailbox topic (shared + legacy per-app keys)."""
    from django.db.models import Q

    return (
        Q(topic__icontains=".contacts.")
        | Q(topic__icontains="capture_contacts")
        | Q(action_path__icontains="capture_contacts")
        | Q(action_path__icontains="/contacts")
    )


def list_topics() -> list[dict]:
    """Aggregate mailbox rows by topic (current search_path / tenant schema).

    Contact captures share one queue — collapse shared + legacy per-app keys
    into a single Contacts row pointing at RES.contacts.system.

    Only typed families appear here (Contacts / Vendors / Inventory / SNMP / Maintenance).
    Raw PolySniffer ``action-`` captures have no Consume handler — omit them so
    they do not look like a second Contacts / Odoo row.
    """
    from dose.models import WebhookMailbox

    rows = (
        WebhookMailbox.objects.exclude(topic="")
        .values("topic")
        .annotate(total=Count("id"))
        .order_by("topic")
    )
    out = []
    contacts_seen = False
    vendors_seen = False
    for row in rows:
        topic = row["topic"] or ""
        family = classify_topic(topic)
        if family == FAMILY_UNKNOWN:
            continue
        if family == FAMILY_CONTACTS:
            if contacts_seen:
                continue
            contacts_seen = True
            topic = "RES.contacts.system"
            family = FAMILY_CONTACTS
        if family == FAMILY_VENDORS:
            if vendors_seen:
                continue
            vendors_seen = True
            topic = "RES.vendors.system"
            family = FAMILY_VENDORS
        out.append(
            {
                "topic": topic,
                "family": family,
                "name": topic_display_name(topic, family),
                "description": topic_description(topic, family),
                "family_label": FAMILY_LABELS.get(family, family),
                "has_history": True,
            }
        )
    return out


def _is_shared_contacts_topic(topic: str) -> bool:
    t = (topic or "").strip().lower()
    return t.startswith("res.contacts.") or classify_topic(topic) == FAMILY_CONTACTS


def _vendor_topic_filter():
    from django.db.models import Q

    return (
        Q(topic__icontains=".vendors.")
        | Q(action_path__icontains="/events/polysaas/vendor")
        | Q(action_path__icontains="vendor/created")
    )


def _is_shared_vendors_topic(topic: str) -> bool:
    t = (topic or "").strip().lower()
    return t.startswith("res.vendors.") or classify_topic(topic) == FAMILY_VENDORS


def list_topic_envelopes(topic: str, *, limit: int = 100) -> list[dict]:
    """Peek envelopes still on the topic queue (current tenant schema)."""
    from dose.models import WebhookMailbox

    topic = (topic or "").strip()
    # Over-fetch slightly so we can drop any pre-delete drained leftovers.
    qs = WebhookMailbox.objects.all()
    if _is_shared_contacts_topic(topic):
        qs = qs.filter(_contact_topic_filter())
    elif _is_shared_vendors_topic(topic):
        qs = qs.filter(_vendor_topic_filter())
    else:
        qs = qs.filter(topic=topic)
    rows = list(qs.order_by("-created_at")[: max(1, int(limit)) * 2])
    out = []
    for row in rows:
        # Legacy: older Consume left rows as processed with result.consume=True.
        if isinstance(row.result, dict) and row.result.get("consume"):
            continue
        env = row.envelope if isinstance(row.envelope, dict) else {}
        payload = env.get("payload")
        if payload is None:
            payload = row.result
        record_count = None
        if isinstance(payload, dict):
            record_count = payload.get("record_count")
            if record_count is None and isinstance(payload.get("records"), list):
                record_count = len(payload["records"])
        out.append(
            {
                "id": row.id,
                "status": row.status,
                "source": row.source,
                "action_path": row.action_path,
                "event_id": row.event_id,
                "created_at": row.created_at,
                "expires_at": row.expires_at,
                "record_count": record_count,
            }
        )
        if len(out) >= max(1, int(limit)):
            break
    return out


def requeue_topic(topic: str) -> dict:
    """Move processed/failed rows on a topic back to pending for Consume."""
    from dose.models import WebhookMailbox

    topic = (topic or "").strip()
    if not topic:
        return {"ok": False, "error": "missing_topic", "updated": 0}
    qs = WebhookMailbox.objects.filter(
        status__in=["processed", "failed", "claimed"],
    )
    if _is_shared_contacts_topic(topic):
        qs = qs.filter(_contact_topic_filter())
    elif _is_shared_vendors_topic(topic):
        qs = qs.filter(_vendor_topic_filter())
    else:
        qs = qs.filter(topic=topic)
    updated = qs.update(
        status="pending",
        processed_at=None,
        claimed_at=None,
        error="",
    )
    return {"ok": True, "topic": topic, "updated": updated}


def consume_envelope(mailbox_id: int, *, also_feed_odoo: bool = True, tenant=None) -> dict:
    """
    Consume one mailbox envelope into history (any status with a known family).

    Used by the per-row "Consume to History" button on Browse Topic.
    """
    from dose.models import WebhookMailbox

    try:
        entry = WebhookMailbox.objects.get(pk=int(mailbox_id))
    except (WebhookMailbox.DoesNotExist, TypeError, ValueError):
        return {"ok": False, "error": "mailbox_not_found", "written": 0}

    topic = (entry.topic or "").strip()
    family = classify_topic(
        topic,
        source=entry.source or "",
        action_path=entry.action_path or "",
    )
    if family == FAMILY_UNKNOWN:
        return {
            "ok": False,
            "error": "no_handler_for_topic",
            "topic": topic,
            "family": family,
            "written": 0,
        }

    mailbox_pk = entry.id
    try:
        entry.mark_claimed()
        n = _consume_one(entry, family)
        # Drain: history keeps the data; remove envelope from the topic queue.
        entry.delete()
    except Exception as exc:
        logger.exception("[TopicConsume] mailbox=%s failed", mailbox_pk)
        try:
            entry.mark_failed(str(exc))
        except Exception:
            pass
        return {"ok": False, "error": str(exc), "topic": topic, "written": 0}

    odoo_feed = None
    if also_feed_odoo and family == FAMILY_SNMP and n and tenant is not None:
        try:
            odoo_feed = _feed_odoo_from_snmp_history(topic, tenant=tenant)
        except Exception as exc:
            odoo_feed = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "topic": topic,
        "family": family,
        "family_label": FAMILY_LABELS.get(family, family),
        "mailbox_id": mailbox_pk,
        "written": n,
        "odoo_feed": odoo_feed,
    }


def consume_topic(
    topic: str,
    *,
    limit: int = 100,
    also_feed_odoo: bool = True,
    tenant=None,
) -> dict:
    """
    Drain pending mailbox rows for ``topic`` into the typed history table.

    Returns counts: claimed, written, failed, family, errors[].
    """
    from dose.models import WebhookMailbox

    topic = (topic or "").strip()
    if not topic:
        return {"ok": False, "error": "missing_topic", "written": 0}

    pending_qs = WebhookMailbox.objects.filter(
        status="pending",
        expires_at__gt=timezone.now(),
    )
    if _is_shared_contacts_topic(topic):
        pending_qs = pending_qs.filter(_contact_topic_filter())
        topic = "RES.contacts.system"
    elif _is_shared_vendors_topic(topic):
        pending_qs = pending_qs.filter(_vendor_topic_filter())
        topic = "RES.vendors.system"
    else:
        pending_qs = pending_qs.filter(topic=topic)
    pending = list(pending_qs.order_by("created_at")[: max(1, int(limit))])
    if not pending:
        return {
            "ok": True,
            "topic": topic,
            "family": classify_topic(topic),
            "claimed": 0,
            "written": 0,
            "failed": 0,
            "message": "no pending rows",
        }

    sample = pending[0]
    family = classify_topic(
        topic,
        source=sample.source or "",
        action_path=sample.action_path or "",
    )
    if family == FAMILY_UNKNOWN:
        return {
            "ok": False,
            "topic": topic,
            "family": family,
            "error": "no_handler_for_topic",
            "claimed": 0,
            "written": 0,
        }

    written = 0
    failed = 0
    errors: list[str] = []
    odoo_feed = None

    for entry in pending:
        mailbox_pk = entry.id
        try:
            entry.mark_claimed()
            n = _consume_one(entry, family)
            written += n
            # Drain: history keeps the data; remove envelope from the topic queue.
            entry.delete()
        except Exception as exc:
            failed += 1
            errors.append(f"mailbox#{mailbox_pk}: {exc}")
            logger.exception("[TopicConsume] mailbox=%s failed", mailbox_pk)
            try:
                entry.mark_failed(str(exc))
            except Exception:
                pass

    if also_feed_odoo and family == FAMILY_SNMP and written and tenant is not None:
        try:
            odoo_feed = _feed_odoo_from_snmp_history(topic, tenant=tenant)
        except Exception as exc:
            logger.warning("[TopicConsume] Odoo feed after SNMP consume: %s", exc)
            odoo_feed = {"ok": False, "error": str(exc)}

    return {
        "ok": failed == 0,
        "topic": topic,
        "family": family,
        "family_label": FAMILY_LABELS.get(family, family),
        "claimed": len(pending),
        "written": written,
        "failed": failed,
        "errors": errors[:20],
        "odoo_feed": odoo_feed,
    }


def _consume_one(entry, family: str) -> int:
    if family == FAMILY_INVENTORY:
        return _write_inventory(entry)
    if family == FAMILY_SNMP:
        return _write_snmp(entry)
    if family == FAMILY_MAINTENANCE:
        return _write_maintenance(entry)
    if family == FAMILY_CONTACTS:
        return _write_contacts(entry)
    if family == FAMILY_VENDORS:
        return _write_vendors(entry)
    raise ValueError(f"unsupported family {family}")


def _payload_records(entry) -> list[dict]:
    env = entry.envelope if isinstance(entry.envelope, dict) else {}
    payload = env.get("payload")
    if payload is None and isinstance(entry.result, dict):
        payload = entry.result
    if not isinstance(payload, dict):
        return []
    records = payload.get("records")
    if isinstance(records, list) and records:
        return [r for r in records if isinstance(r, dict)]
    data = payload.get("data")
    if isinstance(data, dict):
        # SNMP single-device envelope
        if data.get("device_mac") or data.get("metrics"):
            return [data]
        nested = data.get("records")
        if isinstance(nested, list):
            return [r for r in nested if isinstance(r, dict)]
    return []


def _write_inventory(entry) -> int:
    from dose.models.topic_history import InventoryProductHistory

    records = _payload_records(entry)
    if not records:
        # Still acknowledge empty capture
        return 0
    n = 0
    with transaction.atomic():
        for rec in records:
            odoo_id = rec.get("id")
            try:
                odoo_id = int(odoo_id) if odoo_id is not None else None
            except (TypeError, ValueError):
                odoo_id = None
            price = rec.get("list_price")
            list_price = None
            if price is not None and price != "":
                try:
                    list_price = Decimal(str(price))
                except (InvalidOperation, ValueError):
                    list_price = None
            InventoryProductHistory.objects.create(
                topic=entry.topic or "",
                source_event_id=entry.event_id or "",
                source_mailbox_id=entry.id,
                odoo_id=odoo_id,
                name=str(rec.get("name") or rec.get("display_name") or "")[:255],
                default_code=str(rec.get("default_code") or "")[:128],
                list_price=list_price,
                raw_record=rec,
            )
            n += 1
    return n


def _write_snmp(entry) -> int:
    from dose.models.topic_history import SnmpTelemetryHistory

    records = _payload_records(entry)
    if not records:
        env = entry.envelope if isinstance(entry.envelope, dict) else {}
        payload = env.get("payload") if isinstance(env.get("payload"), dict) else {}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if data:
            records = [data]
    n = 0
    with transaction.atomic():
        for rec in records:
            metrics = rec.get("metrics") if isinstance(rec.get("metrics"), dict) else {}
            SnmpTelemetryHistory.objects.create(
                topic=entry.topic or "",
                source_event_id=entry.event_id or "",
                source_mailbox_id=entry.id,
                device_mac=str(rec.get("device_mac") or "")[:64],
                device_name=str(rec.get("device_name") or "")[:255],
                ip_address=str(rec.get("ip_address") or "")[:64],
                status=str(metrics.get("status") or rec.get("status") or "")[:32],
                cpu_utilization=_float_or_none(metrics.get("cpu_utilization")),
                temperature_c=_float_or_none(metrics.get("temperature_c")),
                raw_record=rec,
            )
            n += 1
            # Mirror into maintenance history when anomalous
            status = str(metrics.get("status") or "").lower()
            temp = _float_or_none(metrics.get("temperature_c"))
            if status in ("down", "critical", "offline", "error") or (
                temp is not None and temp >= 60
            ):
                from dose.models.topic_history import MaintenanceEquipmentHistory

                MaintenanceEquipmentHistory.objects.create(
                    topic=entry.topic or "",
                    source_event_id=entry.event_id or "",
                    source_mailbox_id=entry.id,
                    equipment_name=str(rec.get("device_name") or "")[:255],
                    serial_no=str(rec.get("device_mac") or "")[:128],
                    category="Network / SNMP",
                    anomaly=True,
                    request_name=f"SNMP alert: {rec.get('device_name') or rec.get('device_mac')} ({status or 'hot'})"[:255],
                    raw_record=rec,
                )
    return n


def _write_maintenance(entry) -> int:
    from dose.models.topic_history import MaintenanceEquipmentHistory

    records = _payload_records(entry)
    n = 0
    with transaction.atomic():
        for rec in records:
            MaintenanceEquipmentHistory.objects.create(
                topic=entry.topic or "",
                source_event_id=entry.event_id or "",
                source_mailbox_id=entry.id,
                equipment_name=str(rec.get("name") or rec.get("device_name") or "")[:255],
                serial_no=str(rec.get("serial_no") or rec.get("device_mac") or "")[:128],
                category=str(rec.get("category") or "")[:128],
                anomaly=bool(rec.get("anomaly")),
                request_name=str(rec.get("request_name") or "")[:255],
                raw_record=rec,
            )
            n += 1
    return n


def _write_contacts(entry) -> int:
    from dose.models.topic_history import ContactHistory
    from dose.services.contact_capture import contact_topic

    records = _payload_records(entry)
    shared_topic = contact_topic(actor="system")
    n = 0
    with transaction.atomic():
        for rec in records:
            raw = rec.get("raw_record") if isinstance(rec.get("raw_record"), dict) else rec
            ContactHistory.objects.create(
                topic=shared_topic,
                source_event_id=entry.event_id or "",
                source_mailbox_id=entry.id,
                source_app=str(rec.get("source_app") or "")[:32],
                external_id=str(rec.get("external_id") or rec.get("id") or "")[:128],
                name=str(rec.get("name") or "")[:255],
                email=str(rec.get("email") or "")[:255],
                phone=str(rec.get("phone") or "")[:64],
                company=str(rec.get("company") or rec.get("parent_name") or "")[:255],
                username=str(rec.get("username") or "")[:128],
                active=bool(rec.get("active", True)),
                raw_record=raw if isinstance(raw, dict) else {},
            )
            n += 1
    return n


def _write_vendors(entry) -> int:
    from dose.models.topic_history import VendorHistory
    from dose.services.vendor_capture import vendor_topic

    records = _payload_records(entry)
    if not records:
        env = entry.envelope if isinstance(entry.envelope, dict) else {}
        payload = env.get("payload") if isinstance(env.get("payload"), dict) else {}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if data:
            records = [data]
    shared_topic = vendor_topic(actor="system")
    n = 0
    with transaction.atomic():
        for rec in records:
            vid = rec.get("odoo_vendor_id") or rec.get("id")
            cid = rec.get("odoo_contact_id")
            try:
                vid = int(vid) if vid is not None and vid != "" else None
            except (TypeError, ValueError):
                vid = None
            try:
                cid = int(cid) if cid is not None and cid != "" else None
            except (TypeError, ValueError):
                cid = None
            VendorHistory.objects.create(
                topic=shared_topic,
                source_event_id=entry.event_id or "",
                source_mailbox_id=entry.id,
                odoo_vendor_id=vid,
                odoo_contact_id=cid,
                name=str(rec.get("name") or rec.get("vendor_name") or "")[:255],
                email=str(rec.get("email") or "")[:255],
                region=str(rec.get("region") or "")[:255],
                raw_record=rec,
            )
            n += 1
    return n


def _float_or_none(val: Any):
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _feed_odoo_from_snmp_history(topic: str, *, tenant) -> dict:
    """
    Optional Type 1: after SNMP consume, upsert Odoo maintenance from
    recent history rows for this topic.
    """
    from django.db import connection

    from dose.models.topic_history import SnmpTelemetryHistory
    from dose.services.odoo_rpc import OdooRpcClient, OdooRpcError, load_odoo_rpc_config
    from dose.services.snmp_to_odoo_maintenance import SnmpToOdooMaintenance

    recent = list(
        SnmpTelemetryHistory.objects.filter(topic=topic).order_by("-consumed_at")[:50]
    )
    if not recent:
        return {"ok": True, "equipment": 0, "requests": 0}

    class _Req:
        tenant = None
        body = b""

    req = _Req()
    req.tenant = tenant
    # Ensure tenant schema for history reads already set; Odoo config may touch public.
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

    try:
        config = load_odoo_rpc_config(request=req)
        client = OdooRpcClient.from_config(config)
        client.authenticate()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    category_id = SnmpToOdooMaintenance._ensure_category(client)
    eq = 0
    reqs = 0
    for row in recent:
        rec = row.raw_record if isinstance(row.raw_record, dict) else {}
        mac = row.device_mac or rec.get("device_mac") or ""
        name = row.device_name or rec.get("device_name") or mac
        if not mac and not name:
            continue
        try:
            eid = SnmpToOdooMaintenance._upsert_equipment(
                client, name=name, mac=mac or name, category_id=category_id, payload=rec
            )
            eq += 1
            metrics = rec.get("metrics") if isinstance(rec.get("metrics"), dict) else {}
            if SnmpToOdooMaintenance._is_anomaly(metrics, 60):
                SnmpToOdooMaintenance._create_request(
                    client, equipment_id=eid, payload=rec, metrics=metrics
                )
                reqs += 1
        except OdooRpcError as exc:
            return {"ok": False, "error": str(exc), "equipment": eq, "requests": reqs}
    return {"ok": True, "equipment": eq, "requests": reqs}
