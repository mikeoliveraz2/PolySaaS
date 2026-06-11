"""
AddToMLDatasetService — append conversation/context rows to a JSONL training dataset.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import json
import logging
import os
from pathlib import Path

from django.conf import settings

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    filter_parameters,
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
    tenant_from_request,
)

logger = logging.getLogger(__name__)


class AddToMLDatasetService(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='AddToMLDatasetService'):
        return filter_parameters(parameters, key)

    @staticmethod
    def _dataset_dir():
        base = getattr(settings, 'ML_DATASET_DIR', None) or os.path.join(
            getattr(settings, 'BASE_DIR', '.'), 'data', 'ml_datasets'
        )
        path = Path(base)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        dataset_key = cfg.get('dataset_key') or cfg.get('dataset') or 'default'
        tenant = tenant_from_request(request)
        schema = getattr(tenant, 'schema_name', 'public') if tenant else 'public'

        record = cfg.get('record') or {}
        if not isinstance(record, dict):
            record = {'value': record}
        record.setdefault('request', request_snapshot(request))
        if instruction_row:
            record.setdefault('instruction_id', instruction_row.id)
            record.setdefault('event_key', getattr(instruction_row, 'eventKey', None))

        filename = cfg.get('filename') or f'{schema}_{dataset_key}.jsonl'
        filepath = AddToMLDatasetService._dataset_dir() / filename

        try:
            with open(filepath, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, default=str) + '\n')
            result = service_result(
                'AddToMLDatasetService',
                dataset_key=dataset_key,
                filepath=str(filepath),
                bytes_appended=len(json.dumps(record, default=str)),
            )
        except Exception as exc:
            logger.error('[AddToMLDataset] append failed: %s', exc)
            result = service_result('AddToMLDatasetService', status='error', error=str(exc))

        maybe_save_callback(request, instruction_row, result)
        return result
