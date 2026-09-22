from __future__ import annotations

import hashlib
import json
import uuid
from types import SimpleNamespace

from django.db import connection, transaction
from django.utils import timezone

from dose.models import Instruction, MQConfig, RequestLog, UserTenantMembership
from dose.passthrough.orchestration_hook import _save_callback_data
from dose.messaging import create_orchestration_feedback
from dose.tenant_app_lookup import tenant_schema_search_path


TRIGGER_ENVELOPE_KIND = "polysaas.trigger.v1"
SLACK_POLY_ACTION_PATH = "/events/slack/command/poly"
SLACK_POLY_EVENT_KEY = "slack.command.poly"
SLACK_TRIGGER_ROUTING_KEY = "polysaas.events.slack.command.poly"
SLACK_WIREFRAME_ACTIONS = {
    "contact": (
        "/events/slack/webhook/contact",
        "slack.webhook.contact",
    ),
    "sale": (
        "/events/slack/webhook/sale",
        "slack.webhook.sale",
    ),
}
# Odoo Control Panel → New contact (dynamic orch → OdooCreatePartner)
ODOO_CP_CONTACT_ACTION_PATH = "/events/odoo/control-panel/contact"
ODOO_CP_CONTACT_EVENT_KEY = "odoo.control_panel.contact"
SLACK_CONTACT_ACTION_PATH = "/events/slack/message/contact"
SLACK_CONTACT_EVENT_KEY = "slack.message.contact"
SLACK_CONTACT_ROUTING_KEY = "polysaas.events.slack.message.contact"


def _slack_event_id(payload: dict[str, str]) -> str:
    stable = "\x1f".join(
        [
            payload.get("team_id", ""),
            payload.get("trigger_id", ""),
            payload.get("user_id", ""),
            payload.get("command", ""),
            payload.get("text", ""),
        ]
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def build_slack_command_envelope(tenant, payload: dict[str, str]) -> dict:
    return {
        "kind": TRIGGER_ENVELOPE_KIND,
        "event_id": _slack_event_id(payload),
        "correlation_id": str(uuid.uuid4()),
        "tenant_schema": tenant.schema_name,
        "source": "slack",
        "action_path": SLACK_POLY_ACTION_PATH,
        "method": "POST",
        "direction": "REQ",
        "event_key": SLACK_POLY_EVENT_KEY,
        "actor": {
            "external_user_id": payload.get("user_id", ""),
            "team_id": payload.get("team_id", ""),
        },
        "payload": {
            "command": payload.get("command", ""),
            "text": payload.get("text", ""),
            "channel_id": payload.get("channel_id", ""),
            "response_url": payload.get("response_url", ""),
        },
        "received_at": timezone.now().isoformat(),
    }


def publish_slack_command_event(tenant, payload: dict[str, str]) -> dict:
    """
    Publish Slack command event to webhook mailbox.
    
    Builds canonical envelope and writes to WebhookMailbox for consumer processing.
    Returns immediately after mailbox write (no blocking RabbitMQ publish).
    """
    from dose.models import WebhookMailbox

    envelope = build_slack_command_envelope(tenant, payload)
    
    try:
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return {"success": False, "error": "invalid tenant schema"}
            
            # Write to mailbox with 5 minute TTL
            mailbox = WebhookMailbox.create_from_envelope(
                envelope, ttl_seconds=300, tenant=tenant,
            )
            
        return {
            "success": True,
            "event_id": envelope["event_id"],
            "action_path": envelope["action_path"],
            "mailbox_id": mailbox.id,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to write to mailbox: {exc}",
            "event_id": envelope.get("event_id"),
        }


def build_slack_wireframe_envelope(tenant, kind: str, payload: dict) -> dict:
    """Build a real trigger envelope from the deterministic Slack demo UI."""
    if kind not in SLACK_WIREFRAME_ACTIONS:
        raise ValueError("unsupported Slack wireframe event")
    action_path, event_key = SLACK_WIREFRAME_ACTIONS[kind]
    event_seed = json.dumps(
        {
            "tenant": tenant.schema_name,
            "kind": kind,
            "demo_id": payload.get("demo_id", ""),
        },
        sort_keys=True,
    )
    return {
        "kind": TRIGGER_ENVELOPE_KIND,
        "event_id": hashlib.sha256(event_seed.encode("utf-8")).hexdigest(),
        "correlation_id": str(uuid.uuid4()),
        "tenant_schema": tenant.schema_name,
        "source": "slack",
        "action_path": action_path,
        "method": "POST",
        "direction": "REQ",
        "event_key": event_key,
        "actor": {"external_user_id": "polysaas-wireframe"},
        "payload": dict(payload),
        "received_at": timezone.now().isoformat(),
    }


def publish_slack_wireframe_event(tenant, kind: str, payload: dict) -> dict:
    """Queue a wireframe action in the same tenant mailbox as real webhooks."""
    from dose.models import WebhookMailbox

    try:
        envelope = build_slack_wireframe_envelope(tenant, kind, payload)
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return {"success": False, "error": "invalid tenant schema"}
            mailbox = WebhookMailbox.create_from_envelope(
                envelope,
                ttl_seconds=300,
                tenant=tenant,
            )
        return {
            "success": True,
            "event_id": envelope["event_id"],
            "action_path": envelope["action_path"],
            "mailbox_id": mailbox.id,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to write to mailbox: {exc}",
        }


def build_odoo_cp_contact_envelope(tenant, payload: dict) -> dict:
    """Odoo Control Panel New contact → mailbox envelope for OdooCreatePartner."""
    event_seed = json.dumps(
        {
            "tenant": tenant.schema_name,
            "kind": "odoo_cp_contact",
            "demo_id": payload.get("demo_id", ""),
            "email": payload.get("email", ""),
            "name": payload.get("name", ""),
        },
        sort_keys=True,
    )
    return {
        "kind": TRIGGER_ENVELOPE_KIND,
        "event_id": hashlib.sha256(event_seed.encode("utf-8")).hexdigest(),
        "correlation_id": str(uuid.uuid4()),
        "tenant_schema": tenant.schema_name,
        "source": "odoo",
        "action_path": ODOO_CP_CONTACT_ACTION_PATH,
        "method": "POST",
        "direction": "REQ",
        "event_key": ODOO_CP_CONTACT_EVENT_KEY,
        "actor": {"external_user_id": "odoo-control-panel"},
        "payload": dict(payload),
        "received_at": timezone.now().isoformat(),
    }


def publish_odoo_cp_contact_event(tenant, payload: dict) -> dict:
    """Queue Odoo Control Panel contact create in tenant WebhookMailbox."""
    from dose.models import WebhookMailbox

    try:
        envelope = build_odoo_cp_contact_envelope(tenant, payload)
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return {"success": False, "error": "invalid tenant schema"}
            mailbox = WebhookMailbox.create_from_envelope(
                envelope,
                ttl_seconds=300,
                tenant=tenant,
            )
        return {
            "success": True,
            "event_id": envelope["event_id"],
            "action_path": envelope["action_path"],
            "mailbox_id": mailbox.id,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to write to mailbox: {exc}",
        }


def _claim_event(envelope: dict, tenant) -> bool:
    event_id = envelope["event_id"]
    lock_material = f"{tenant.schema_name}:{event_id}".encode("utf-8")
    lock_id = int.from_bytes(hashlib.sha256(lock_material).digest()[:8], "big", signed=True)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
        if RequestLog.objects.filter(
            path=envelope["action_path"],
            method="EVENT",
            body__event_id=event_id,
        ).exists():
            return False
        RequestLog.objects.create(
            user=None,
            tenant=tenant,
            path=envelope["action_path"],
            method="EVENT",
            body={
                "event_id": event_id,
                "correlation_id": envelope.get("correlation_id", ""),
                "source": envelope.get("source", ""),
                "status": "claimed",
            },
        )
    return True


def _request_for_envelope(envelope: dict, tenant):
    payload = envelope.get("payload") or {}
    body = json.dumps(payload).encode("utf-8")
    return SimpleNamespace(
        body=body,
        method=envelope["method"],
        path=envelope["action_path"],
        headers={},
        GET={},
        POST=payload,
        user=None,
        tenant=tenant,
        atomic_parameters=[],
        mq_message_data=payload,
        trigger_envelope=envelope,
        correlation_id=envelope.get("correlation_id", ""),
    )


def _feedback_users(tenant) -> list:
    users = list(
        UserTenantMembership.objects.filter(tenant=tenant)
        .select_related("user")
        .values_list("user", flat=True)
    )
    if not users:
        return [None]
    from django.contrib.auth import get_user_model

    return list(get_user_model().objects.filter(pk__in=users))


def build_slack_contact_envelope(tenant, payload: dict) -> dict:
    """
    Build envelope for Slack message → Odoo contact creation.
    
    Payload should contain: name, email, company, plus Slack metadata.
    """
    event_seed = json.dumps(
        {
            "tenant": tenant.schema_name,
            "slack_team_id": payload.get("slack_team_id", ""),
            "slack_message_ts": payload.get("slack_message_ts", ""),
            "slack_channel_id": payload.get("slack_channel_id", ""),
        },
        sort_keys=True,
    )
    event_id = hashlib.sha256(event_seed.encode("utf-8")).hexdigest()
    
    return {
        "kind": TRIGGER_ENVELOPE_KIND,
        "event_id": event_id,
        "correlation_id": str(uuid.uuid4()),
        "tenant_schema": tenant.schema_name,
        "source": "slack",
        "action_path": SLACK_CONTACT_ACTION_PATH,
        "method": "POST",
        "direction": "REQ",
        "event_key": SLACK_CONTACT_EVENT_KEY,
        "actor": {
            "external_user_id": payload.get("slack_user_id", ""),
            "team_id": payload.get("slack_team_id", ""),
        },
        "payload": {
            "name": payload.get("name", ""),
            "email": payload.get("email", ""),
            "company": payload.get("company", ""),
            "slack_user_id": payload.get("slack_user_id", ""),
            "slack_channel_id": payload.get("slack_channel_id", ""),
            "slack_message_ts": payload.get("slack_message_ts", ""),
        },
        "received_at": timezone.now().isoformat(),
    }


def publish_slack_contact_event(tenant, payload: dict) -> dict:
    """
    Publish Slack contact creation event to webhook mailbox.
    
    Returns immediately after mailbox write (no blocking RabbitMQ publish).
    """
    from dose.models import WebhookMailbox
    
    try:
        envelope = build_slack_contact_envelope(tenant, payload)
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return {"success": False, "error": "invalid tenant schema"}
            
            mailbox = WebhookMailbox.create_from_envelope(
                envelope,
                ttl_seconds=300,
                tenant=tenant,
            )
            
            return {
                "success": True,
                "event_id": envelope["event_id"],
                "action_path": envelope["action_path"],
                "mailbox_id": mailbox.id,
            }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to write to mailbox: {exc}",
            "event_id": envelope.get("event_id") if 'envelope' in locals() else None,
        }


def process_trigger_envelope(envelope: dict, tenant) -> dict:
    if envelope.get("kind") != TRIGGER_ENVELOPE_KIND:
        return {"status": "ignored", "error": "unsupported envelope kind"}
    if envelope.get("tenant_schema") != getattr(tenant, "schema_name", None):
        return {"status": "ignored", "error": "tenant mismatch"}
    if not envelope.get("event_id"):
        return {"status": "ignored", "error": "missing event_id"}
    request = _request_for_envelope(envelope, tenant)
    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return {"status": "error", "error": "invalid tenant schema"}
        if not _claim_event(envelope, tenant):
            return {"status": "duplicate", "event_id": envelope["event_id"]}
        instructions = list(
            Instruction.objects.filter(
                requestpath=envelope["action_path"],
                requestmethod=envelope["method"],
                direction=envelope["direction"],
            )
        )
        results = []
        for instruction in instructions:
            result = {
                "status": "success",
                "event_id": envelope["event_id"],
                "correlation_id": envelope.get("correlation_id", ""),
                "path": envelope["action_path"],
                "method": envelope["method"],
                "direction": envelope["direction"],
                "instruction_id": instruction.id,
                "eventKey": instruction.eventKey or envelope.get("event_key", ""),
                "executescript": instruction.executescript or "",
            }
            try:
                atomic_result = instruction.execute_atomic_service(request)
                if isinstance(atomic_result, dict):
                    result.update(atomic_result)
                    result["executescript"] = (
                        instruction.executescript or result.get("executescript") or ""
                    )
                elif atomic_result is not None:
                    result["service_result"] = atomic_result
            except Exception as exc:
                result["status"] = "error"
                result["error"] = str(exc)

            _save_callback_data(request, instruction, result, tenant)
            for user in _feedback_users(tenant):
                create_orchestration_feedback(
                    tenant=tenant,
                    user=user,
                    instruction=instruction,
                    result=result,
                )
            results.append(result)

    return {
        "status": "processed" if instructions else "no_instruction",
        "event_id": envelope["event_id"],
        "matched": len(instructions),
        "results": results,
    }
