"""
WriteToBigQuery — insert orchestration rows into BigQuery (ADC or service account).
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import json
import logging
import os
import uuid
from datetime import datetime, timezone

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


class WriteToBigQuery(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='WriteToBigQuery'):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        snap = request_snapshot(request)

        project_id = (
            cfg.get('project_id')
            or os.environ.get('GCP_PROJECT_ID')
            or os.environ.get('BIGQUERY_PROJECT_ID')
            or getattr(settings, 'GCP_PROJECT_ID', 'application-integration-4524')
        )
        dataset_id = cfg.get('dataset_id') or os.environ.get('BIGQUERY_DATASET_ID', 'polysaas')
        table_id = cfg.get('table_id') or 'orchestration_events'

        event_type = cfg.get('event_type') or getattr(instruction_row, 'eventKey', None) or 'orchestration'
        source_system = cfg.get('source_system') or 'polysaas'
        event_data = cfg.get('event_data') or {
            'request': snap,
            'instruction_id': getattr(instruction_row, 'id', None),
            'instruction_path': getattr(instruction_row, 'requestpath', None),
        }

        row = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'source_system': source_system,
            'contact_id': snap.get('user_email') or None,
            'event_data': json.dumps(event_data, default=str),
            'status': 'ok',
            'error_message': None,
        }

        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id)
            table_ref = f'{project_id}.{dataset_id}.{table_id}'
            errors = client.insert_rows_json(table_ref, [row])
            if errors:
                result = service_result(
                    'WriteToBigQuery',
                    status='error',
                    table=table_ref,
                    errors=errors,
                )
            else:
                result = service_result(
                    'WriteToBigQuery',
                    table=table_ref,
                    event_id=row['event_id'],
                )
        except ImportError:
            result = service_result(
                'WriteToBigQuery',
                status='skipped',
                reason='google-cloud-bigquery not installed',
                row_preview=row,
            )
        except Exception as exc:
            logger.warning('[WriteToBigQuery] insert failed: %s', exc)
            result = service_result('WriteToBigQuery', status='error', error=str(exc), row_preview=row)

        maybe_save_callback(request, instruction_row, result)
        return result
