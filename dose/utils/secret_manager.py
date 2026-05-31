"""
GCP Secret Manager utility for PolySaaS.
Uses Application Default Credentials (ADC) - no JSON key file needed.
Run `gcloud auth application-default login` once per machine.
"""
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)

_secret_cache: dict = {}
_client = None
_client_unavailable = False


def _as_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


_CLOUD_RUNTIME = any(
    os.environ.get(name)
    for name in (
        "K_SERVICE",
        "GAE_ENV",
        "FUNCTION_TARGET",
        "CLOUD_RUN_JOB",
        "GOOGLE_CLOUD_PROJECT",
        "GCP_PROJECT",
    )
)

# Defaults:
# - cloud runtime: use Secret Manager
# - local runtime: skip Secret Manager (prevents noisy ADC reauth errors)
# Override with:
#   POLYSAAS_USE_GCP_SECRETS=1  -> force enable
#   POLYSAAS_SKIP_GCP_SECRETS=1 -> force disable
_USE_GCP_SECRETS = _as_bool("POLYSAAS_USE_GCP_SECRETS", default=_CLOUD_RUNTIME)
_SKIP_GCP_SECRETS = _as_bool("POLYSAAS_SKIP_GCP_SECRETS", default=False) or not _USE_GCP_SECRETS


def _get_client():
    global _client, _client_unavailable
    if _client is not None:
        return _client
    if _client_unavailable:
        return None
    if _SKIP_GCP_SECRETS:
        _client_unavailable = True
        logger.debug("Secret Manager disabled for this runtime")
        return None
    try:
        from google.cloud import secretmanager
        _client = secretmanager.SecretManagerServiceClient()
        return _client
    except Exception as e:
        logger.debug("Secret Manager client unavailable: %s", e)
        _client_unavailable = True
        return None


def get_secret(secret_id: str, env_fallback: Optional[str] = None,
               default: Optional[str] = None,
               project_id: Optional[str] = None) -> Optional[str]:
    """
    Fetch a secret from GCP Secret Manager with env var fallback.
    Caches results in-process to avoid repeated API calls.
    """
    project = project_id or os.environ.get('GCP_PROJECT_ID', 'application-integration-4524')
    cache_key = f"{project}/{secret_id}"

    if cache_key in _secret_cache:
        return _secret_cache[cache_key]

    # 1. Check environment variable first if env_fallback is provided
    if env_fallback:
        value = os.environ.get(env_fallback, '').strip()
        if value:
            _secret_cache[cache_key] = value
            return value

    # 2. Fall back to Secret Manager
    client = _get_client()
    if client:
        try:
            name = f"projects/{project}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(
                request={"name": name},
                timeout=3.0,
                retry=None,
            )
            value = response.payload.data.decode("UTF-8").strip()
            _secret_cache[cache_key] = value
            return value
        except Exception as e:
            logger.debug("Secret Manager lookup failed for '%s': %s", secret_id, e)
            global _client_unavailable
            _client_unavailable = True

    return default


def sm(secret_id: str, env_fallback: Optional[str] = None,
       default: Optional[str] = '') -> str:
    """Shorthand for get_secret — returns '' instead of None by default."""
    result = get_secret(secret_id, env_fallback, default)
    return result if result is not None else ''


def clear_cache():
    _secret_cache.clear()
    global _client, _client_unavailable
    _client = None
    _client_unavailable = False
