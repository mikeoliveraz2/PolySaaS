"""Create or update an Odoo res.partner from a normalized payload.

Instruction selector: atomic_apps = ("odoo",), category write.
Find-or-create by email, then name. Shared RPC lives in odoo_rpc.py.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    instruction_config,
    maybe_save_callback,
    service_result,
)
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.odoo_rpc import (
    OdooRpcClient,
    OdooRpcError,
    load_odoo_rpc_config,
    public_config,
)

logger = logging.getLogger(__name__)

_PARTNER_KEYS = ("name", "email", "phone", "street", "city", "zip", "is_company")


class OdooCreatePartner(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "write"

    @staticmethod
    def get_parameters(parameters, key="OdooCreatePartner"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        payload = _extract_partner_payload(request, instruction_row)
        name = (payload.get("name") or "").strip()
        if not name:
            result = service_result(
                "OdooCreatePartner",
                status="error",
                error="missing_name",
            )
            maybe_save_callback(request, instruction_row, result, description="OdooCreatePartner missing name")
            return result

        vals = _partner_vals(payload)
        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        pub = public_config(config)

        try:
            client = OdooRpcClient.from_config(config)
            client.authenticate()
            partner_id, created = _find_or_create_partner(client, vals)
        except OdooRpcError as exc:
            logger.error("[OdooCreatePartner] %s: %s", exc.status, exc)
            result = service_result(
                "OdooCreatePartner",
                status="error",
                error=exc.status,
                detail=str(exc),
                odoo=pub,
            )
            maybe_save_callback(request, instruction_row, result, description="OdooCreatePartner RPC error")
            return result
        except Exception as exc:
            logger.error("[OdooCreatePartner] unexpected error: %s", exc)
            result = service_result(
                "OdooCreatePartner",
                status="error",
                error="error",
                detail=str(exc),
                odoo=pub,
            )
            maybe_save_callback(request, instruction_row, result, description="OdooCreatePartner error")
            return result

        result = service_result(
            "OdooCreatePartner",
            status="success",
            partner_id=partner_id,
            created=created,
            name=vals.get("name"),
            email=vals.get("email") or "",
            odoo=pub,
            transport=client.transport,
        )
        maybe_save_callback(
            request,
            instruction_row,
            result,
            description=f"Odoo partner {'created' if created else 'updated'}: {vals.get('name')}",
        )
        logger.info(
            "[OdooCreatePartner] %s partner_id=%s name=%s transport=%s",
            "created" if created else "updated",
            partner_id,
            vals.get("name"),
            client.transport,
        )
        return result


def _extract_partner_payload(request, instruction_row) -> dict:
    """mq_message_data, then JSON body, then Instruction.parameters_json."""
    data = getattr(request, "mq_message_data", None) if request is not None else None
    if isinstance(data, dict) and data:
        nested = data.get("normalized_data")
        if isinstance(nested, dict) and nested:
            return dict(nested)
        # Slack slash commands deliver operator input in `text`. Accept either
        # JSON (`/poly {"name":"Acme","email":"a@b.com"}`) or a plain partner
        # name (`/poly Acme`). This adaptation belongs in the consumer, not the
        # mailbox router or Action Point matcher.
        slash_text = data.get("text")
        if isinstance(slash_text, str) and slash_text.strip():
            text = slash_text.strip()
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                return parsed
            return {"name": text}
        return dict(data)

    body = getattr(request, "body", None) if request is not None else None
    parsed = _parse_json_body(body)
    if parsed:
        nested = parsed.get("normalized_data")
        if isinstance(nested, dict) and nested:
            return dict(nested)
        return parsed

    cfg = instruction_config(instruction_row)
    return {k: cfg[k] for k in _PARTNER_KEYS if k in cfg}


def _parse_json_body(body) -> dict:
    if not body:
        return {}
    if isinstance(body, dict):
        return dict(body)
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if isinstance(body, str) and body.strip():
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _partner_vals(payload: dict) -> dict:
    vals: dict[str, Any] = {
        "name": str(payload.get("name") or "").strip(),
        "is_company": bool(payload.get("is_company", False)),
    }
    for src, dest in (
        ("email", "email"),
        ("phone", "phone"),
        ("street", "street"),
        ("city", "city"),
        ("zip", "zip"),
    ):
        value = payload.get(src)
        if value not in (None, ""):
            vals[dest] = str(value).strip()
    return vals


def _find_or_create_partner(client: OdooRpcClient, vals: dict) -> tuple[int, bool]:
    existing_ids = []
    email = vals.get("email")
    if email:
        existing_ids = client.execute_kw(
            "res.partner", "search", [[["email", "=", email]]], {"limit": 1}
        )
    if not existing_ids and vals.get("name"):
        existing_ids = client.execute_kw(
            "res.partner",
            "search",
            [[["name", "=", vals["name"]]]],
            {"limit": 1},
        )
    if existing_ids:
        partner_id = int(existing_ids[0])
        client.execute_kw("res.partner", "write", [[partner_id], vals])
        return partner_id, False
    new_id = client.execute_kw("res.partner", "create", [vals])
    return int(new_id), True
