"""
Session sync endpoint for HubSpot popup authentication.

After popup login on hubspot.com succeeds, the client calls this endpoint to
persist session cookies server-side for upstream passthrough forwarding.
"""
import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def _session_service(request, endpoint_id: int):
    from dose.services.hubspot_session import HubspotSessionService

    return HubspotSessionService(request, endpoint_id=endpoint_id)


def _harvest_via_passthrough(request, endpoint_id: int, endpoint_host: str = "") -> bool:
    """
    Best-effort: run passthrough GET /home/ server-side and capture Set-Cookie
    from upstream into HubspotSessionService (same path as login_post capture).
    """
    try:
        from urllib.parse import urlparse

        from dose.models import PassThroughEndpoint
        from dose.passthrough.registry import resolve_handler_for_pt_admin_trigger
        from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough

        endpoint = PassThroughEndpoint.objects.filter(pk=endpoint_id).first()
        if not endpoint:
            return False

        trigger = urlparse((getattr(endpoint, "endpoint_url", None) or "").strip()).netloc
        host = (endpoint_host or trigger or "").strip()
        if not host:
            return False

        handler = resolve_handler_for_pt_admin_trigger(trigger) if trigger else None
        if handler is not None:
            handler.endpoint = endpoint

        request._polysniffer_endpoint_id = endpoint_id
        request._polysniffer_sniff_mode = "passthrough"
        resp = dispatch_polysniff_passthrough(request, host, "home/")
        if handler and hasattr(handler, "_capture_login_cookies_from_response"):
            handler._capture_login_cookies_from_response(resp, request)

        svc = _session_service(request, endpoint_id)
        cookies = svc._django_session_cookies()
        if cookies:
            return svc.validate_web_cookies(cookies)
    except Exception as exc:
        logger.warning(
            "[SYNC-SESSION] harvest_via_passthrough failed eid=%s: %s", endpoint_id, exc
        )
    return False


@staff_member_required
@csrf_exempt
def sync_hubspot_session(request, endpoint_host: str):
    """
    Receive HubSpot session cookies from popup and store server-side.

    POST /pt/polysniff/{endpoint_host}/api/sync-session/
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    from dose.polysniffer.views.core import get_endpoint_by_host

    try:
        endpoint = get_endpoint_by_host(endpoint_host, request)
    except Exception as exc:
        return JsonResponse({"error": f"endpoint not found: {exc}"}, status=404)

    endpoint_id = int(endpoint.pk)
    host = (endpoint_host or "").strip().strip("/")

    try:
        data = json.loads(request.body.decode("utf-8"))
        action = (data.get("action") or "store").strip().lower()
        cookies = data.get("cookies") or {}

        svc = _session_service(request, endpoint_id)

        if action == "probe":
            stored = svc.ensure_web_cookies()
            valid = bool(stored)
            return JsonResponse(
                {
                    "status": "probe",
                    "validated": valid,
                    "count": len(stored),
                }
            )

        if action == "after_popup":
            harvested = _harvest_via_passthrough(request, endpoint_id, host)
            stored = svc.ensure_web_cookies()
            valid = False
            if stored:
                valid = svc.validate_web_cookies(stored)
            logger.warning(
                "[SYNC-SESSION] after_popup host=%s eid=%s harvested=%s validated=%s count=%s cookies=%s",
                host,
                endpoint_id,
                harvested,
                valid,
                len(stored),
                ",".join(sorted(stored.keys())) if stored else "",
            )
            return JsonResponse(
                {
                    "status": "after_popup",
                    "validated": valid,
                    "count": len(stored),
                    "harvested": harvested,
                }
            )

        if not cookies:
            logger.warning(
                "[SYNC-SESSION] No cookies in payload for host=%s eid=%s", host, endpoint_id
            )
            return JsonResponse({"status": "no-cookies", "validated": False}, status=200)

        svc.persist_web_cookies(cookies, source="popup_sync")
        valid = svc.validate_web_cookies(svc._django_session_cookies())
        logger.warning(
            "[SYNC-SESSION] Stored %d cookies for host=%s eid=%s validated=%s",
            len(cookies),
            host,
            endpoint_id,
            valid,
        )
        logger.warning("[SYNC-SESSION] Cookie names: %s", ", ".join(cookies.keys()))
        return JsonResponse(
            {
                "status": "stored",
                "count": len(cookies),
                "validated": valid,
            }
        )

    except json.JSONDecodeError:
        logger.warning("[SYNC-SESSION] Invalid JSON in sync-session request")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception("[SYNC-SESSION] Unexpected error: %s", e)
        return JsonResponse({"error": str(e)}, status=500)
