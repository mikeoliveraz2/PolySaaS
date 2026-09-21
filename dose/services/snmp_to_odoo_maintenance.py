"""
SnmpToOdooMaintenance — dumb webhook enroll onto SNMP topic (pending).

POST /dose/webhook/snmp/<tenant_slug>/
  → enroll WebhookMailbox as pending on topic RES.snmp.telemetry.<slug>
  → Admin Topic browser → Consume drains to history (+ optional Odoo feed)

Odoo maintenance.equipment / request writes run on Consume, not in this accept path.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from dose.models.webhook_mailbox import CAPTURE_MAILBOX_TTL_SECONDS, WebhookMailbox
from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import instruction_config, service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.odoo_rpc import OdooRpcClient, OdooRpcError, load_odoo_rpc_config
from dose.tenant_app_lookup import tenant_schema_search_path

logger = logging.getLogger(__name__)

DEFAULT_TEMP_CRITICAL = 60
EQUIPMENT_CATEGORY_NAME = "Network / SNMP"


class SnmpToOdooMaintenance(AtomicServiceBase):
    """SNMP JSON → pending topic mailbox (Consume → history + optional Odoo)."""

    atomic_apps = ("odoo",)
    atomic_category = "integration"

    @staticmethod
    def get_parameters(parameters, key="SnmpToOdooMaintenance"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        tenant = getattr(request, "tenant", None)
        if tenant is None or not getattr(tenant, "schema_name", None):
            return service_result(
                "SnmpToOdooMaintenance", status="error", error="missing_tenant"
            )

        payload = SnmpToOdooMaintenance._parse_body(request)
        if not payload:
            return service_result(
                "SnmpToOdooMaintenance",
                status="skipped",
                reason="empty_or_invalid_json",
            )

        mailbox = SnmpToOdooMaintenance._enroll_mailbox(
            tenant, payload, instruction_row
        )
        if not mailbox.get("success"):
            return service_result(
                "SnmpToOdooMaintenance",
                status="error",
                error=mailbox.get("error") or "mailbox_enroll_failed",
                mailbox=mailbox,
            )

        return service_result(
            "SnmpToOdooMaintenance",
            status="ok",
            mailbox=mailbox,
            note="enrolled_pending — use Topic browser Consume to drain",
        )

    @staticmethod
    def _parse_body(request) -> dict | None:
        raw = getattr(request, "body", None) or b""
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not raw:
            return None
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return None
        if isinstance(data, list) and data and isinstance(data[0], dict):
            data = data[0]
        if not isinstance(data, dict):
            return None
        return data

    @staticmethod
    def _is_anomaly(metrics: dict, temp_critical: int) -> bool:
        status = str(metrics.get("status") or "").strip().lower()
        if status in ("down", "critical", "offline", "error"):
            return True
        try:
            temp = float(metrics.get("temperature_c"))
        except (TypeError, ValueError):
            return False
        return temp >= float(temp_critical)

    @staticmethod
    def _enroll_mailbox(tenant, payload: dict, instruction_row) -> dict:
        schema = tenant.schema_name
        event_id = str(payload.get("event_id") or uuid.uuid4().hex)
        correlation_id = str(uuid.uuid4())
        device = payload.get("device_name") or payload.get("device_mac") or "snmp-device"
        topic = f"RES.snmp.telemetry.{getattr(tenant, 'slug', schema)}"
        action_path = "/webhook/snmp/inbound"
        metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
        envelope = {
            "kind": "polysaas.capture.v1",
            "event_id": event_id.replace("-", "")[:64],
            "correlation_id": correlation_id,
            "tenant_schema": schema,
            "source": "snmp",
            "action_path": action_path,
            "method": "POST",
            "direction": "REQ",
            "event_key": getattr(instruction_row, "eventKey", None) or "snmp.telemetry",
            "topic": topic,
            "payload": {
                "capture": "snmp_inbound",
                "device_name": device,
                "device_mac": payload.get("device_mac"),
                "data": payload,
                "records": [
                    {
                        "device_mac": payload.get("device_mac"),
                        "device_name": device,
                        "ip_address": payload.get("ip_address"),
                        "status": metrics.get("status"),
                        "cpu_utilization": metrics.get("cpu_utilization"),
                        "temperature_c": metrics.get("temperature_c"),
                        "timestamp": payload.get("timestamp"),
                    }
                ],
                "record_count": 1,
            },
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with tenant_schema_search_path(tenant) as ok:
                if not ok:
                    return {"success": False, "error": "invalid tenant schema"}
            row = WebhookMailbox.create_from_envelope(
                envelope,
                ttl_seconds=CAPTURE_MAILBOX_TTL_SECONDS,
                status="pending",
                result={
                    "snmp": True,
                    "pending_consume": True,
                    "device_mac": payload.get("device_mac"),
                    "records": envelope["payload"]["records"],
                    "record_count": 1,
                },
                tenant=tenant,
            )
            return {
                "success": True,
                "mailbox_id": row.id,
                "event_id": row.event_id,
                "topic": topic,
            }
        except Exception as exc:
            logger.warning("[SNMP→mailbox] enroll failed: %s", exc, exc_info=True)
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _feed_odoo(
        request,
        payload: dict,
        *,
        instruction_row=None,
        temp_critical: int,
        create_requests: bool,
    ) -> dict:
        mac = (payload.get("device_mac") or "").strip()
        name = (payload.get("device_name") or mac or "SNMP Device").strip()
        if not mac and not name:
            raise OdooRpcError("error", "missing device_mac and device_name")

        metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        client = OdooRpcClient.from_config(config)
        client.authenticate()

        category_id = SnmpToOdooMaintenance._ensure_category(client)
        equipment_id = SnmpToOdooMaintenance._upsert_equipment(
            client, name=name, mac=mac or name, category_id=category_id, payload=payload
        )

        out = {
            "equipment_id": equipment_id,
            "category_id": category_id,
            "device_mac": mac,
            "device_name": name,
            "metrics": metrics,
            "request_id": None,
        }

        if create_requests and SnmpToOdooMaintenance._is_anomaly(metrics, temp_critical):
            req_id = SnmpToOdooMaintenance._create_request(
                client, equipment_id=equipment_id, payload=payload, metrics=metrics
            )
            out["request_id"] = req_id
            out["anomaly"] = True
        else:
            out["anomaly"] = False

        return out

    @staticmethod
    def _ensure_category(client: OdooRpcClient) -> int:
        ids = client.execute_kw(
            "maintenance.equipment.category",
            "search",
            [[["name", "=", EQUIPMENT_CATEGORY_NAME]]],
            {"limit": 1},
        )
        if ids:
            return int(ids[0])
        return int(
            client.execute_kw(
                "maintenance.equipment.category",
                "create",
                [{"name": EQUIPMENT_CATEGORY_NAME}],
            )
        )

    @staticmethod
    def _upsert_equipment(
        client: OdooRpcClient, *, name: str, mac: str, category_id: int, payload: dict
    ) -> int:
        # Prefer serial_no = MAC for stable identity across Week 1 / Week 2.
        ids = client.execute_kw(
            "maintenance.equipment",
            "search",
            [[["serial_no", "=", mac]]],
            {"limit": 1},
        )
        vals = {
            "name": name[:120],
            "serial_no": mac[:64],
            "category_id": category_id,
            "note": (
                f"SNMP feed\n"
                f"ip={payload.get('ip_address') or ''}\n"
                f"last_event={payload.get('event_id') or ''}\n"
                f"last_ts={payload.get('timestamp') or ''}"
            ),
        }
        if ids:
            eid = int(ids[0])
            client.execute_kw("maintenance.equipment", "write", [[eid], vals])
            return eid
        return int(client.execute_kw("maintenance.equipment", "create", [vals]))

    @staticmethod
    def _create_request(
        client: OdooRpcClient, *, equipment_id: int, payload: dict, metrics: dict
    ) -> int:
        device = payload.get("device_name") or payload.get("device_mac") or "device"
        status = metrics.get("status")
        temp = metrics.get("temperature_c")
        cpu = metrics.get("cpu_utilization")
        name = f"SNMP alert: {device} ({status})"
        description = (
            f"Auto-opened by PolySaaS SNMP orchestration.\n"
            f"device_mac={payload.get('device_mac')}\n"
            f"ip={payload.get('ip_address')}\n"
            f"status={status}\n"
            f"cpu_utilization={cpu}\n"
            f"temperature_c={temp}\n"
            f"event_id={payload.get('event_id')}\n"
            f"timestamp={payload.get('timestamp')}\n"
        )
        vals = {
            "name": name[:120],
            "equipment_id": equipment_id,
            "description": description,
            "maintenance_type": "corrective",
            "priority": "2",
        }
        # Avoid duplicate open requests for same equipment + same alert title.
        existing = client.execute_kw(
            "maintenance.request",
            "search",
            [[
                ["equipment_id", "=", equipment_id],
                ["name", "=", vals["name"]],
            ]],
            {"limit": 1},
        )
        if existing:
            return int(existing[0])
        try:
            return int(client.execute_kw("maintenance.request", "create", [vals]))
        except Exception:
            # Some Odoo builds use different field names — retry minimal
            minimal = {
                "name": vals["name"],
                "equipment_id": equipment_id,
                "description": description,
            }
            return int(client.execute_kw("maintenance.request", "create", [minimal]))
