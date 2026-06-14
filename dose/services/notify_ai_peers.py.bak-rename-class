"""
NotifyAIPeersService — broadcast orchestration context to Mattermost AI peers.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    filter_parameters,
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
)

logger = logging.getLogger(__name__)


class NotifyAIPeersService(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='NotifyAIPeersService'):
        return filter_parameters(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        from dose.mattermost_bot.bot import PEERS, _active_peers, _post_as_peer

        cfg = instruction_config(instruction_row)
        channel_id = cfg.get('channel_id') or cfg.get('mattermost_channel_id')
        if not channel_id:
            return service_result('NotifyAIPeersService', status='error', error='missing_channel_id')

        snap = request_snapshot(request)
        message = cfg.get('message') or (
            f"**Orchestration event** — `{snap.get('path')}`\n"
            f"Tenant: {snap.get('tenant') or '—'}\n"
            f"User: {snap.get('user') or '—'}\n"
            f"Instruction: {getattr(instruction_row, 'description', '') or '—'}"
        )
        root_id = cfg.get('root_id') or ''

        peers_cfg = cfg.get('peers') or cfg.get('peer_list')
        if peers_cfg == '@anyone' or peers_cfg == 'anyone':
            target_peers = _active_peers()
        elif isinstance(peers_cfg, list) and peers_cfg:
            target_peers = [p.lower().lstrip('@') for p in peers_cfg]
        else:
            target_peers = _active_peers()

        posted = []
        errors = []
        for peer_key in target_peers:
            if peer_key not in PEERS:
                errors.append({'peer': peer_key, 'error': 'unknown_peer'})
                continue
            try:
                _post_as_peer(peer_key, channel_id, message, root_id)
                posted.append(peer_key)
            except Exception as exc:
                logger.warning('[NotifyAIPeers] post failed for %s: %s', peer_key, exc)
                errors.append({'peer': peer_key, 'error': str(exc)})

        status = 'success' if posted else 'error'
        result = service_result(
            'NotifyAIPeersService',
            status=status,
            channel_id=channel_id,
            posted=posted,
            errors=errors or None,
        )
        maybe_save_callback(request, instruction_row, result)
        return result
