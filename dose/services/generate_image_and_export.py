"""
GenerateImageAndExport — generate an image via xAI (or mock) and optional export URL.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import base64
import logging
import os
from pathlib import Path

import requests
from django.conf import settings

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.atomic_service_utils import (
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
)

logger = logging.getLogger(__name__)


class GenerateImageAndExport(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='GenerateImageAndExport'):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def _generate_image(prompt, api_key):
        """Try xAI image API; return (bytes_or_url, provider)."""
        if api_key:
            try:
                resp = requests.post(
                    'https://api.x.ai/v1/images/generations',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={'model': 'grok-2-image', 'prompt': prompt, 'n': 1},
                    timeout=120,
                )
                if resp.status_code < 400:
                    data = resp.json()
                    items = data.get('data') or []
                    if items:
                        item = items[0]
                        if item.get('url'):
                            return item['url'], 'xai_url'
                        b64 = item.get('b64_json')
                        if b64:
                            return base64.b64decode(b64), 'xai_b64'
            except Exception as exc:
                logger.warning('[GenerateImage] xAI failed: %s', exc)
        return None, 'unavailable'

    @staticmethod
    def _save_local(image_data, filename):
        out_dir = Path(getattr(settings, 'GENERATED_MEDIA_DIR', None) or os.path.join(
            getattr(settings, 'BASE_DIR', '.'), 'data', 'generated_images'
        ))
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / filename
        if isinstance(image_data, bytes):
            path.write_bytes(image_data)
            return str(path)
        return image_data

    @staticmethod
    def _export_url(export_url, image_path_or_url, cfg):
        if not export_url:
            return None
        method = (cfg.get('export_method') or 'POST').upper()
        headers = dict(cfg.get('export_headers') or {})
        payload = cfg.get('export_body') or {
            'image_path': image_path_or_url,
            'source': 'GenerateImageAndExport',
        }
        try:
            resp = requests.request(
                method,
                export_url,
                headers=headers,
                json=payload if isinstance(payload, dict) else None,
                timeout=int(cfg.get('export_timeout', 60)),
            )
            return {'http_status': resp.status_code, 'body_preview': (resp.text or '')[:500]}
        except Exception as exc:
            return {'error': str(exc)}

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        snap = request_snapshot(request)
        prompt = cfg.get('prompt') or f"PolySaaS orchestration visual for {snap.get('path', 'workflow')}"
        api_key = cfg.get('api_key') or getattr(settings, 'XAI_API_KEY', '')

        image_data, provider = GenerateImageAndExport._generate_image(prompt, api_key)
        local_path = None
        if image_data:
            if isinstance(image_data, bytes):
                fname = cfg.get('filename') or f"orch_{getattr(instruction_row, 'id', 'new')}.png"
                local_path = GenerateImageAndExport._save_local(image_data, fname)
            else:
                local_path = image_data
        else:
            provider = 'mock'
            fname = cfg.get('filename') or f"orch_{getattr(instruction_row, 'id', 'new')}_placeholder.txt"
            local_path = GenerateImageAndExport._save_local(b'', fname)
            Path(local_path).write_text(f'[mock image] prompt={prompt}\n', encoding='utf-8')

        export_url = cfg.get('export_url') or cfg.get('nextcloud_url')
        export_result = GenerateImageAndExport._export_url(export_url, local_path, cfg)

        result = service_result(
            'GenerateImageAndExport',
            provider=provider,
            prompt=prompt[:500],
            local_path=local_path,
            export=export_result,
        )
        maybe_save_callback(request, instruction_row, result)
        return result
