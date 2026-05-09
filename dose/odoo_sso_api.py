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

    # Find the Odoo endpoint — try exact name first, fall back to URL/trigger containing 'odoo'
    endpoint = None
    try:
        from django.db.models import Q
        endpoint = PassThroughEndpoint.objects.filter(is_enabled=True).filter(
            Q(trigger_path__iexact='odoo') |
            Q(trigger_path__icontains='odoo') |
            Q(endpoint_url__icontains='odoo')
        ).order_by('id').first()
    except Exception as e:
        logger.warning("[ODOO SSO] Endpoint lookup failed: %s", e)

    if not endpoint:
        return JsonResponse({"error": "No Odoo endpoint configured"}, status=404)

    logger.info("[ODOO SSO] Using endpoint trigger_path=%s endpoint_url=%s",
                endpoint.trigger_path, endpoint.endpoint_url)

    parsed = urlparse(endpoint.endpoint_url)
    odoo_base = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    # Use trigger_path (e.g. "odoo") not the hostname — the named trigger routes through
    # display.html which provides the Odoo body-scope container and Owl mounting hooks.
    # The hostname trigger bypasses display.html for sub-paths → blank screen.
    redirect_url = f"/pt/admin/{endpoint.trigger_path.strip('/')}/web"

    # Get credentials from TenantApp.extra_config (set during subscription)
    ta = TenantApp.objects.filter(tenant=tenant, app_name='odoo').first()
    extra = (ta.extra_config or {}) if ta else {}
    default_pw = getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')

    # odoo_db stored during subscription is tenant.schema_name — not the Odoo DB name.
    # Always use 'odoodb' (the Odoo instance DB) regardless of what is stored.
    db = "odoodb"

    # Try tenant user first, fall back to admin
    stored_login = extra.get("odoo_login") or ""
    stored_pw    = extra.get("odoo_password") or ""
    credential_sets = []
    if stored_login and stored_pw:
        credential_sets.append((stored_login, stored_pw, "tenant-user"))
    credential_sets.append(("odooAdmin", default_pw, "admin-fallback"))

    logger.info("[ODOO SSO] db=%s at %s — trying %d credential set(s)", db, odoo_base, len(credential_sets))

    import requests as _req

    last_error = "Authentication failed"
    for login, password, cred_label in credential_sets:
        try:
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
                logger.info("[ODOO SSO] Success cred=%s uid=%s session=%s...", cred_label, uid, session_id[:8])
                return JsonResponse({
                    "ok": True,
                    "session_id": session_id,
                    "uid": uid,
                    "redirect_url": redirect_url,
                })

            odoo_err = (data.get("error") or {})
            last_error = odoo_err.get("data", {}).get("message") or odoo_err.get("message") or "Authentication failed"
            logger.warning("[ODOO SSO] cred=%s login=%s db=%s => uid=%s err=%s", cred_label, login, db, uid, last_error)

        except Exception as exc:
            last_error = str(exc)
            logger.exception("[ODOO SSO] Request failed cred=%s: %s", cred_label, exc)

    return JsonResponse({
        "error": last_error,
        "debug": f"tried login={stored_login or 'odooAdmin'} db={db} at {odoo_base}",
    }, status=401)
