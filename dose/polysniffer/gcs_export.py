"""
Optional GCS export for PolySniffer HAR bundles (GCP migration alignment).
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 — 2026-06-24
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


def export_har_to_gcs(har_data: dict, *, tenant_slug: str, capture_id: int) -> str | None:
    """
    Upload HAR JSON to GCS. Returns gs:// URI or None if skipped/failed.
    Requires POLYSNIFFER_GCS_BUCKET (and default GCP credentials on Cloud Run / GCE).
    """
    bucket_name = os.environ.get('POLYSNIFFER_GCS_BUCKET', '').strip()
    if not bucket_name:
        return None

    object_name = f'{tenant_slug}/{capture_id}/export.har'
    try:
        from google.cloud import storage

        client = storage.Client(project=os.environ.get('GCP_PROJECT_ID') or None)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(
            json.dumps(har_data, indent=2),
            content_type='application/json',
        )
        uri = f'gs://{bucket_name}/{object_name}'
        logger.info('PolySniffer HAR exported to %s', uri)
        return uri
    except Exception as exc:
        logger.warning('PolySniffer GCS export failed: %s', exc)
        return None
