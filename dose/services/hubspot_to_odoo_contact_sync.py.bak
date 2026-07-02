"""
HubSpotToOdooContactSync — Atomic service that fires when a new contact is
created in HubSpot via the passthrough and mirrors it as a res.partner record
in Odoo CRM.

Triggered by:  Instruction matching POST /crm/v3/objects/contacts
               (or legacy POST /contacts/v1/contact)
               direction: outbound (request leaving PolySaaS toward HubSpot)

The service reads the contact properties from the intercepted request body,
maps them to Odoo partner fields, and creates/updates via XML-RPC.
Results are saved to CallBackData and logged to the orchestration bar.
"""
from __future__ import annotations

import json
import logging
import xmlrpc.client
from datetime import datetime

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service

logger = logging.getLogger(__name__)

# Odoo XML-RPC defaults — overridden by TenantApp.extra_config or Parameters
_ODOO_DEFAULTS = {
    "url": "http://localhost:8069",
    "db": "odoo",
    "username": "admin",
    "password": "admin",
}


class HubSpotToOdooContactSync(AtomicServiceBase):
    """
    Intercepts a HubSpot contact-create POST and syncs the contact to Odoo as
    a res.partner (contact type, not company).  Idempotent: searches by email
    first; updates if found, creates if not.
    """

    @staticmethod
    def get_parameters(parameters):
        return filter_parameters_for_service(parameters, "HubSpotToOdooContactSync")

    @staticmethod
    def execute_and_save(request, instruction_row):
        timestamp = datetime.now().isoformat()

        # ── 1. Parse the intercepted request body ────────────────────────────
        contact_props = HubSpotToOdooContactSync._extract_contact_props(request)
        if not contact_props:
            logger.warning("[HS→Odoo] No contact properties in request body — skipping")
            return {"status": "skipped", "reason": "no_contact_properties"}

        logger.info(
            "[HS→Odoo] Syncing HubSpot contact: email=%s name=%s",
            contact_props.get("email"),
            contact_props.get("name"),
        )

        # ── 2. Map HubSpot properties → Odoo partner fields ──────────────────
        partner_vals = HubSpotToOdooContactSync._map_with_engine_or_fallback(
            instruction_row, contact_props
        )
        if not partner_vals.get("name"):
            logger.warning("[HS→Odoo] Contact has no usable name — skipping")
            return {"status": "skipped", "reason": "missing_name", "props": contact_props}

        # ── 3. Odoo connection config ─────────────────────────────────────────
        odoo_config = HubSpotToOdooContactSync._get_odoo_config(request)

        # ── 4. Sync to Odoo ───────────────────────────────────────────────────
        odoo_result = HubSpotToOdooContactSync._sync_to_odoo(odoo_config, partner_vals)

        callback_data = {
            "service_name": "HubSpotToOdooContactSync",
            "execution_timestamp": timestamp,
            "source_app": "hubspot",
            "entity": "contact",
            "action": "created",
            "partner_vals": partner_vals,
            "odoo_result": odoo_result,
        }

        # ── 5. Persist to CallBackData ────────────────────────────────────────
        try:
            if instruction_row and getattr(instruction_row, "save_callbackdata", False):
                from dose.models import CallBackData
                from dose.passthrough.orchestration_log import ensure_tenant_search_path

                tenant = getattr(request, "tenant", None)
                if tenant and ensure_tenant_search_path(tenant, "hs_odoo_contact_sync"):
                    CallBackData.objects.create(
                        tenant=tenant,
                        matchingEventKey=getattr(instruction_row, "eventKey", None),
                        description=(
                            f"HubSpot contact → Odoo partner: "
                            f"{partner_vals.get('name', 'N/A')} "
                            f"({odoo_result.get('status', '?')})"
                        ),
                        parameters_json=json.dumps(callback_data),
                        callbackdata=callback_data,
                    )
        except Exception as exc:
            logger.error("[HS→Odoo] Error saving CallBackData: %s", exc)

        # ── 6. Notify user via DoseMessage ────────────────────────────────────
        try:
            from dose.models import DoseMessage

            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                status_text = odoo_result.get("status", "unknown")
                DoseMessage.objects.create(
                    user=user,
                    message=(
                        f"HubSpot contact synced to Odoo: "
                        f"{partner_vals.get('name', 'N/A')} — {status_text}"
                    ),
                    level="success" if status_text in ("created", "updated") else "warning",
                )
        except Exception as exc:
            logger.warning("[HS→Odoo] Could not create DoseMessage: %s", exc)

        return callback_data

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_contact_props(request) -> dict:
        """
        Extract contact properties from a request body.

        Handles all HubSpot payload shapes — both passthrough-intercepted API
        calls and inbound workflow webhook payloads.

        Shape 1 — v3 flat (CRM API and most workflow webhooks):
            {"properties": {"email": "a@b.com", "firstname": "Ann", ...}}

        Shape 2 — v3 nested (older workflow webhooks, properties with history):
            {"properties": {"email": {"value": "a@b.com", "versions": [...]}, ...}}

        Shape 3 — v1 list (legacy CRM API):
            {"properties": [{"property": "email", "value": "a@b.com"}, ...]}

        Shape 4 — flat root (some workflow "Send HTTP request" configs):
            {"email": "a@b.com", "firstname": "Ann", ...}

        Shape 5 — CRM event array (HubSpot webhook subscription API):
            [{"subscriptionType": "contact.creation", "objectId": 123, ...}]
        """
        try:
            body_bytes = getattr(request, "body", None) or b""
            if isinstance(body_bytes, str):
                body_bytes = body_bytes.encode("utf-8")
            data = json.loads(body_bytes.decode("utf-8", errors="replace") or "{}")
        except Exception:
            data = {}

        # Shape 5 — unwrap single-item CRM event array
        if isinstance(data, list):
            data = data[0] if data else {}

        raw_props = data.get("properties")

        # Shape 3 — v1 list
        if isinstance(raw_props, list):
            props: dict = {}
            for item in raw_props:
                key = item.get("property", "")
                val = item.get("value", "")
                if key == "email":
                    props["email"] = val
                elif key == "firstname":
                    props.setdefault("_firstname", val)
                elif key == "lastname":
                    props.setdefault("_lastname", val)
                elif key == "phone":
                    props["phone"] = val
                elif key == "company":
                    props["company"] = val
            fn = props.pop("_firstname", "")
            ln = props.pop("_lastname", "")
            props["name"] = f"{fn} {ln}".strip()
            if not props.get("email") and not props.get("name"):
                return {}
            return props

        # Shape 1 / 2 — properties is a dict (flat or nested {value:...})
        if isinstance(raw_props, dict):
            def _val(v):
                """Unwrap nested {value: ...} objects from older workflow format."""
                return v["value"] if isinstance(v, dict) and "value" in v else v

            raw = {k: _val(v) for k, v in raw_props.items()}

        # Shape 4 — flat root (wrap and treat as v3 flat)
        elif any(k in data for k in ("email", "firstname", "lastname", "phone")):
            raw = data

        else:
            return {}

        props = {}
        props["email"] = raw.get("email", "")
        firstname = raw.get("firstname", "")
        lastname = raw.get("lastname", "")
        props["name"] = f"{firstname} {lastname}".strip() or raw.get("name", "")
        props["phone"] = raw.get("phone", raw.get("mobilephone", ""))
        props["company"] = raw.get("company", "")
        props["jobtitle"] = raw.get("jobtitle", "")
        props["website"] = raw.get("website", "")
        props["address"] = raw.get("address", "")
        props["city"] = raw.get("city", "")
        props["zip"] = raw.get("zip", "")
        props["country"] = raw.get("country", "")

        if not props.get("email") and not props.get("name"):
            return {}
        return props

    @staticmethod
    def _map_with_engine_or_fallback(instruction_row, contact_props: dict) -> dict:
        """Use database Mapping rows first; fall back to hard-coded map."""
        if instruction_row:
            try:
                from dose.services.mapping_engine import (
                    apply_mappings_for_instruction,
                    build_context_from_payload,
                )
                from dose.models import InstructionMapping

                if InstructionMapping.objects.filter(
                    instruction=instruction_row, enabled=True
                ).exists():
                    ctx = build_context_from_payload(contact_props)
                    mapped = apply_mappings_for_instruction(instruction_row, ctx)
                    if mapped and mapped.get("name"):
                        logger.info("[HS\u2192Odoo] Used Mapping engine: %d fields", len(mapped))
                        return mapped
            except Exception as exc:
                logger.warning("[HS→Odoo] Mapping engine error, falling back: %s", exc)

        return HubSpotToOdooContactSync._map_to_odoo_partner(contact_props)

    @staticmethod
    def _map_to_odoo_partner(props: dict) -> dict:
        """Hard-coded fallback: map HubSpot contact properties → Odoo res.partner."""
        partner: dict = {
            "name": props.get("name", props.get("email", "Unknown Contact")),
            "is_company": False,
            "customer_rank": 1,
        }
        for hs_field, odoo_field in (
            ("email", "email"),
            ("phone", "phone"),
            ("address", "street"),
            ("city", "city"),
            ("zip", "zip"),
            ("website", "website"),
            ("jobtitle", "function"),
        ):
            if props.get(hs_field):
                partner[odoo_field] = props[hs_field]
        if props.get("country"):
            partner["_country_name"] = props["country"]
        if props.get("company"):
            partner["_company_name"] = props["company"]
        return partner

    @staticmethod
    def _get_odoo_config(request) -> dict:
        """Load Odoo XML-RPC config from TenantApp.extra_config, PassThroughEndpoint, or defaults."""
        config = dict(_ODOO_DEFAULTS)

        # Try TenantApp.extra_config for Odoo credentials
        try:
            from dose.models import TenantApp

            tenant = getattr(request, "tenant", None)
            if tenant:
                ta = TenantApp.objects.filter(tenant=tenant, app_slug="odoo").first()
                if ta and isinstance(getattr(ta, "extra_config", None), dict):
                    ec = ta.extra_config
                    if ec.get("odoo_url"):
                        config["url"] = ec["odoo_url"].rstrip("/")
                    if ec.get("odoo_db"):
                        config["db"] = ec["odoo_db"]
                    if ec.get("odoo_login"):
                        config["username"] = ec["odoo_login"]
                    if ec.get("odoo_password"):
                        config["password"] = ec["odoo_password"]
        except Exception as exc:
            logger.debug("[HS→Odoo] TenantApp config lookup: %s", exc)

        # Fall back to PassThroughEndpoint if TenantApp didn't fill everything
        if config["url"] == _ODOO_DEFAULTS["url"]:
            try:
                from dose.models.pass_through_endpoint import PassThroughEndpoint

                ep = PassThroughEndpoint.objects.filter(
                    trigger_path="odoo", is_enabled=True
                ).order_by("-id").first()
                if ep:
                    config["url"] = ep.endpoint_url.rstrip("/")
                    if ep.auth_username:
                        config["username"] = ep.auth_username
                    if ep.auth_password:
                        config["password"] = ep.auth_password
            except Exception as exc:
                logger.debug("[HS→Odoo] PassThroughEndpoint lookup: %s", exc)

        return config

    @staticmethod
    def _sync_to_odoo(config: dict, partner_vals: dict) -> dict:
        """Create or update res.partner in Odoo via XML-RPC."""
        url = config["url"]
        db = config["db"]
        username = config["username"]
        password = config["password"]

        try:
            common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid = common.authenticate(db, username, password, {})
            if not uid:
                logger.error("[HS→Odoo] Odoo authentication failed for user %s @ %s", username, url)
                return {"status": "auth_failed", "url": url, "db": db}

            models_proxy = xmlrpc.client.ServerProxy(
                f"{url}/xmlrpc/2/object", allow_none=True
            )

            # Strip internal helper fields before sending to Odoo
            vals = {k: v for k, v in partner_vals.items() if not k.startswith("_")}

            # Resolve country name → country_id
            country_name = partner_vals.get("_country_name")
            if country_name:
                try:
                    country_ids = models_proxy.execute_kw(
                        db, uid, password, "res.country", "search",
                        [[["name", "ilike", country_name]]],
                        {"limit": 1},
                    )
                    if country_ids:
                        vals["country_id"] = country_ids[0]
                except Exception as exc:
                    logger.debug("[HS→Odoo] Country lookup failed: %s", exc)

            # Resolve or create company partner
            company_name = partner_vals.get("_company_name")
            if company_name:
                try:
                    company_ids = models_proxy.execute_kw(
                        db, uid, password, "res.partner", "search",
                        [[["name", "=", company_name], ["is_company", "=", True]]],
                        {"limit": 1},
                    )
                    if company_ids:
                        vals["parent_id"] = company_ids[0]
                    else:
                        new_co = models_proxy.execute_kw(
                            db, uid, password, "res.partner", "create",
                            [{"name": company_name, "is_company": True, "customer_rank": 1}],
                        )
                        vals["parent_id"] = new_co
                except Exception as exc:
                    logger.debug("[HS→Odoo] Company lookup/create failed: %s", exc)

            # Dedup by email first, then name
            existing: list = []
            if vals.get("email"):
                existing = models_proxy.execute_kw(
                    db, uid, password, "res.partner", "search",
                    [[["email", "=", vals["email"]]]],
                )
            if not existing and vals.get("name"):
                existing = models_proxy.execute_kw(
                    db, uid, password, "res.partner", "search",
                    [[["name", "=", vals["name"]], ["is_company", "=", False]]],
                )

            if existing:
                models_proxy.execute_kw(
                    db, uid, password, "res.partner", "write",
                    [existing, vals],
                )
                logger.info(
                    "[HS→Odoo] Updated Odoo partner id=%s: %s",
                    existing[0],
                    vals.get("name"),
                )
                return {"status": "updated", "partner_id": existing[0], "name": vals.get("name")}
            else:
                new_id = models_proxy.execute_kw(
                    db, uid, password, "res.partner", "create", [vals]
                )
                logger.info(
                    "[HS→Odoo] Created Odoo partner id=%s: %s",
                    new_id,
                    vals.get("name"),
                )
                return {"status": "created", "partner_id": new_id, "name": vals.get("name")}

        except ConnectionRefusedError:
            logger.error("[HS→Odoo] Connection refused: %s", url)
            return {"status": "connection_refused", "url": url}
        except Exception as exc:
            logger.error("[HS→Odoo] XML-RPC sync error: %s", exc)
            return {"status": "error", "error": str(exc)}
