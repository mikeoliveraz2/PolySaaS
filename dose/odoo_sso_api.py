import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def odoo_sso_api(request):
    """
    Server-side SSO for Odoo.
    Authenticates with Odoo via /web/session/authenticate on behalf of the
    PolySaaS user, returns the session_id so the browser can set the cookie.
    """
    from django.db import connection
    from django.conf import settings
    from dose.utils import get_current_tenant
    from dose.models import PassThroughEndpoint, TenantApp

    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({"error": "No tenant context"}, status=403)

    # Set tenant schema context for queries
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant.schema_name}", public')
    except Exception:
        pass

    # Find the Odoo endpoint for this tenant
    endpoint = None
    try:
        endpoint = PassThroughEndpoint.objects.filter(
            is_enabled=True,
            trigger_path__iexact='odoo',
        ).first()
    except Exception as e:
        logger.warning("[ODOO SSO] Endpoint lookup failed: %s", e)

    if not endpoint:
        return JsonResponse({"error": "No Odoo endpoint configured"}, status=404)

    parsed = urlparse(endpoint.endpoint_url)
    odoo_base = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    proxy_hostname = parsed.netloc  # e.g. polysaas-odoo2.onrender.com
    redirect_url = f"/pt/admin/{proxy_hostname}/web"

    # Get credentials from TenantApp.extra_config (set during subscription)
    ta = TenantApp.objects.filter(tenant=tenant, app_name='odoo').first()
    extra = (ta.extra_config or {}) if ta else {}
    default_pw = getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')
    login = extra.get("odoo_login") or "odooAdmin"
    password = extra.get("odoo_password") or default_pw
    db = extra.get("odoo_db") or "odoodb"

    logger.info("[ODOO SSO] Authenticating login=%s db=%s at %s", login, db, odoo_base)

    # Authenticate via Odoo JSON-RPC /web/session/authenticate
    try:
        import requests as _req
        resp = _req.post(
            f"{odoo_base}/web/session/authenticate",
            json={
                "jsonrpc": "2.0",
                "method": "call",
                "id": 1,
                "params": {"db": db, "login": login, "password": password},
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        data = resp.json()
        uid = (data.get("result") or {}).get("uid")
        session_id = resp.cookies.get("session_id")

        if uid and session_id:
            logger.info("[ODOO SSO] Success uid=%s session=%s...", uid, session_id[:8])
            return JsonResponse({
                "ok": True,
                "session_id": session_id,
                "uid": uid,
                "redirect_url": redirect_url,
            })
        else:
            error_msg = (data.get("error") or {}).get("message") or "Authentication failed"
            logger.warning("[ODOO SSO] Failed uid=%s has_session=%s msg=%s", uid, bool(session_id), error_msg)
            return JsonResponse({
                "error": error_msg,
                "uid": uid,
                "has_session": bool(session_id),
            }, status=401)
    except Exception as exc:
        logger.exception("[ODOO SSO] Request failed: %s", exc)
        return JsonResponse({"error": str(exc)}, status=500)
