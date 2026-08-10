"""
AI Analysis Views for PolySniffer
Provides endpoints for AI to analyze captures and generate handlers
"""
import json

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .ai_analysis import generate_handler_from_captures
from .views.core import get_endpoint_by_host


def _capture_session_id(request):
    if request.method == "GET":
        raw_value = request.GET.get("capture_session_id")
    elif request.content_type == "application/json":
        try:
            raw_value = json.loads(request.body.decode("utf-8") or "{}").get(
                "capture_session_id"
            )
        except json.JSONDecodeError:
            raw_value = None
    else:
        raw_value = request.POST.get("capture_session_id")
    try:
        capture_session_id = int(raw_value)
    except (TypeError, ValueError):
        return None
    return capture_session_id if capture_session_id > 0 else None


@staff_member_required
@require_GET
def ai_analyze_endpoint(request, endpoint_host):
    """
    Analyze PolySniffer captures for an endpoint and return structured analysis.
    This is what AI (like Cursor) will use to generate handlers.

    GET /admin/polysniffer/ai-analyze/<endpoint_id>/
    """
    endpoint = get_endpoint_by_host(endpoint_host, request)
    capture_session_id = _capture_session_id(request)
    if capture_session_id is None:
        return JsonResponse(
            {"success": False, "error": "capture_session_id is required"},
            status=400,
        )

    try:
        analysis = generate_handler_from_captures(endpoint_host, capture_session_id)
        if analysis.get("error"):
            return JsonResponse({"success": False, **analysis}, status=400)

        return JsonResponse({
            "success": True,
            "endpoint_host": endpoint_host,
            "endpoint_url": endpoint.endpoint_url,
            "analysis": analysis,
            "handler_code": analysis.get("handler_code"),
            "ready_for_ai": True
        }, json_dumps_params={'indent': 2})

    except Exception as e:
        import traceback
        return JsonResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


@staff_member_required
@require_POST
def ai_generate_handler(request, endpoint_host):
    """
    Generate a reviewable handler draft from one completed Native session.

    POST /admin/polysniffer/ai-generate-handler/<endpoint_id>/
    """
    endpoint = get_endpoint_by_host(endpoint_host, request)
    capture_session_id = _capture_session_id(request)
    if capture_session_id is None:
        return JsonResponse(
            {"success": False, "error": "capture_session_id is required"},
            status=400,
        )

    try:
        analysis = generate_handler_from_captures(endpoint_host, capture_session_id)

        if analysis.get("error"):
            return JsonResponse({"success": False, **analysis}, status=400)

        if not analysis.get("handler_code"):
            return JsonResponse({
                "success": False,
                "error": "Could not generate handler code. Run PolySniffer first to capture authentication flow."
            }, status=400)

        return JsonResponse({
            "success": True,
            "status": "draft",
            "message": "Handler draft generated for review; nothing was installed or saved.",
            "endpoint_host": endpoint_host,
            "endpoint_url": endpoint.endpoint_url,
            "capture_session_id": analysis["capture_session_id"],
            "capture_session_name": analysis.get("capture_session_name", ""),
            "tenant_schema": analysis.get("tenant_schema", ""),
            "handler_code": analysis["handler_code"],
            "analysis_summary": {
                "auth_method": analysis["authentication"].get("method"),
                "session_cookie": analysis["authentication"].get("session_cookie"),
                "csrf_token_field": analysis["authentication"].get("csrf_token_field")
            }
        }, json_dumps_params={'indent': 2})

    except Exception as e:
        import traceback
        return JsonResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

