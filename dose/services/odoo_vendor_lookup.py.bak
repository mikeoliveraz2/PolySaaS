"""New Vendor Assist atomic: branded page + criteria + shortlist + bind + save.

Triggered by tenant-schema Instructions matching GET/POST /odoo/vendors/new.
The Odoo passthrough handler must not hardcode that path; instruction matching does.
Slice 7 shortlist uses the existing LLM router (RoutePlan + complete_chat).
There is no web-search tool on that router; AI suggested rows come from the
LLM. Demo directory remains fallback and padding. Slice 4 binds a selected
row. Slice 5 creates the vendor in Odoo via RPC. Slice 6 publishes Vendors (polysaas.vendor.created)
and Contacts topics. Frozen Slack customer-create is not used.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    maybe_save_callback,
    service_result,
    tenant_from_request,
)
from dose.services.atomic_services_registry import filter_parameters_for_service

logger = logging.getLogger(__name__)

VENDOR_PAGE_TITLE = "New Vendor (PolySaaS Assist)"
VENDOR_PAGE_LOADED_MESSAGE = "Vendor page loaded"
CRITERIA_CAPTURED_MESSAGE = "Criteria captured"
CRITERIA_CAPTURE_FAILED_MESSAGE = "Vendor criteria capture failed"
SHORTLIST_RETURNED_MESSAGE = "Shortlist returned"
SHORTLIST_FAILED_MESSAGE = "Shortlist search failed"
BIND_LOADED_MESSAGE = "Vendor details loaded from selection"
BIND_FAILED_MESSAGE = "Vendor selection bind failed"
VENDOR_CREATED_MESSAGE = "Vendor created"
CONTACT_LINKED_MESSAGE = "Contact linked"
CONTACT_LINK_FAILED_MESSAGE = "Contact link failed — vendor still created"
VENDOR_CREATE_FAILED_MESSAGE = "Vendor create failed"
EVENT_PUBLISHED_MESSAGE = "Event published"
VENDOR_EVENT_PUBLISHED_MESSAGE = "Vendor event published"
CONTACT_EVENT_PUBLISHED_MESSAGE = "Contact event published"
EVENT_PUBLISH_FAILED_MESSAGE = "Event publish failed — vendor saved, retry pending"
CRITERIA_SESSION_KEY = "odoo_vendor_assist_criteria"
VENDOR_PUBLISH_SESSION_KEY = "odoo_vendor_assist_published_event_ids"
CRITERIA_CAPTURE_STEP = "capture_criteria"
BIND_SELECTION_STEP = "bind"
SAVE_VENDOR_STEP = "save"
SHORTLIST_SOURCE_LABEL = "Demo directory"
AI_SOURCE_LABEL = "AI suggested"
LLM_SHORTLIST_TIMEOUT_SECONDS = 8
# Visible on GET HTML so a screenshot proves which Assist template is live.
ASSIST_BUILD = "table-visible-20260924+s4+s5+s6+s7"

# Curated demo rows only. Ranked/filtered; never fetched from the live web.
DEMO_VENDOR_DIRECTORY = (
    {
        "id": "seawrap",
        "name": "SeaWrap Packaging",
        "email": "sales@seawrap.example",
        "phone": "+65 6123 4401",
        "website": "https://seawrap.example",
        "region": "Southeast Asia",
        "product_line": "Packaging film",
        "price_band": "Under $2 per unit",
        "main_contact": {
            "name": "Lina Tan",
            "email": "lina.tan@seawrap.example",
        },
    },
    {
        "id": "mekongfilm",
        "name": "Mekong Film Co",
        "email": "hello@mekongfilm.example",
        "phone": "+84 28 3999 1200",
        "website": "https://mekongfilm.example",
        "region": "Vietnam / Southeast Asia",
        "product_line": "Packaging film",
        "price_band": "Low unit price",
    },
    {
        "id": "aseanpack",
        "name": "ASEAN Pack Supplies",
        "email": "orders@aseanpack.example",
        "phone": "+66 2 555 0199",
        "website": "https://aseanpack.example",
        "region": "Thailand / Southeast Asia",
        "product_line": "Packaging film and pouches",
        "price_band": "Budget to mid",
        "main_contact": {
            "name": "Somsak Prasert",
            "email": "somsak@aseanpack.example",
        },
    },
    {
        "id": "graphitepoint",
        "name": "Graphite Point Stationery",
        "email": "buy@graphitepoint.example",
        "phone": "+60 3 2100 8800",
        "website": "https://graphitepoint.example",
        "region": "Malaysia / Southeast Asia",
        "product_line": "Pencils and writing supplies",
        "price_band": "Under $2 per unit",
        "main_contact": {
            "name": "Mei Chen",
            "email": "mei.chen@graphitepoint.example",
        },
    },
    {
        "id": "pencilworks",
        "name": "PencilWorks Johor",
        "email": "sales@pencilworks.example",
        "phone": "+60 7 331 4400",
        "website": "https://pencilworks.example",
        "region": "Johor / Southeast Asia",
        "product_line": "Pencils",
        "price_band": "Low unit price",
    },
    {
        "id": "nordiccrates",
        "name": "Nordic Timber Crates",
        "email": "export@nordiccrates.example",
        "phone": "+47 21 000 110",
        "website": "https://nordiccrates.example",
        "region": "Northern Europe",
        "product_line": "Wooden shipping crates",
        "price_band": "Premium",
    },
)

DEFAULT_PRODUCT_LINE = "Packaging film"
DEFAULT_REGION = "Southeast Asia"
DEFAULT_PRICE_RANGE = "Under $2 per unit"


class OdooVendorAssist(AtomicServiceBase):
    """Build the New Vendor Assist page and record in-page steps (criteria, shortlist, bind)."""

    atomic_apps = ("odoo",)
    atomic_category = "ui"
    returns_passthrough_page = True

    @staticmethod
    def get_parameters(parameters, key="OdooVendorAssist"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        if _is_bind_selection_request(request):
            return bind_vendor_selection(request, instruction_row)

        if _is_save_vendor_request(request):
            return save_vendor(request, instruction_row)

        if _is_criteria_capture_request(request):
            return capture_vendor_criteria(request, instruction_row)

        # Orchestration bar POST /dose/api/orchestration-navigate/ only needs a match
        # count. Full HTML is served on document GET via instruction_page — rendering
        # admin chrome here was heavy and could surface as gateway 502 on the bar.
        if getattr(request, "_orch_navigate_api", False) or (
            "/dose/api/orchestration-navigate" in (getattr(request, "path_info", "") or "")
        ):
            emit_vendor_page_loaded(request)
            result = service_result(
                "OdooVendorAssist",
                status="success",
                matched_only=True,
                message=VENDOR_PAGE_LOADED_MESSAGE,
            )
            maybe_save_callback(
                request,
                instruction_row,
                {
                    "status": "success",
                    "matched_only": True,
                    "message": VENDOR_PAGE_LOADED_MESSAGE,
                },
                description="New Vendor Assist matched on navigate (page deferred)",
            )
            return result

        emit_vendor_page_loaded(request)
        html = render_vendor_assist_html(request)
        result = service_result(
            "OdooVendorAssist",
            status="success",
            html=html,
            content_type="text/html; charset=utf-8",
            wrap_passthrough=True,
            page_title=VENDOR_PAGE_TITLE,
            message=VENDOR_PAGE_LOADED_MESSAGE,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {
                "status": "success",
                "page_title": VENDOR_PAGE_TITLE,
                "message": VENDOR_PAGE_LOADED_MESSAGE,
            },
            description="New Vendor Assist page served",
        )
        return result


def _request_payload(request) -> dict:
    """Parse JSON body or form POST. Never raises."""
    raw = getattr(request, "body", b"") or b""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = str(raw).strip()
    if text:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    post = getattr(request, "POST", None)
    if post:
        return {key: post.get(key) for key in post}
    return {}


def _is_bind_selection_request(request) -> bool:
    method = (getattr(request, "method", "GET") or "GET").upper()
    if method != "POST":
        return False
    payload = _request_payload(request)
    step = str(payload.get("step") or payload.get("action") or "").strip().lower()
    if payload.get("bind_selection") is True or str(payload.get("bind_selection") or "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True
    return step in (BIND_SELECTION_STEP, "bind_selection")


def _is_save_vendor_request(request) -> bool:
    method = (getattr(request, "method", "GET") or "GET").upper()
    if method != "POST":
        return False
    payload = _request_payload(request)
    step = str(payload.get("step") or payload.get("action") or "").strip().lower()
    if payload.get("save_vendor") is True or str(payload.get("save_vendor") or "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True
    return step in (SAVE_VENDOR_STEP, "save_vendor", "save_to_odoo")


def _is_criteria_capture_request(request) -> bool:
    method = (getattr(request, "method", "GET") or "GET").upper()
    if method != "POST":
        return False
    if _is_bind_selection_request(request):
        return False
    if _is_save_vendor_request(request):
        return False
    if "/dose/api/orchestration-navigate" in (getattr(request, "path_info", "") or ""):
        payload = _request_payload(request)
        step = str(payload.get("step") or "").strip()
        return step == CRITERIA_CAPTURE_STEP
    return True


def _vendor_from_bind_payload(payload: dict) -> dict:
    nested = payload.get("vendor") if isinstance(payload.get("vendor"), dict) else {}
    contact = nested.get("main_contact") if isinstance(nested.get("main_contact"), dict) else {}
    if not contact:
        raw = payload.get("main_contact")
        contact = raw if isinstance(raw, dict) else {}
    name = str(
        payload.get("name") or nested.get("name") or payload.get("vendor_name") or ""
    ).strip()
    email = str(payload.get("email") or nested.get("email") or "").strip()
    phone = str(payload.get("phone") or nested.get("phone") or "").strip()
    website = str(payload.get("website") or nested.get("website") or "").strip()
    contact_name = str(
        payload.get("contact_name")
        or payload.get("main_contact_name")
        or contact.get("name")
        or ""
    ).strip()
    contact_email = str(
        payload.get("contact_email")
        or payload.get("main_contact_email")
        or contact.get("email")
        or ""
    ).strip()
    vendor = {
        "name": name,
        "email": email,
        "phone": phone,
        "website": website,
    }
    if contact_name or contact_email:
        vendor["main_contact"] = {"name": contact_name, "email": contact_email}
    return vendor


def bind_vendor_selection(request, instruction_row):
    """Slice 4: record the selected demo row and toast. No Odoo RPC."""
    try:
        payload = _request_payload(request)
        vendor = _vendor_from_bind_payload(payload)
        if not vendor.get("name"):
            emit_vendor_step_message(request, BIND_FAILED_MESSAGE, level="error")
            public = {
                "ok": False,
                "status": "error",
                "message": BIND_FAILED_MESSAGE,
                "vendor": vendor,
                "bind_ok": False,
            }
            result = service_result(
                "OdooVendorAssist",
                json_response=True,
                wrap_passthrough=False,
                json=dict(public),
                **public,
            )
            maybe_save_callback(
                request,
                instruction_row,
                {"status": "error", "message": BIND_FAILED_MESSAGE},
                description="New Vendor Assist bind failed (missing name)",
            )
            return result

        emit_vendor_step_message(request, BIND_LOADED_MESSAGE, level="success")
        public = {
            "ok": True,
            "status": "success",
            "message": BIND_LOADED_MESSAGE,
            "vendor": vendor,
            "bind_ok": True,
        }
        result = service_result(
            "OdooVendorAssist",
            json_response=True,
            wrap_passthrough=False,
            json=dict(public),
            **public,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {"status": "success", "message": BIND_LOADED_MESSAGE, "vendor": vendor},
            description="New Vendor Assist selection bound",
        )
        return result
    except Exception:
        logger.exception("[OdooVendorAssist] bind selection failed")
        emit_vendor_step_message(request, BIND_FAILED_MESSAGE, level="error")
        public = {
            "ok": False,
            "status": "error",
            "message": BIND_FAILED_MESSAGE,
            "bind_ok": False,
        }
        result = service_result(
            "OdooVendorAssist",
            json_response=True,
            wrap_passthrough=False,
            json=dict(public),
            **public,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {"status": "error", "message": BIND_FAILED_MESSAGE},
            description="New Vendor Assist bind failed",
        )
        return result


def _vendor_form_href(request, partner_id: int) -> str:
    """Passthrough path to the created res.partner form (not the Assist page)."""
    path = getattr(request, "path", None) or getattr(request, "path_info", "") or ""
    if "/odoo/vendors/new" in path:
        base = path.split("/odoo/vendors/new")[0]
    else:
        base = path.rsplit("/", 1)[0] if "/" in path else ""
    return f"{base}/odoo/res.partner/{int(partner_id)}"


def save_vendor(request, instruction_row):
    """Slice 5–6: create company (+ optional contact) in Odoo, then enroll capture.v1."""
    payload = _request_payload(request)
    vendor = _vendor_from_bind_payload(payload)
    if not vendor.get("name"):
        emit_vendor_step_message(request, VENDOR_CREATE_FAILED_MESSAGE, level="error")
        public = {
            "ok": False,
            "status": "error",
            "message": VENDOR_CREATE_FAILED_MESSAGE,
            "vendor_created": False,
            "contact_linked": False,
            "partner_id": None,
        }
        result = service_result(
            "OdooVendorAssist",
            json_response=True,
            wrap_passthrough=False,
            json=dict(public),
            **public,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {"status": "error", "message": VENDOR_CREATE_FAILED_MESSAGE},
            description="New Vendor Assist save failed (empty name)",
        )
        return result

    try:
        from dose.services.odoo_rpc import OdooRpcClient, load_odoo_rpc_config

        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        client = OdooRpcClient.from_config(config)
        client.authenticate()
        partner_id = create_odoo_vendor_company(client, vendor)
    except Exception:
        logger.exception("[OdooVendorAssist] vendor company create failed")
        emit_vendor_step_message(request, VENDOR_CREATE_FAILED_MESSAGE, level="error")
        public = {
            "ok": False,
            "status": "error",
            "message": VENDOR_CREATE_FAILED_MESSAGE,
            "vendor_created": False,
            "contact_linked": False,
            "partner_id": None,
        }
        result = service_result(
            "OdooVendorAssist",
            json_response=True,
            wrap_passthrough=False,
            json=dict(public),
            **public,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {"status": "error", "message": VENDOR_CREATE_FAILED_MESSAGE},
            description="New Vendor Assist save failed (company)",
        )
        return result

    emit_vendor_step_message(request, VENDOR_CREATED_MESSAGE, level="success")
    form_href = _vendor_form_href(request, partner_id)
    contact = vendor.get("main_contact") if isinstance(vendor.get("main_contact"), dict) else {}
    contact_name = str(contact.get("name") or "").strip()
    contact_email = str(contact.get("email") or "").strip()
    contact_phone = str(contact.get("phone") or payload.get("contact_phone") or "").strip()
    want_contact = bool(contact_name or contact_email or contact_phone)

    contact_id = None
    contact_ok = False
    contact_message = ""
    if want_contact:
        try:
            contact_id = link_odoo_vendor_contact(
                client,
                partner_id,
                {
                    "name": contact_name or contact_email,
                    "email": contact_email,
                    "phone": contact_phone,
                },
            )
            contact_ok = True
            contact_message = CONTACT_LINKED_MESSAGE
            emit_vendor_step_message(request, CONTACT_LINKED_MESSAGE, level="success")
        except Exception:
            logger.exception("[OdooVendorAssist] vendor contact link failed")
            contact_message = CONTACT_LINK_FAILED_MESSAGE
            emit_vendor_step_message(request, CONTACT_LINK_FAILED_MESSAGE, level="error")

    publish = publish_saved_vendor_capture(
        request,
        vendor=vendor,
        partner_id=partner_id,
        contact_id=contact_id,
        contact_ok=contact_ok,
        payload=payload,
    )
    vendor_pub = publish.get("vendor") or {}
    contact_pub = publish.get("contact") or {}
    vendor_ok = bool(vendor_pub.get("success"))
    vendor_deduped = bool(vendor_pub.get("deduped"))
    contact_ok_pub = bool(contact_pub.get("success"))
    contact_deduped = bool(contact_pub.get("deduped"))
    contact_attempted_pub = bool(publish.get("contact_attempted"))

    if vendor_ok and not vendor_deduped:
        emit_vendor_step_message(request, VENDOR_EVENT_PUBLISHED_MESSAGE, level="success")
        vendor_publish_message = VENDOR_EVENT_PUBLISHED_MESSAGE
    elif vendor_ok and vendor_deduped:
        vendor_publish_message = VENDOR_EVENT_PUBLISHED_MESSAGE
    else:
        emit_vendor_step_message(request, EVENT_PUBLISH_FAILED_MESSAGE, level="error")
        vendor_publish_message = EVENT_PUBLISH_FAILED_MESSAGE

    contact_publish_message = ""
    if contact_attempted_pub:
        if contact_ok_pub and not contact_deduped:
            emit_vendor_step_message(request, CONTACT_EVENT_PUBLISHED_MESSAGE, level="success")
            contact_publish_message = CONTACT_EVENT_PUBLISHED_MESSAGE
        elif contact_ok_pub and contact_deduped:
            contact_publish_message = CONTACT_EVENT_PUBLISHED_MESSAGE

    messages = [VENDOR_CREATED_MESSAGE]
    if want_contact:
        messages.append(contact_message)
    if not vendor_deduped:
        messages.append(vendor_publish_message)
    if contact_publish_message and not contact_deduped:
        messages.append(contact_publish_message)
    public = {
        "ok": True,
        "status": "success",
        "message": VENDOR_CREATED_MESSAGE,
        "messages": messages,
        "vendor_created": True,
        "contact_linked": contact_ok,
        "contact_attempted": want_contact,
        "contact_message": contact_message,
        "partner_id": partner_id,
        "contact_id": contact_id,
        "odoo_form_href": form_href,
        "vendor": vendor,
        "event_published": vendor_ok and not vendor_deduped,
        "event_publish_skipped": vendor_deduped,
        "event_publish_message": vendor_publish_message,
        "contact_event_published": contact_ok_pub and not contact_deduped,
        "contact_event_message": contact_publish_message,
        "event_id": vendor_pub.get("event_id"),
        "mailbox_id": vendor_pub.get("mailbox_id"),
        "event_key": vendor_pub.get("event_key"),
        "vendor_topic": vendor_pub.get("topic"),
        "contact_topic": contact_pub.get("topic"),
        "capture_kind": "polysaas.capture.v1",
    }
    result = service_result(
        "OdooVendorAssist",
        json_response=True,
        wrap_passthrough=False,
        json=dict(public),
        **public,
    )
    maybe_save_callback(
        request,
        instruction_row,
        {
            "status": "success",
            "message": VENDOR_CREATED_MESSAGE,
            "partner_id": partner_id,
            "contact_id": contact_id,
            "contact_linked": contact_ok,
            "event_published": vendor_ok,
            "event_id": vendor_pub.get("event_id"),
        },
        description="New Vendor Assist saved vendor to Odoo",
    )
    return result


def _vendor_capture_event_id(tenant, partner_id, email: str) -> str:
    schema = getattr(tenant, "schema_name", None) or "unknown"
    raw = f"{schema}|odoo.vendor|{int(partner_id)}|{(email or '').strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _contact_capture_event_id(tenant, contact_id, email: str) -> str:
    schema = getattr(tenant, "schema_name", None) or "unknown"
    cid = int(contact_id) if contact_id is not None else 0
    raw = f"{schema}|odoo.contact|{cid}|{(email or '').strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _session_has_published_event(request, event_id: str) -> bool:
    session = getattr(request, "session", None)
    if session is None or not event_id:
        return False
    try:
        seen = session.get(VENDOR_PUBLISH_SESSION_KEY) or []
        return isinstance(seen, list) and event_id in seen
    except Exception:
        return False


def _mark_published_event(request, event_id: str) -> None:
    session = getattr(request, "session", None)
    if session is None or not event_id:
        return
    try:
        seen = session.get(VENDOR_PUBLISH_SESSION_KEY) or []
        if not isinstance(seen, list):
            seen = []
        if event_id not in seen:
            seen.append(event_id)
            session[VENDOR_PUBLISH_SESSION_KEY] = seen[-50:]
            if hasattr(session, "modified"):
                session.modified = True
    except Exception:
        return


def publish_saved_vendor_capture(
    request, *, vendor, partner_id, contact_id, payload, contact_ok=False
):
    """Publish vendor to Vendors topic; enroll contact on Contacts if saved. Fail-soft."""
    from dose.services.contact_capture import enroll_contact_capture, normalize_contact
    from dose.services.vendor_capture import (
        VENDOR_ACTION_PATH,
        VENDOR_EVENT_KEY,
        enroll_vendor_capture,
    )

    tenant = tenant_from_request(request)
    email = str(vendor.get("email") or "").strip()
    vendor_event_id = _vendor_capture_event_id(tenant, partner_id, email)

    session_criteria = _criteria_from_session(request)
    criteria = {
        "product_line": str(
            payload.get("product_line") or session_criteria.get("product_line") or ""
        ).strip(),
        "region": str(
            payload.get("region")
            or vendor.get("region")
            or session_criteria.get("region")
            or ""
        ).strip(),
        "price_range": str(
            payload.get("price_range")
            or payload.get("price")
            or vendor.get("price_band")
            or session_criteria.get("price_range")
            or ""
        ).strip(),
    }
    actor = "system"
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "username", None):
        actor = str(user.username)

    vendor_record = {
        "odoo_vendor_id": partner_id,
        "odoo_contact_id": contact_id,
        "name": str(vendor.get("name") or "").strip(),
        "vendor_name": str(vendor.get("name") or "").strip(),
        "email": email,
        "region": criteria["region"],
        "criteria": criteria,
        "product_line": criteria["product_line"],
        "price_range": criteria["price_range"],
    }

    vendor_enroll = {
        "success": True,
        "deduped": True,
        "event_id": vendor_event_id,
        "event_key": VENDOR_EVENT_KEY,
    }
    if not _session_has_published_event(request, vendor_event_id):
        try:
            vendor_enroll = enroll_vendor_capture(
                tenant=tenant,
                record=vendor_record,
                actor=actor,
                action_path=VENDOR_ACTION_PATH,
                event_key=VENDOR_EVENT_KEY,
                method="POST",
                event_id=vendor_event_id,
            )
        except Exception as exc:
            logger.warning("[OdooVendorAssist] vendor enroll failed: %s", exc, exc_info=True)
            vendor_enroll = {
                "success": False,
                "error": str(exc),
                "event_id": vendor_event_id,
                "event_key": VENDOR_EVENT_KEY,
            }
        vendor_enroll = vendor_enroll if isinstance(vendor_enroll, dict) else {}
        vendor_enroll.setdefault("event_key", VENDOR_EVENT_KEY)
        vendor_enroll.setdefault("event_id", vendor_event_id)
        if vendor_enroll.get("success"):
            _mark_published_event(request, vendor_event_id)

    contact_enroll = {}
    contact_attempted = bool(contact_ok and contact_id)
    if contact_attempted:
        contact = vendor.get("main_contact") if isinstance(vendor.get("main_contact"), dict) else {}
        contact_email = str(contact.get("email") or "").strip()
        contact_event_id = _contact_capture_event_id(tenant, contact_id, contact_email)
        if _session_has_published_event(request, contact_event_id):
            contact_enroll = {
                "success": True,
                "deduped": True,
                "event_id": contact_event_id,
                "event_key": "odoo.capture_contacts",
            }
        else:
            record = normalize_contact(
                source_app="odoo",
                external_id=contact_id,
                name=str(contact.get("name") or "").strip(),
                email=contact_email,
                phone=str(contact.get("phone") or "").strip(),
                company=str(vendor.get("name") or "").strip(),
                raw_record={
                    "odoo_vendor_id": partner_id,
                    "odoo_contact_id": contact_id,
                },
            )
            try:
                contact_enroll = enroll_contact_capture(
                    tenant=tenant,
                    source_app="odoo",
                    records=[record],
                    actor=actor,
                    action_path="odoo/contacts",
                    event_key="odoo.capture_contacts",
                    method="POST",
                    event_id=contact_event_id,
                )
            except Exception as exc:
                logger.warning(
                    "[OdooVendorAssist] contact enroll failed: %s", exc, exc_info=True
                )
                contact_enroll = {"success": False, "error": str(exc)}
            contact_enroll = contact_enroll if isinstance(contact_enroll, dict) else {}
            if contact_enroll.get("success"):
                _mark_published_event(request, contact_event_id)

    return {
        "vendor": vendor_enroll,
        "contact": contact_enroll,
        "contact_attempted": contact_attempted,
        "success": bool(vendor_enroll.get("success")),
        "deduped": bool(vendor_enroll.get("deduped")),
        "event_id": vendor_enroll.get("event_id"),
        "mailbox_id": vendor_enroll.get("mailbox_id"),
        "event_key": vendor_enroll.get("event_key"),
        "topic": vendor_enroll.get("topic"),
    }


def create_odoo_vendor_company(client, vendor: dict) -> int:
    """Create res.partner company with supplier_rank > 0. Vendor-specific; not customer-create."""
    vals = {
        "name": str(vendor.get("name") or "").strip(),
        "is_company": True,
        "supplier_rank": 1,
        "customer_rank": 0,
    }
    if vendor.get("email"):
        vals["email"] = str(vendor["email"]).strip()
    if vendor.get("phone"):
        vals["phone"] = str(vendor["phone"]).strip()
    if vendor.get("website"):
        vals["website"] = str(vendor["website"]).strip()
    return int(client.execute_kw("res.partner", "create", [vals]))


def link_odoo_vendor_contact(client, parent_id: int, contact: dict) -> int:
    """Create or update a child contact under the vendor. Light email idempotency."""
    email = str(contact.get("email") or "").strip()
    name = str(contact.get("name") or email or "Contact").strip()
    phone = str(contact.get("phone") or "").strip()
    existing_id = None
    if email:
        found = client.execute_kw(
            "res.partner",
            "search",
            [[["parent_id", "=", int(parent_id)], ["email", "=", email]]],
            {"limit": 1},
        )
        if found:
            existing_id = int(found[0])
    vals = {
        "name": name,
        "is_company": False,
        "parent_id": int(parent_id),
        "customer_rank": 0,
        "supplier_rank": 0,
    }
    if email:
        vals["email"] = email
    if phone:
        vals["phone"] = phone
    if existing_id:
        client.execute_kw("res.partner", "write", [[existing_id], vals])
        return existing_id
    return int(client.execute_kw("res.partner", "create", [vals]))


def capture_vendor_criteria(request, instruction_row):
    """Slice 2: record product line / region / price range and toast."""
    payload = _request_payload(request)
    product_line = str(payload.get("product_line") or payload.get("product") or "").strip()
    region = str(payload.get("region") or "").strip()
    price_range = str(
        payload.get("price_range") or payload.get("price") or ""
    ).strip()
    criteria = {
        "product_line": product_line,
        "region": region,
        "price_range": price_range,
    }
    missing = [name for name, val in criteria.items() if not val]
    if missing:
        detail = f"{CRITERIA_CAPTURE_FAILED_MESSAGE}: missing {', '.join(missing)}"
        emit_vendor_step_message(request, detail, level="error")
        emit_vendor_step_message(request, SHORTLIST_FAILED_MESSAGE, level="error")
        demo_rows = _label_rows(_always_demo_directory_rows(criteria), SHORTLIST_SOURCE_LABEL)
        public = {
            "ok": False,
            "status": "error",
            "message": detail,
            "criteria": criteria,
            "vendors": list(demo_rows),
            "suggested_vendors": list(demo_rows),
            "source": SHORTLIST_SOURCE_LABEL,
            "shortlist_status": SHORTLIST_FAILED_MESSAGE,
            "shortlist_message": SHORTLIST_FAILED_MESSAGE,
            "shortlist_ok": False,
        }
        result = service_result(
            "OdooVendorAssist",
            json_response=True,
            wrap_passthrough=False,
            json=dict(public),
            **public,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {"status": "error", "message": detail, "criteria": criteria},
            description="New Vendor Assist criteria capture failed",
        )
        return result

    session = getattr(request, "session", None)
    if session is not None:
        try:
            session[CRITERIA_SESSION_KEY] = criteria
            if hasattr(session, "modified"):
                session.modified = True
        except Exception:
            logger.warning("[OdooVendorAssist] could not store criteria in session")

    emit_vendor_step_message(request, CRITERIA_CAPTURED_MESSAGE, level="success")
    try:
        vendors, shortlist_ok = suggest_vendors(criteria)
    except Exception:
        logger.exception("[OdooVendorAssist] shortlist failed")
        vendors, shortlist_ok = [], False
    if not vendors:
        vendors = _label_rows(_always_demo_directory_rows(criteria), SHORTLIST_SOURCE_LABEL)
        shortlist_ok = False
    if shortlist_ok and vendors:
        shortlist_message = SHORTLIST_RETURNED_MESSAGE
        emit_vendor_step_message(request, shortlist_message, level="success")
    else:
        shortlist_message = SHORTLIST_FAILED_MESSAGE
        emit_vendor_step_message(request, shortlist_message, level="error")
    public = {
        "ok": True,
        "status": "success",
        "message": CRITERIA_CAPTURED_MESSAGE,
        "criteria": criteria,
        "vendors": list(vendors),
        "suggested_vendors": list(vendors),
        "source": _shortlist_source_summary(vendors),
        "shortlist_status": shortlist_message,
        "shortlist_message": shortlist_message,
        "shortlist_ok": shortlist_ok and bool(vendors),
    }
    result = service_result(
        "OdooVendorAssist",
        json_response=True,
        wrap_passthrough=False,
        json=dict(public),
        **public,
    )
    maybe_save_callback(
        request,
        instruction_row,
        {
            "status": "success",
            "message": CRITERIA_CAPTURED_MESSAGE,
            "shortlist_message": shortlist_message,
            "criteria": criteria,
            "vendor_count": len(vendors),
        },
        description="New Vendor Assist criteria captured and shortlist",
    )
    return result


def emit_vendor_page_loaded(request) -> None:
    """Create a tenant-schema DoseMessage so the passthrough green bar can show it."""
    emit_vendor_step_message(request, VENDOR_PAGE_LOADED_MESSAGE, level="success")


def emit_vendor_step_message(request, message: str, level: str = "info") -> None:
    """Each atomic step reports success or failure via DoseMessage (tenant schema)."""
    from dose.messaging import create_dose_message

    tenant = tenant_from_request(request)
    if not tenant:
        logger.warning("[OdooVendorAssist] no tenant; skip DoseMessage")
        return
    user = getattr(request, "user", None)
    create_dose_message(
        tenant=tenant,
        user=user,
        message=message,
        level=level,
    )


def _criteria_from_session(request) -> dict:
    session = getattr(request, "session", None) or {}
    stored = session.get(CRITERIA_SESSION_KEY) if hasattr(session, "get") else None
    if isinstance(stored, dict):
        return {
            "product_line": stored.get("product_line") or DEFAULT_PRODUCT_LINE,
            "region": stored.get("region") or DEFAULT_REGION,
            "price_range": stored.get("price_range") or DEFAULT_PRICE_RANGE,
        }
    return {
        "product_line": DEFAULT_PRODUCT_LINE,
        "region": DEFAULT_REGION,
        "price_range": DEFAULT_PRICE_RANGE,
    }


def _always_demo_directory_rows(criteria: dict, vendors=None) -> list:
    """LLM never gates the table. Always 3–6 curated DEMO_VENDOR_DIRECTORY rows."""
    catalog = [dict(row) for row in DEMO_VENDOR_DIRECTORY]
    rows = [row for row in (vendors or []) if isinstance(row, dict) and row.get("name")]
    if len(rows) >= 3:
        return rows[:6]
    ranked = _deterministic_rank_directory(criteria, catalog)
    if len(ranked) >= 3:
        return ranked[:6]
    return catalog[:6]


def _label_rows(rows: list, source: str) -> list:
    labeled = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item["source"] = source
        labeled.append(item)
    return labeled


def _shortlist_source_summary(vendors: list) -> str:
    labels = []
    for row in vendors or []:
        label = str((row or {}).get("source") or "").strip()
        if label and label not in labels:
            labels.append(label)
    if AI_SOURCE_LABEL in labels and SHORTLIST_SOURCE_LABEL in labels:
        return f"{AI_SOURCE_LABEL} + {SHORTLIST_SOURCE_LABEL}"
    if AI_SOURCE_LABEL in labels:
        return AI_SOURCE_LABEL
    return SHORTLIST_SOURCE_LABEL


def _merge_ai_and_demo(criteria: dict, ai_rows: list) -> list:
    """Keep AI rows first; pad with Demo directory when the LLM returns few."""
    merged = _label_rows(ai_rows, AI_SOURCE_LABEL)
    seen = {str(row.get("name") or "").strip().lower() for row in merged if row.get("name")}
    if len(merged) >= 3:
        return merged[:6]
    for demo in _always_demo_directory_rows(criteria):
        name = str(demo.get("name") or "").strip().lower()
        if not name or name in seen:
            continue
        item = dict(demo)
        item["source"] = SHORTLIST_SOURCE_LABEL
        merged.append(item)
        seen.add(name)
        if len(merged) >= 6:
            break
    if len(merged) < 3:
        merged.extend(
            _label_rows(_always_demo_directory_rows(criteria), SHORTLIST_SOURCE_LABEL)
        )
    return merged[:6]


def suggest_vendors(criteria: dict) -> tuple[list, bool]:
    """LLM shortlist via RoutePlan/complete_chat; Demo directory fail-soft.

    No web-search helper exists on the router. Timeout is short. Empty or
    failed LLM still returns curated Demo directory rows.
    """
    ai_rows = _llm_suggest_vendors(criteria)
    if ai_rows:
        return _merge_ai_and_demo(criteria, ai_rows), True
    demo = _label_rows(_always_demo_directory_rows(criteria), SHORTLIST_SOURCE_LABEL)
    return demo, False


def _llm_suggest_vendors(criteria: dict) -> list:
    """Ask the standard router for a vendor JSON list. No paid search API."""
    try:
        from django.conf import settings

        from llm_router.providers import complete_chat
        from llm_router.router import RoutePlan
    except Exception:
        logger.warning("[OdooVendorAssist] LLM router import failed")
        return []

    plan = RoutePlan(
        provider=getattr(settings, "LLM_ROUTER_STANDARD_PROVIDER", "anthropic"),
        model=getattr(settings, "LLM_ROUTER_STANDARD_MODEL", "claude-sonnet-4-6"),
        task_bucket="standard",
        user_tier="standard",
        reason="odoo_vendor_assist_shortlist",
    )
    prompt = (
        "Suggest 3 to 6 supplier companies matching the operator criteria "
        "(product line, region, price). Use general knowledge only. "
        "Return JSON only: "
        '{"vendors":[{"name":"...","email":"...","phone":"...","website":"...",'
        '"region":"...","product_line":"...","price_band":"...",'
        '"main_contact":{"name":"...","email":"..."}}]}. No markdown.\n'
        f"Criteria: {json.dumps(criteria)}"
    )
    try:
        out = complete_chat(
            plan,
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You suggest a short vendor list for PolySaaS New Vendor Assist. "
                "Output JSON with a vendors array. No markdown."
            ),
            max_tokens=800,
            timeout=LLM_SHORTLIST_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning("[OdooVendorAssist] complete_chat failed: %s", exc)
        return []
    text = (out or "").strip()
    if text.startswith("[llm_router]"):
        return []
    vendors = _parse_suggested_vendor_rows(text)
    return vendors[:6]


def _parse_ranked_ids(text: str) -> list:
    blob = text.strip()
    match = re.search(r"\{.*\}", blob, re.DOTALL)
    if match:
        blob = match.group(0)
    try:
        data = json.loads(blob)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    if isinstance(data, dict):
        ids = data.get("ids") or data.get("vendors") or []
    elif isinstance(data, list):
        ids = data
    else:
        return []
    out = []
    for item in ids:
        if isinstance(item, str):
            out.append(item.strip())
        elif isinstance(item, dict) and item.get("id"):
            out.append(str(item.get("id")).strip())
    return [i for i in out if i]


def _parse_suggested_vendor_rows(text: str) -> list:
    blob = (text or "").strip()
    match = re.search(r"\{.*\}", blob, re.DOTALL)
    if match:
        blob = match.group(0)
    try:
        data = json.loads(blob)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    raw = []
    if isinstance(data, dict):
        raw = data.get("vendors") or data.get("suggested_vendors") or []
    elif isinstance(data, list):
        raw = data
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        contact = item.get("main_contact") if isinstance(item.get("main_contact"), dict) else {}
        rows.append(
            {
                "id": str(item.get("id") or re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")[:40],
                "name": name,
                "email": str(item.get("email") or "").strip(),
                "phone": str(item.get("phone") or "").strip(),
                "website": str(item.get("website") or "").strip(),
                "region": str(item.get("region") or "").strip(),
                "product_line": str(item.get("product_line") or "").strip(),
                "price_band": str(item.get("price_band") or item.get("price_range") or "").strip(),
                "main_contact": {
                    "name": str(contact.get("name") or item.get("contact_name") or "").strip(),
                    "email": str(contact.get("email") or item.get("contact_email") or "").strip(),
                },
                "source": AI_SOURCE_LABEL,
            }
        )
    return rows


def _deterministic_rank_directory(criteria: dict, catalog: list) -> list:
    """Keyword score so the demo still shows rows when the LLM is down."""
    product = str((criteria or {}).get("product_line") or "").lower()
    region = str((criteria or {}).get("region") or "").lower()
    price = str((criteria or {}).get("price_range") or "").lower()
    scored = []
    for row in catalog:
        hay = " ".join(
            str(row.get(k) or "")
            for k in ("name", "region", "product_line", "price_band")
        ).lower()
        score = 0
        for token in re.findall(r"[a-z0-9]+", product):
            if len(token) > 2 and token in hay:
                score += 3
        for token in re.findall(r"[a-z0-9]+", region):
            if len(token) > 2 and token in hay:
                score += 2
        if any(w in price for w in ("low", "under", "budget", "cheap")) and any(
            w in hay for w in ("low", "under", "budget")
        ):
            score += 2
        if "pencil" in product and "pencil" in hay:
            score += 6
        if "film" in product and "film" in hay:
            score += 6
        if "asia" in region and "asia" in hay:
            score += 2
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    ranked = [row for score, row in scored if score > 0]
    if len(ranked) < 3:
        ranked = [row for _, row in scored]
    return ranked[:6]


def render_vendor_assist_html(request) -> str:
    """Branded shell HTML with criteria fields (search/save still stubs)."""
    from django.template.loader import render_to_string

    ctx = {"page_title": VENDOR_PAGE_TITLE, "assist_build": ASSIST_BUILD}
    ctx.update(_criteria_from_session(request))
    return render_to_string(
        "admin/odoo_vendor_lookup.html",
        ctx,
        request=request,
    )
