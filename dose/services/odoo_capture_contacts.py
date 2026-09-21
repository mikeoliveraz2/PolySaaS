"""
OdooCaptureContacts — GET-style list of Odoo res.partner contacts into
Captured Topics (mailbox) for Consume → ContactHistory.

Endpoint bookmark: Capture contacts (direct_event odoo.capture_contacts).
"""
from __future__ import annotations

import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.contact_capture import (
    MAX_CONTACT_PAGES,
    PAGE_SIZE,
    enroll_contact_capture,
    normalize_contact,
)
from dose.services.odoo_rpc import (
    OdooRpcClient,
    OdooRpcError,
    load_odoo_rpc_config,
    public_config,
)

logger = logging.getLogger(__name__)

_CONTACT_FIELDS = (
    "id",
    "name",
    "email",
    "phone",
    "parent_id",
    "customer_rank",
    "active",
)


class OdooCaptureContacts(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="OdooCaptureContacts"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row=None):
        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        pub = public_config(config)
        max_rows = PAGE_SIZE * MAX_CONTACT_PAGES
        try:
            mq = getattr(request, "mq_message_data", None) if request is not None else None
            if isinstance(mq, dict) and mq.get("limit") not in (None, ""):
                max_rows = max(1, min(int(mq.get("limit")), PAGE_SIZE * MAX_CONTACT_PAGES))
        except (TypeError, ValueError):
            pass

        try:
            client = OdooRpcClient.from_config(config)
            client.authenticate()
            raw_rows = []
            offset = 0
            while offset < max_rows:
                batch_limit = min(PAGE_SIZE, max_rows - offset)
                batch = client.execute_kw(
                    "res.partner",
                    "search_read",
                    [[["customer_rank", ">", 0]]],
                    {
                        "fields": list(_CONTACT_FIELDS),
                        "limit": batch_limit,
                        "offset": offset,
                        "order": "name asc, id desc",
                    },
                )
                if not batch:
                    break
                raw_rows.extend(batch)
                if len(batch) < batch_limit:
                    break
                offset += len(batch)
        except OdooRpcError as exc:
            logger.error("[OdooCaptureContacts] %s: %s", exc.status, exc)
            return service_result(
                "OdooCaptureContacts",
                status="error",
                error=exc.status,
                detail=str(exc),
                odoo=pub,
            )
        except Exception as exc:
            logger.error("[OdooCaptureContacts] unexpected: %s", exc)
            return service_result(
                "OdooCaptureContacts",
                status="error",
                error="error",
                detail=str(exc),
                odoo=pub,
            )

        contacts = []
        for row in raw_rows:
            parent = row.get("parent_id")
            if isinstance(parent, (list, tuple)) and parent:
                parent_name = parent[1] if len(parent) > 1 else str(parent[0])
            else:
                parent_name = parent or ""
            contacts.append(
                normalize_contact(
                    source_app="odoo",
                    external_id=row.get("id"),
                    name=row.get("name") or "",
                    email=row.get("email") or "",
                    phone=row.get("phone") or "",
                    company=parent_name or "",
                    username="",
                    active=bool(row.get("active", True)),
                    raw_record=row,
                )
            )

        actor = "system"
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "username", None):
            actor = str(user.username)

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            try:
                from dose.utils import get_current_tenant

                tenant = get_current_tenant(request)
            except Exception:
                tenant = None

        enroll = enroll_contact_capture(
            tenant=tenant,
            source_app="odoo",
            records=contacts,
            actor=actor,
            action_path="odoo/contacts",
            event_key="odoo.capture_contacts",
            method="GET",
        )

        result = service_result(
            "OdooCaptureContacts",
            status="success" if enroll.get("success") else "error",
            count=len(contacts),
            contacts=contacts,
            odoo=pub,
            mailbox=enroll,
            topic=enroll.get("topic"),
            mailbox_id=enroll.get("mailbox_id"),
        )
        if not enroll.get("success"):
            result["error"] = enroll.get("error") or "mailbox_enroll_failed"
            result["detail"] = result["error"]
        return result
