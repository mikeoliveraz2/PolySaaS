"""
HubSpot API wrapper — per-tenant OAuth tokens via hubspot-api-client.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone

from dose.services.hubspot_oauth import (
    get_tenant_hubspot_app,
    persist_tokens_on_tenant_app,
    refresh_access_token,
)

logger = logging.getLogger(__name__)


class HubspotApiError(Exception):
    pass


class HubspotNotConnected(HubspotApiError):
    pass


class HubspotApiService:
    def __init__(self, tenant, tenant_app=None):
        self.tenant = tenant
        self.tenant_app = tenant_app or get_tenant_hubspot_app(tenant)
        if not self.tenant_app:
            raise HubspotNotConnected('HubSpot is not enabled for this tenant')

    @classmethod
    def for_tenant(cls, tenant) -> 'HubspotApiService':
        return cls(tenant)

    def _extra(self) -> Dict[str, Any]:
        cfg = self.tenant_app.extra_config
        return cfg if isinstance(cfg, dict) else {}

    def _token_expired(self) -> bool:
        raw = self._extra().get('hs_token_expires_at') or ''
        if not raw:
            return False
        try:
            from django.utils.dateparse import parse_datetime
            exp = parse_datetime(raw)
            if not exp:
                return False
            if timezone.is_naive(exp):
                exp = timezone.make_aware(exp, timezone.utc)
            return timezone.now() >= exp - timedelta(minutes=2)
        except Exception:
            return False

    def _refresh_if_needed(self) -> str:
        extra = self._extra()
        token = extra.get('hs_access_token') or ''
        refresh = extra.get('hs_refresh_token') or ''
        if not token:
            raise HubspotNotConnected('Connect HubSpot OAuth first')
        if not self._token_expired():
            return token
        if not refresh:
            return token
        result = refresh_access_token(refresh)
        if not result.get('ok'):
            raise HubspotApiError(result.get('error') or 'token refresh failed')
        persist_tokens_on_tenant_app(self.tenant_app, result)
        self.tenant_app.refresh_from_db()
        return self._extra().get('hs_access_token') or token

    def client(self):
        try:
            from hubspot import HubSpot
        except ImportError as exc:
            raise HubspotApiError('hubspot-api-client is not installed') from exc
        token = self._refresh_if_needed()
        return HubSpot(access_token=token)

    def _props_list(self, records, props: List[str]) -> List[Dict[str, Any]]:
        rows = []
        for rec in records or []:
            data = {'id': getattr(rec, 'id', None)}
            p = getattr(rec, 'properties', None) or {}
            for key in props:
                data[key] = p.get(key)
            rows.append(data)
        return rows

    def list_contacts(self, *, limit: int = 10) -> List[Dict[str, Any]]:
        props = ['firstname', 'lastname', 'email', 'phone', 'company']
        api = self.client().crm.contacts.basic_api
        page = api.get_page(limit=limit, properties=props)
        return self._props_list(page.results, props)

    def create_contact(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a CRM contact. Requires contacts.write (Private App or OAuth)."""
        props = {k: v for k, v in (properties or {}).items() if v not in (None, "")}
        if not props:
            raise HubspotApiError("create_contact requires at least one property")
        try:
            from hubspot.crm.contacts import SimplePublicObjectInputForCreate
        except ImportError:
            from hubspot.crm.contacts import SimplePublicObjectInput as SimplePublicObjectInputForCreate
        api = self.client().crm.contacts.basic_api
        try:
            created = api.create(
                simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                    properties=props
                )
            )
        except TypeError:
            created = api.create(
                simple_public_object_input=SimplePublicObjectInputForCreate(properties=props)
            )
        except Exception as exc:
            raise HubspotApiError(f"create_contact failed: {exc}") from exc
        return {
            "id": getattr(created, "id", None),
            "properties": getattr(created, "properties", None) or props,
        }

    def create_deal(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a CRM deal. Requires deals.write (Private App or OAuth)."""
        props = {k: v for k, v in (properties or {}).items() if v not in (None, "")}
        if not props.get("dealname"):
            raise HubspotApiError("create_deal requires dealname")
        try:
            from hubspot.crm.deals import SimplePublicObjectInputForCreate
        except ImportError:
            from hubspot.crm.deals import SimplePublicObjectInput as SimplePublicObjectInputForCreate
        api = self.client().crm.deals.basic_api
        try:
            created = api.create(
                simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                    properties=props
                )
            )
        except TypeError:
            created = api.create(
                simple_public_object_input=SimplePublicObjectInputForCreate(properties=props)
            )
        except Exception as exc:
            raise HubspotApiError(f"create_deal failed: {exc}") from exc
        return {
            "id": getattr(created, "id", None),
            "properties": getattr(created, "properties", None) or props,
        }

    def list_companies(self, *, limit: int = 10) -> List[Dict[str, Any]]:
        props = ['name', 'domain', 'phone', 'city', 'industry']
        page = self.client().crm.companies.basic_api.get_page(limit=limit, properties=props)
        return self._props_list(page.results, props)

    def list_deals(self, *, limit: int = 10) -> List[Dict[str, Any]]:
        props = [
            'dealname',
            'amount',
            'dealstage',
            'closedate',
            'pipeline',
            'description',
            'createdate',
            'hs_lastmodifieddate',
            'dealtype',
        ]
        page = self.client().crm.deals.basic_api.get_page(limit=limit, properties=props)
        return self._props_list(page.results, props)

    def list_tickets(self, *, limit: int = 10) -> List[Dict[str, Any]]:
        props = ['subject', 'content', 'hs_pipeline_stage', 'hs_ticket_priority', 'createdate']
        try:
            page = self.client().crm.tickets.basic_api.get_page(limit=limit, properties=props)
            return self._props_list(page.results, props)
        except Exception as exc:
            logger.warning('[HubSpotAPI] tickets list failed: %s', exc)
            return []

    def list_tasks(self, *, limit: int = 10) -> List[Dict[str, Any]]:
        props = ['hs_task_subject', 'hs_task_status', 'hs_timestamp', 'hs_task_priority']
        try:
            page = self.client().crm.objects.basic_api.get_page(
                object_type='tasks',
                limit=limit,
                properties=props,
            )
            return self._props_list(page.results, props)
        except Exception as exc:
            logger.warning('[HubSpotAPI] tasks list failed: %s', exc)
            return []
