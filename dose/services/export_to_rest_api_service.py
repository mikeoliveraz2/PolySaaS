"""
ExportToRESTAPIService — POST/PUT/PATCH data to any external REST endpoint.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit PENDING
import json
import logging

import requests

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    filter_parameters,
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
)

logger = logging.getLogger(__name__)


class ExportToRESTAPIService(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='ExportToRESTAPIService'):
        return filter_parameters(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        url = cfg.get('url') or cfg.get('endpoint')
        if not url:
            return service_result('ExportToRESTAPIService', status='error', error='missing_url')

        method = (cfg.get('method') or 'POST').upper()
        headers = dict(cfg.get('headers') or {})
        timeout = int(cfg.get('timeout', 30))

        body = cfg.get('body')
        if body is None:
            body = request_snapshot(request)
        if cfg.get('wrap_request', False) and isinstance(body, dict):
            body = {'orchestration': body, 'request': request_snapshot(request)}

        try:
            resp = requests.request(
                method,
                url,
                headers=headers,
                json=body if isinstance(body, (dict, list)) else None,
                data=None if isinstance(body, (dict, list)) else body,
                timeout=timeout,
            )
            text_preview = (resp.text or '')[:1000]
            try:
                response_json = resp.json()
            except Exception:
                response_json = None

            result = service_result(
                'ExportToRESTAPIService',
                url=url,
                http_status=resp.status_code,
                response_preview=text_preview,
                response_json=response_json,
            )
            if resp.status_code >= 400:
                result['status'] = 'error'
        except Exception as exc:
            logger.error('[ExportToRESTAPI] request failed: %s', exc)
            result = service_result('ExportToRESTAPIService', status='error', url=url, error=str(exc))

        maybe_save_callback(request, instruction_row, result)
        return result
