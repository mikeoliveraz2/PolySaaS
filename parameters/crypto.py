"""
Fernet encryption for Parameter.encrypted_payload (at-rest secrets in DB).

Key resolution:
1. settings.PARAMETER_FERNET_KEY — preferred in production (output of Fernet.generate_key() as ASCII).
2. HKDF(settings.SECRET_KEY) — fallback so local dev works without an extra env var;
   rotating SECRET_KEY invalidates existing ciphertext.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger(__name__)

_SALT = b"PolySaaS-parameters-fernet-v1"


def _derive_fernet_key_from_secret_key(secret_key: str) -> bytes:
    raw = (secret_key or "").encode("utf-8")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        info=b"",
    )
    return base64.urlsafe_b64encode(hkdf.derive(raw[:256] or b"fallback"))


def get_parameter_fernet() -> Optional[Fernet]:
    from django.conf import settings

    explicit = getattr(settings, "PARAMETER_FERNET_KEY", None)
    if explicit:
        key_b = explicit.strip().encode("ascii") if isinstance(explicit, str) else explicit
        try:
            return Fernet(key_b)
        except Exception as exc:
            logger.warning("PARAMETER_FERNET_KEY invalid (%s); using SECRET_KEY derivation", exc)
    sk = getattr(settings, "SECRET_KEY", "") or ""
    try:
        return Fernet(_derive_fernet_key_from_secret_key(sk))
    except Exception as exc:
        logger.error("Could not build Parameter Fernet key: %s", exc)
        return None


def encrypt_json_dict(data: dict[str, Any]) -> str:
    f = get_parameter_fernet()
    if f is None:
        raise RuntimeError("Parameter encryption key is not available")
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return f.encrypt(payload).decode("ascii")


def decrypt_json_dict(token: str) -> Optional[dict[str, Any]]:
    if not token or not str(token).strip():
        return None
    f = get_parameter_fernet()
    if f is None:
        logger.error("Parameter Fernet unavailable; cannot decrypt secrets")
        return None
    try:
        raw = f.decrypt(str(token).strip().encode("ascii"))
        obj = json.loads(raw.decode("utf-8"))
        if not isinstance(obj, dict):
            return None
        return obj
    except InvalidToken:
        logger.warning("Parameter encrypted_payload decrypt failed (wrong key or corrupt data)")
        return None
    except json.JSONDecodeError:
        logger.warning("Parameter decrypted payload is not valid JSON object")
        return None
    except Exception as exc:
        logger.warning("Parameter decrypt error: %s", exc)
        return None
