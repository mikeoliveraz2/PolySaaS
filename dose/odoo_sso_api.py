import time
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required
def odoo_sso_api(request):
    """
    Server-side SSO for Odoo.
    Authenticates with Odoo via JSON-RPC on behalf of the PolySaaS user,
    returns the session_id so the browser can set the cookie and load Odoo.
    """
    from dose.utils import get_current_tenant
    from dose.models import PassThroughEndpoint, TenantApp

    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({"error": "No tenant context"}, status=403)

    # Find the Odoo endpoint for this tenant
    odoo_url = None
    try:
        endpoint = PassThroughEndpoint.objects.filter(
            tenant=tenant,
            endpoint_url__contains="odoo",
            is_enabled=True,
        ).first()
        if endpoint:
            odoo_url = endpoint.endpoint_url.rstrip("/")
    except Exception:
        pass

    if not odoo_url:
        return JsonResponse({"error": "No Odoo endpoint configured"}, status=404)

    # Get tenant config for Odoo credentials
    tenant_config = tenant.get_config_dict()
    odoo_config = tenant_config.get("odoo_provision", {})

    login = odoo_config.get("user_login", "")
    password = odoo_config.get("user_password", "")
    db = odoo_config.get("database_name", "odoodb")

    if not login or not password:
        return JsonResponse({"error": "Odoo credentials not configured"}, status=400)

    # Server-side JSON-RPC authenticate to Odoo
    try:
        import requests as _req
        auth_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [db, login, password, {}],
            },
            "id": int(time.time()),
        }
        resp = _req.post(
            f"{odoo_url}/jsonrpc",
            json=auth_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        data = resp.json()
        uid = data.get("result")
        session_id = resp.cookies.get("session_id")

        if uid and session_id:
            return JsonResponse({
                "ok": True,
                "session_id": session_id,
                "uid": uid,
                "redirect_url": f"/pt/admin/{endpoint.trigger_path}/",
            })
        else:
            return JsonResponse({
                "error": "Odoo authentication failed",
                "uid": uid,
                "has_session": bool(session_id),
            }, status=401)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
