"""
Capture HTTP traffic atomics — Odoo-first MQ path (RabbitMQ).

CaptureGetResponse   — Instruction direction=RES, requestmethod=GET
  Runs after the upstream response arrives; captures returned body/data.

CapturePostResponse  — Instruction direction=RES, requestmethod=POST
  Runs after a POST returns (e.g. Odoo web_search_read). Captures the
  response dict that already holds list rows before the SPA renders them.

CapturePostRequest   — Instruction direction=REQ, requestmethod=POST
  Captures the outbound POST body as it goes to the upstream app.

All publish to RabbitMQ with topic {REQ|RES}.{action_path}.{username}
(see dose.utils.mq_topic) — RES for response capture, REQ for request capture.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Tuple

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.atomic_service_utils import (
    instruction_config,
    maybe_save_callback,
    service_result,
)
from dose.utils.mq_topic import build_mq_topic, topic_from_request

logger = logging.getLogger(__name__)

# Cap payload size so HTML pages / large JSON do not blow the broker.
_MAX_CAPTURE_CHARS = 100_000


def _parse_body(raw: Any) -> Tuple[Any, str]:
    """Return (parsed_or_text, kind) where kind is json|text|empty|bytes."""
    if raw is None:
        return None, "empty"
    if isinstance(raw, (dict, list)):
        return raw, "json"
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            return {"_bytes_len": len(raw)}, "bytes"
    else:
        text = str(raw)

    text = text.strip()
    if not text:
        return None, "empty"
    try:
        return json.loads(text), "json"
    except Exception:
        return text, "text"


def _truncate(data: Any, max_chars: int = _MAX_CAPTURE_CHARS) -> Any:
    """
    Cap payload size without destroying list ``records``.

    Large Odoo list responses used to become ``{_truncated, _preview}`` which
    stripped ``records[]`` and made the mailbox demo useless.
    """
    if data is None:
        return None

    # Prefer keeping records[] intact (mailbox history / admin table).
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        records = list(data["records"])
        keep = {
            k: v for k, v in data.items() if k != "records"
        }
        keep["record_count"] = len(records)
        # Slim rows first if needed
        slim_keys = (
            "id",
            "default_code",
            "display_name",
            "name",
            "qty_available",
            "virtual_available",
            "quantity",
            "inventory_quantity",
            "location_id",
            "product_id",
            "list_price",
            "uom_id",
            "type",
            "categ_id",
            "barcode",
        )

        def _slim_row(row):
            if not isinstance(row, dict):
                return row
            slim = {k: row[k] for k in slim_keys if k in row}
            return slim or {k: row[k] for k in list(row.keys())[:12]}

        slim_records = [_slim_row(r) for r in records]
        candidate = {**keep, "records": slim_records}
        dumped = json.dumps(candidate, default=str)
        if len(dumped) <= max_chars:
            return candidate
        # Drop rows until under budget (keep newest/first N).
        for n in (100, 50, 25, 10, 5, 1):
            candidate = {
                **keep,
                "records": slim_records[:n],
                "record_count": len(records),
                "_records_truncated": len(records) > n,
                "_records_shown": min(n, len(slim_records)),
            }
            if len(json.dumps(candidate, default=str)) <= max_chars:
                return candidate
        return {
            **keep,
            "records": slim_records[:1],
            "record_count": len(records),
            "_records_truncated": True,
            "_records_shown": 1,
        }

    if isinstance(data, (dict, list)):
        dumped = json.dumps(data, default=str)
        if len(dumped) <= max_chars:
            return data
        return {
            "_truncated": True,
            "_original_chars": len(dumped),
            "_preview": dumped[:max_chars],
        }
    text = str(data)
    if len(text) <= max_chars:
        return data
    return text[:max_chars] + f"…[+{len(text) - max_chars} chars]"


def _normalize_list_payload(data: Any) -> Any:
    """
    Surface Odoo web_search_read / search_read records for mailbox history.

    Odoo JSON-RPC list loads look like:
      {"jsonrpc": "2.0", "id": …, "result": {"records": […], "length": N}}
    or sometimes ``result`` is already a list of rows.
    """
    if not isinstance(data, dict):
        return data

    result = data.get("result")
    if isinstance(result, dict) and isinstance(result.get("records"), list):
        records = result.get("records") or []
        return {
            "records": records,
            "length": result.get("length", len(records)),
            "record_count": len(records),
            "source": "odoo_web_search_read",
        }
    # Some Odoo call_kw methods return result as a bare list of dicts.
    if isinstance(result, list) and result and isinstance(result[0], dict):
        return {
            "records": result,
            "length": len(result),
            "record_count": len(result),
            "source": "odoo_result_list",
        }
    if isinstance(data.get("records"), list):
        records = data.get("records") or []
        return {
            "records": records,
            "length": data.get("length", len(records)),
            "record_count": len(records),
            "source": "records_dict",
        }
    return data


def _username_from_request(request) -> str:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return getattr(user, "username", None) or "anonymous"
    return "anonymous"


def _action_path(request, instruction_row) -> str:
    path = (
        getattr(instruction_row, "requestpath", None)
        or getattr(request, "path", None)
        or ""
    )
    return str(path).strip() or "/"


def _publish(topic: str, message: dict) -> dict:
    from dose.services.data_extractor import EndpointDataExtractor

    return EndpointDataExtractor._publish_to_mq(topic, message)


def _enroll_capture_mailbox(request, instruction_row, topic: str, message: dict, publish_result) -> dict:
    """
    Write-free mailbox enroll for captures (mailbox/topic pattern).

    Always attempts a WebhookMailbox row with the MQ topic and a useful TTL.
    Does not depend on Instruction.save_callbackdata. Status=pending so Topic
    browser Consume can drain captures into typed report tables.
    """
    import uuid

    from django.utils import timezone as dj_timezone

    from dose.models import WebhookMailbox
    from dose.models.webhook_mailbox import CAPTURE_MAILBOX_TTL_SECONDS
    from dose.services.atomic_service_utils import tenant_from_request
    from dose.tenant_app_lookup import tenant_schema_search_path

    tenant = tenant_from_request(request)
    if tenant is None:
        try:
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)
        except Exception:
            tenant = None
    if tenant is None or not getattr(tenant, "schema_name", None):
        logger.warning("[Capture] mailbox enroll skipped — no tenant on request")
        return {"success": False, "error": "no_tenant"}

    cfg = instruction_config(instruction_row)
    ttl = int(cfg.get("mailbox_ttl_seconds") or CAPTURE_MAILBOX_TTL_SECONDS)

    correlation_id = str(uuid.uuid4())
    event_id = uuid.uuid4().hex
    published = message.get("data")
    envelope = {
        "kind": "polysaas.capture.v1",
        "event_id": event_id,
        "correlation_id": correlation_id,
        "tenant_schema": tenant.schema_name,
        "source": "passthrough",
        "action_path": message.get("action_path") or "",
        "method": message.get("method") or "",
        "direction": message.get("direction") or "",
        "event_key": message.get("eventKey") or getattr(instruction_row, "eventKey", None) or "",
        "topic": topic,
        "actor": {"username": message.get("username") or "anonymous"},
        "payload": {
            "capture": message.get("capture"),
            "topic": topic,
            "data": published,
            "records": (
                published.get("records")
                if isinstance(published, dict)
                else None
            ),
            "record_count": (
                published.get("record_count")
                if isinstance(published, dict)
                else None
            ),
            "response_meta": message.get("response_meta"),
            "request_meta": message.get("request_meta"),
            "instruction_id": message.get("instruction_id"),
            "publish_result": publish_result,
        },
        "received_at": dj_timezone.now().isoformat(),
    }
    result_summary = {
        "topic": topic,
        "capture": message.get("capture"),
        "publish_result": publish_result,
        "data": published,
        "records": envelope["payload"].get("records"),
        "record_count": envelope["payload"].get("record_count"),
        "response_meta": message.get("response_meta"),
        "request_meta": message.get("request_meta"),
    }

    try:
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return {"success": False, "error": "invalid tenant schema"}
            row = WebhookMailbox.create_from_envelope(
                envelope,
                ttl_seconds=ttl,
                status="pending",
                result=result_summary,
                tenant=tenant,
            )
        return {
            "success": True,
            "mailbox_id": row.id,
            "event_id": event_id,
            "topic": topic,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "record_count": envelope["payload"].get("record_count"),
        }
    except Exception as exc:
        logger.warning("[Capture] mailbox enroll failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}


def _extract_upstream_response_payload(request) -> Tuple[Any, dict]:
    """
    Passthrough orch hook sets request._upstream_response (requests.Response).
    """
    meta = {
        "status_code": None,
        "content_type": "",
        "source": None,
    }
    upstream = getattr(request, "_upstream_response", None)
    if upstream is not None:
        meta["source"] = "upstream_response"
        meta["status_code"] = getattr(upstream, "status_code", None)
        headers = getattr(upstream, "headers", None) or {}
        try:
            meta["content_type"] = headers.get("Content-Type") or headers.get("content-type") or ""
        except Exception:
            meta["content_type"] = ""
        ct = (meta["content_type"] or "").lower()
        if "json" in ct:
            try:
                return upstream.json(), meta
            except Exception:
                pass
        content = getattr(upstream, "content", None)
        if content is None and hasattr(upstream, "text"):
            content = upstream.text
        parsed, kind = _parse_body(content)
        meta["body_kind"] = kind
        return parsed, meta

    if hasattr(request, "content") and not hasattr(request, "method"):
        meta["source"] = "http_response_arg"
        meta["status_code"] = getattr(request, "status_code", None)
        parsed, kind = _parse_body(getattr(request, "content", None))
        meta["body_kind"] = kind
        return parsed, meta

    meta["source"] = "missing"
    return None, meta


def _extract_post_body(request) -> Tuple[Any, dict]:
    meta = {"source": "request.body", "body_kind": "empty"}
    raw = getattr(request, "body", None)
    if raw:
        parsed, kind = _parse_body(raw)
        meta["body_kind"] = kind
        return parsed, meta

    if hasattr(request, "POST") and request.POST:
        meta["source"] = "request.POST"
        meta["body_kind"] = "form"
        return dict(request.POST), meta

    if hasattr(request, "mq_message_data") and request.mq_message_data:
        meta["source"] = "mq_message_data"
        meta["body_kind"] = "json"
        return request.mq_message_data, meta

    return None, meta


def _capture_response_side(
    *,
    request,
    instruction_row,
    service_name: str,
    capture_label: str,
    method_expected: str,
    allow_navigate_fallback: bool = False,
):
    """Shared RES capture → mailbox enroll (+ optional MQ)."""
    method = (getattr(request, "method", None) or "").upper()
    if hasattr(request, "content") and not hasattr(request, "method"):
        method = method_expected

    if method != method_expected:
        return service_result(
            service_name,
            status="skipped",
            reason=f"not_{method_expected.lower()}",
            method=method or "missing",
        )

    cfg = instruction_config(instruction_row)
    max_chars = int(cfg.get("max_chars", _MAX_CAPTURE_CHARS))
    publish = cfg.get("publish", True)

    data, meta = _extract_upstream_response_payload(request)
    if data is None and meta.get("source") == "missing":
        if not allow_navigate_fallback:
            return service_result(
                service_name,
                status="skipped",
                reason="no_upstream_response",
                response_meta=meta,
            )
        action_path = _action_path(request, instruction_row)
        data = {
            "capture_mode": "navigate",
            "path": action_path or getattr(request, "path", ""),
            "note": "no upstream response body (client-side navigation)",
        }
        meta = {
            "status_code": None,
            "content_type": "application/json",
            "source": "navigate_no_upstream",
            "body_kind": "json",
        }

    # Prefer the records dict Odoo already built for the list view.
    data = _normalize_list_payload(data)
    captured = _truncate(data, max_chars=max_chars)
    action_path = _action_path(request, instruction_row)
    if hasattr(request, "method"):
        topic = topic_from_request(request, action_path=action_path, direction="RES")
    else:
        topic = build_mq_topic(action_path, "anonymous", direction="RES")

    message = {
        "capture": capture_label,
        "topic": topic,
        "action_path": action_path,
        "method": method_expected,
        "direction": "RES",
        "response_meta": meta,
        "data": captured,
        "username": _username_from_request(request) or "anonymous",
        "instruction_id": getattr(instruction_row, "id", None),
        "eventKey": getattr(instruction_row, "eventKey", None),
    }

    mailbox_result = _enroll_capture_mailbox(
        request, instruction_row, topic, message, publish_result=None,
    )
    publish_result = None
    if publish:
        try:
            publish_result = _publish(topic, message)
        except Exception as pub_exc:
            logger.warning("[%s] MQ publish failed: %s", service_name, pub_exc)
            publish_result = {"status": "error", "error": str(pub_exc)}
        if isinstance(mailbox_result, dict) and mailbox_result.get("success"):
            mailbox_result = {**mailbox_result, "publish_result": publish_result}

    result = service_result(
        service_name,
        topic=topic,
        action_path=action_path,
        response_meta=meta,
        data_preview=_truncate(captured, max_chars=500),
        record_count=(
            captured.get("record_count") if isinstance(captured, dict) else None
        ),
        publish_result=publish_result,
        mailbox_result=mailbox_result,
    )
    if hasattr(request, "method"):
        maybe_save_callback(request, instruction_row, result)
    return result


class CaptureGetResponse(AtomicServiceBase):
    """
    Capture data returned by a GET (Instruction: direction=RES, requestmethod=GET).

    Passthrough wiring: orchestration_hook sets request._upstream_response
    before calling execute_and_save(request, instruction_row).
    """
    atomic_apps = ()
    atomic_category = "capture"

    @staticmethod
    def get_parameters(parameters, key="CaptureGetResponse"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        return _capture_response_side(
            request=request,
            instruction_row=instruction_row,
            service_name="CaptureGetResponse",
            capture_label="get_response",
            method_expected="GET",
            allow_navigate_fallback=True,
        )


class CapturePostResponse(AtomicServiceBase):
    """
    Capture data returned by a POST (Instruction: direction=RES, requestmethod=POST).

    Use this for SPA list loads such as Odoo
    ``POST /web/dataset/call_kw/<model>/web_search_read`` — the response JSON
    already contains ``result.records`` (the rows about to render).
    """
    atomic_apps = ()
    atomic_category = "capture"

    @staticmethod
    def get_parameters(parameters, key="CapturePostResponse"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        return _capture_response_side(
            request=request,
            instruction_row=instruction_row,
            service_name="CapturePostResponse",
            capture_label="post_response",
            method_expected="POST",
            allow_navigate_fallback=False,
        )


class CapturePostRequest(AtomicServiceBase):
    """
    Capture data on a POST as it goes upstream
    (Instruction: direction=REQ, requestmethod=POST).
    """
    atomic_apps = ()
    atomic_category = "capture"

    @staticmethod
    def get_parameters(parameters, key="CapturePostRequest"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        method = (getattr(request, "method", None) or "").upper()
        if method != "POST":
            return service_result(
                "CapturePostRequest",
                status="skipped",
                reason="not_post",
                method=method or "missing",
            )

        cfg = instruction_config(instruction_row)
        max_chars = int(cfg.get("max_chars", _MAX_CAPTURE_CHARS))
        publish = cfg.get("publish", True)

        data, meta = _extract_post_body(request)
        if data is None:
            return service_result(
                "CapturePostRequest",
                status="skipped",
                reason="no_post_body",
                body_meta=meta,
            )

        captured = _truncate(data, max_chars=max_chars)
        action_path = _action_path(request, instruction_row)
        topic = topic_from_request(request, action_path=action_path, direction="REQ")

        message = {
            "capture": "post_request",
            "topic": topic,
            "action_path": action_path,
            "method": "POST",
            "direction": "REQ",
            "request_meta": meta,
            "data": captured,
            "username": _username_from_request(request) or "anonymous",
            "instruction_id": getattr(instruction_row, "id", None),
            "eventKey": getattr(instruction_row, "eventKey", None),
        }

        mailbox_result = _enroll_capture_mailbox(
            request, instruction_row, topic, message, publish_result=None,
        )
        publish_result = None
        if publish:
            try:
                publish_result = _publish(topic, message)
            except Exception as pub_exc:
                logger.warning("[CapturePostRequest] MQ publish failed: %s", pub_exc)
                publish_result = {"status": "error", "error": str(pub_exc)}

        result = service_result(
            "CapturePostRequest",
            topic=topic,
            action_path=action_path,
            request_meta=meta,
            data_preview=_truncate(captured, max_chars=500),
            publish_result=publish_result,
            mailbox_result=mailbox_result,
        )
        maybe_save_callback(request, instruction_row, result)
        return result
