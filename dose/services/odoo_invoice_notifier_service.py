"""
OdooInvoiceNotifierService — Atomic service that receives an Odoo invoice.created
message (from MQ topic polysaas.odoo.invoice.created) and posts a formatted
notification to a Mattermost channel.

Architecture:
  PolySniffer detects POST /web/dataset/call_kw/account.move/create
  → EndpointDataExtractorService publishes to polysaas.odoo.invoice.created
  → MQRequestController routes to this service via Instruction on /mq/polysaas.odoo.invoice
  → This service posts to Mattermost

Config (from TenantApp.extra_config for mattermost app_name):
  mm_url       — Mattermost base URL
  mm_token     — Bot/admin personal access token
  mm_channel   — channel name or ID to post to (default: 'town-square')
"""
import json
import logging

import requests as http_requests

from dose.services.atomic_service_base import AtomicServiceBase

logger = logging.getLogger(__name__)

_EMOJI_MAP = {
    "created": "🧾",
    "updated": "✏️",
    "paid":    "✅",
    "deleted": "🗑️",
}


class OdooInvoiceNotifierService(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters):
        key = 'OdooInvoiceNotifierService'
        if isinstance(parameters, dict):
            return parameters if parameters.get('MatchingKey') == key else None
        elif isinstance(parameters, list):
            return [
                p for p in parameters
                if (isinstance(p, dict) and p.get('MatchingKey') == key)
                or (hasattr(p, 'matchingKey') and getattr(p, 'matchingKey', None) == key)
            ]
        return None

    @staticmethod
    def execute_and_save(request, instruction_row):
        message_data = getattr(request, 'mq_message_data', None)
        if not message_data:
            body = getattr(request, 'body', None)
            if body:
                if isinstance(body, bytes):
                    body = body.decode('utf-8', errors='replace')
                try:
                    message_data = json.loads(body) if isinstance(body, str) else body
                except (json.JSONDecodeError, TypeError):
                    message_data = {}

        if not message_data:
            logger.warning('[OdooInvoiceNotifier] No message data')
            return {'status': 'error', 'reason': 'no_message_data'}

        normalized = message_data.get('normalized_data', {})
        action = message_data.get('action', 'created')
        raw = message_data.get('raw_data', {})

        ref = normalized.get('reference') or raw.get('name') or 'N/A'
        total = normalized.get('total_amount') or raw.get('amount_total') or '?'
        partner = normalized.get('customer_id') or raw.get('partner_id') or 'Unknown'
        if isinstance(partner, list):
            partner = partner[1] if len(partner) > 1 else str(partner[0])

        emoji = _EMOJI_MAP.get(action, '📄')
        text = (
            f"{emoji} **New Odoo Invoice {action.title()}**\n"
            f"| Field | Value |\n"
            f"|---|---|\n"
            f"| Reference | `{ref}` |\n"
            f"| Customer | {partner} |\n"
            f"| Total | **{total}** |\n"
            f"\n_Detected by PolySaaS Orchestration_ 🔗"
        )

        config = OdooInvoiceNotifierService._load_mm_config(request)
        post_result = OdooInvoiceNotifierService._post_to_mattermost(config, text)

        result = {
            'status': 'sent' if post_result.get('ok') else 'failed',
            'channel': config.get('mm_channel'),
            'mm_result': post_result,
            'invoice_ref': ref,
            'invoice_total': total,
        }

        try:
            from dose.models import DoseMessage
            user = getattr(request, 'user', None)
            if user and getattr(user, 'is_authenticated', False):
                DoseMessage.objects.create(
                    user=user,
                    message=f"Invoice {ref} → Mattermost notification sent",
                    level='success',
                )
        except Exception as exc:
            logger.warning('[OdooInvoiceNotifier] DoseMessage failed: %s', exc)

        logger.info('[OdooInvoiceNotifier] Result: %s', result)
        return result

    @staticmethod
    def _load_mm_config(request):
        config = {
            'mm_url': 'https://polysaas-mattermost.onrender.com',
            'mm_token': '',
            'mm_channel': 'town-square',
        }
        try:
            from dose.models import TenantApp
            tenant = getattr(request, 'tenant', None)
            manager = getattr(TenantApp, 'public_bundles', TenantApp.objects)
            ta = manager.filter(
                app_name='mattermost', status='active',
            )
            if tenant:
                ta = ta.filter(tenant=tenant)
            ta = ta.first()
            if ta and isinstance(ta.extra_config, dict):
                cfg = ta.extra_config
                if cfg.get('mm_url'):
                    config['mm_url'] = cfg['mm_url'].rstrip('/')
                elif cfg.get('mm_base_url'):
                    config['mm_url'] = cfg['mm_base_url'].rstrip('/')
                if cfg.get('mm_token'):
                    config['mm_token'] = cfg['mm_token']
                elif cfg.get('mattermost_token'):
                    config['mm_token'] = cfg['mattermost_token']
                if cfg.get('mm_channel'):
                    config['mm_channel'] = cfg['mm_channel']
        except Exception as exc:
            logger.warning('[OdooInvoiceNotifier] Could not load MM config: %s', exc)
        return config

    @staticmethod
    def _post_to_mattermost(config, text):
        mm_url = config.get('mm_url', '')
        token = config.get('mm_token', '')
        channel = config.get('mm_channel', 'town-square')

        if not mm_url or not token:
            logger.warning('[OdooInvoiceNotifier] Missing mm_url or mm_token — skipping post')
            return {'ok': False, 'reason': 'missing_config', 'mm_url': mm_url}

        try:
            resp = http_requests.post(
                f'{mm_url}/api/v4/posts',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                json={'channel_id': channel, 'message': text},
                timeout=15,
            )
            if resp.status_code == 201:
                data = resp.json()
                logger.info('[OdooInvoiceNotifier] Posted to channel %s (post_id=%s)', channel, data.get('id'))
                return {'ok': True, 'post_id': data.get('id')}
            else:
                logger.warning('[OdooInvoiceNotifier] MM post failed: %s %s', resp.status_code, resp.text[:200])
                return {'ok': False, 'status_code': resp.status_code, 'error': resp.text[:200]}
        except Exception as exc:
            logger.error('[OdooInvoiceNotifier] HTTP error: %s', exc)
            return {'ok': False, 'error': str(exc)}
