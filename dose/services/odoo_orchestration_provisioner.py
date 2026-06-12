# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Demo Tenant Odoo invoicing orchestration — 2026-06-12

"""
Provision Odoo Invoicing orchestration Instructions when a tenant subscribes to Odoo.

Creates tenant-scoped Instructions so the green orchestration bar matches on
Invoicing navigation and invoice list API calls — no manual "+ Insert Instruction" step.
"""
from __future__ import annotations

import logging
import xmlrpc.client
from typing import Any, Dict, Optional

from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)

# Shared polysaas-odoo2 default (BINGO Odoo invoicing menu_id).
DEFAULT_INVOICING_MENU_ID = 116

INVOICING_MENU_XML_IDS = (
    'account.menu_finance',
    'account.menu_accounting',
    'account.menu_board_journal_1',
    'account.menu_action_move_out_invoice_type',
)


def _odoo_xmlrpc_config() -> Dict[str, str]:
    return {
        'url': getattr(settings, 'ODOO_SHARED_URL', 'https://polysaas-odoo2.onrender.com').rstrip('/'),
        'db': getattr(settings, 'ODOO_SHARED_DB', 'polysaas_odoo'),
        'admin_login': getattr(settings, 'ODOO_XMLRPC_ADMIN_LOGIN', 'odooAdmin'),
        'admin_password': getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!'),
    }


def discover_odoo_invoicing_menu_id() -> Optional[int]:
    """Resolve Invoicing/Accounting menu id from shared Odoo via XML-RPC."""
    config = _odoo_xmlrpc_config()
    try:
        common = xmlrpc.client.ServerProxy(
            f"{config['url']}/xmlrpc/2/common", allow_none=True,
        )
        uid = common.authenticate(
            config['db'], config['admin_login'], config['admin_password'], {},
        )
        if not uid:
            logger.warning('[OdooOrchProvision] XML-RPC auth failed — using default menu_id')
            return None
        models = xmlrpc.client.ServerProxy(
            f"{config['url']}/xmlrpc/2/object", allow_none=True,
        )
        db, pw = config['db'], config['admin_password']
        for xml_id in INVOICING_MENU_XML_IDS:
            try:
                module, name = xml_id.split('.', 1)
                rows = models.execute_kw(
                    db, uid, pw, 'ir.model.data', 'search_read',
                    [[['module', '=', module], ['name', '=', name]]],
                    {'fields': ['res_id'], 'limit': 1},
                )
                if rows and rows[0].get('res_id'):
                    menu_id = int(rows[0]['res_id'])
                    logger.info('[OdooOrchProvision] menu_id=%s from xml_id %s', menu_id, xml_id)
                    return menu_id
            except Exception as exc:
                logger.debug('[OdooOrchProvision] xml_id %s lookup failed: %s', xml_id, exc)
        rows = models.execute_kw(
            db, uid, pw, 'ir.ui.menu', 'search_read',
            [[['name', 'ilike', 'Invoicing']]],
            {'fields': ['id'], 'limit': 1},
        )
        if rows:
            menu_id = int(rows[0]['id'])
            logger.info('[OdooOrchProvision] menu_id=%s from menu name search', menu_id)
            return menu_id
    except Exception as exc:
        logger.warning('[OdooOrchProvision] menu discovery failed: %s', exc)
    return None


def _upsert_instruction(tenant, *, requestpath, match_type, direction, requestmethod,
                        executescript, event_key, description, match_extra=None,
                        save_callbackdata=True):
    from dose.models import Instruction

    defaults = {
        'tenant': tenant,
        'match_type': match_type,
        'match_extra': match_extra or {},
        'executescript': executescript,
        'eventKey': event_key,
        'description': description,
        'save_callbackdata': save_callbackdata,
        'appusername': 'demo',
        'urllist': '',
    }
    obj, created = Instruction.objects.update_or_create(
        tenant=tenant,
        requestpath=requestpath,
        direction=direction,
        requestmethod=requestmethod,
        defaults=defaults,
    )
    action = 'created' if created else 'updated'
    logger.info(
        '[OdooOrchProvision] %s instruction id=%s path=%r dir=%s script=%s',
        action, obj.pk, requestpath, direction, executescript,
    )
    return obj, created


def provision_odoo_invoicing_orchestration(tenant, *, menu_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Create/update Invoicing orchestration Instructions in the tenant schema.

    Called after successful Odoo user provisioning during subscribe.
    """
    if not tenant or not getattr(tenant, 'schema_name', None):
        return {'success': False, 'error': 'no tenant'}

    schema = tenant.schema_name
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}", public')

    if menu_id is None:
        menu_id = discover_odoo_invoicing_menu_id() or DEFAULT_INVOICING_MENU_ID

    # Store menu_id on TenantApp for support/debug (public bundle row).
    try:
        from dose.models import TenantApp
        ta = TenantApp.public_bundles.filter(tenant=tenant, app_name='odoo').first()
        if ta:
            extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
            extra['odoo_invoicing_menu_id'] = menu_id
            ta.extra_config = extra
            ta.save(update_fields=['extra_config'])
    except Exception as exc:
        logger.warning('[OdooOrchProvision] could not store menu_id on TenantApp: %s', exc)

    created_ids = []

    # 1) Green bar / SPA navigation — matches /odoo/accounting (with or without /menu_id suffix).
    nav_path = f'/odoo/accounting/{menu_id}' if menu_id else '/odoo/accounting'
    obj, _ = _upsert_instruction(
        tenant,
        requestpath=nav_path,
        match_type='path',
        direction='REQ',
        requestmethod='GET',
        executescript='HelloWorld',
        event_key='odoo_invoicing_viewed',
        description='User viewed Invoicing in Odoo (auto-provisioned at subscribe)',
        match_extra={},
    )
    created_ids.append(obj.pk)

    # 2) Broader path fallback for Odoo 18 routes without menu suffix in the bar.
    obj2, _ = _upsert_instruction(
        tenant,
        requestpath='/odoo/accounting',
        match_type='path',
        direction='REQ',
        requestmethod='GET',
        executescript='HelloWorld',
        event_key='odoo_invoicing_viewed',
        description='User viewed Odoo Accounting/Invoicing (path fallback)',
        match_extra={},
    )
    created_ids.append(obj2.pk)

    # 3) Invoice list data load through passthrough (POST web_search_read).
    obj3, _ = _upsert_instruction(
        tenant,
        requestpath='account.move/web_search_read',
        match_type='contains',
        direction='REQ',
        requestmethod='POST',
        executescript='OdooInvoiceNotifierService',
        event_key='odoo_invoicing_viewed',
        description='Odoo invoice list loaded via passthrough API (auto-provisioned)',
        match_extra={},
    )
    created_ids.append(obj3.pk)

    logger.info(
        '[OdooOrchProvision] Done for %s (%s) menu_id=%s instruction_ids=%s',
        tenant.name, schema, menu_id, created_ids,
    )
    return {
        'success': True,
        'menu_id': menu_id,
        'instruction_ids': created_ids,
        'schema': schema,
    }
