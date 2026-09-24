"""New Vendor Assist atomic: branded page + criteria capture + demo shortlist.

Triggered by tenant-schema Instructions matching GET/POST /odoo/vendors/new.
The Odoo passthrough handler must not hardcode that path; instruction matching does.
Slice 3 shortlist is curated/demo directory ranked by the same LLM router as
invoice refine — not live web search.
"""
from __future__ import annotations

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
CRITERIA_SESSION_KEY = "odoo_vendor_assist_criteria"
CRITERIA_CAPTURE_STEP = "capture_criteria"
SHORTLIST_SOURCE_LABEL = "Demo directory"
# Visible on GET HTML so a screenshot proves which Assist template is live.
ASSIST_BUILD = "bake-table-20260924"

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
    """Build the New Vendor Assist page and record in-page steps (criteria, shortlist)."""

    atomic_apps = ("odoo",)
    atomic_category = "ui"
    returns_passthrough_page = True

    @staticmethod
    def get_parameters(parameters, key="OdooVendorAssist"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
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


def _is_criteria_capture_request(request) -> bool:
    method = (getattr(request, "method", "GET") or "GET").upper()
    if method != "POST":
        return False
    if "/dose/api/orchestration-navigate" in (getattr(request, "path_info", "") or ""):
        payload = _request_payload(request)
        step = str(payload.get("step") or "").strip()
        return step == CRITERIA_CAPTURE_STEP
    return True


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
        demo_rows = _always_demo_directory_rows(criteria)
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
    vendors = _always_demo_directory_rows(criteria, vendors)
    if len(vendors) < 3:
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
        "source": SHORTLIST_SOURCE_LABEL,
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


def suggest_vendors(criteria: dict) -> tuple[list, bool]:
    """Rank the curated demo directory locally first; optional LLM refine.

    LLM is optional rank only, never a gate. Local rows always come from
    DEMO_VENDOR_DIRECTORY (3–6). llm_ranked is True only when the router
    returns a usable ranking within a short timeout.
    """
    catalog = [dict(row) for row in DEMO_VENDOR_DIRECTORY]
    local_rows = _always_demo_directory_rows(criteria)
    ranked = _llm_rank_directory(criteria, catalog)
    if ranked:
        return _always_demo_directory_rows(criteria, ranked), True
    return local_rows, False


def _llm_rank_directory(criteria: dict, catalog: list) -> list:
    """Ask the standard router to pick 3–6 catalog ids. Never live search."""
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
    slim = [
        {
            "id": row.get("id"),
            "name": row.get("name"),
            "region": row.get("region"),
            "product_line": row.get("product_line"),
            "price_band": row.get("price_band"),
        }
        for row in catalog
    ]
    prompt = (
        "Rank this curated demo vendor directory for the operator criteria. "
        "Do not invent vendors or search the web. Return JSON only: "
        '{"ids": ["id1", "id2"]} with 3 to 6 ids from the catalog, best first.\n'
        f"Criteria: {json.dumps(criteria)}\n"
        f"Catalog: {json.dumps(slim)}"
    )
    try:
        out = complete_chat(
            plan,
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You rank a closed demo directory for PolySaaS New Vendor Assist. "
                "Output JSON with an ids array. No markdown."
            ),
            max_tokens=400,
            timeout=4,
        )
    except Exception as exc:
        logger.warning("[OdooVendorAssist] complete_chat failed: %s", exc)
        return []
    text = (out or "").strip()
    if text.startswith("[llm_router]"):
        return []
    ids = _parse_ranked_ids(text)
    by_id = {str(row.get("id")): row for row in catalog}
    picked = [by_id[i] for i in ids if i in by_id]
    if len(picked) < 3:
        return []
    return picked[:6]


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
