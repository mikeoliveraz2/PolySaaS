"""
Optional HS256 JWT claims for tenant_id / tenant_role (API clients).

Does not replace django-oauth-toolkit opaque access tokens; only decodes tokens
that are valid HS256 JWTs signed with SECRET_KEY and carry tenant claims.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def decode_tenant_claims_from_bearer(auth_header):
    """
    If Authorization is ``Bearer <jwt>``, try to decode HS256 payload.

    Returns dict with optional keys: tenant_id (int), tenant_role (str), or None.
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    if not token or token.count(".") != 2:
        return None
    try:
        import jwt
    except ImportError:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": []},
        )
    except Exception as e:
        logger.debug("tenant JWT decode skipped: %s", e)
        return None
    tid = payload.get("tenant_id")
    if tid is None:
        return None
    try:
        tid = int(tid)
    except (TypeError, ValueError):
        return None
    role = payload.get("tenant_role") or payload.get("role")
    if role is not None and not isinstance(role, str):
        role = str(role)
    return {"tenant_id": tid, "tenant_role": role}
