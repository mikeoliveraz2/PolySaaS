"""
AI Analysis Views for PolySniffer
Provides endpoints for AI to analyze captures and generate handlers
"""
import json

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET, require_POST

from .ai_analysis import generate_handler_from_captures
from .views.core import get_endpoint_by_host


def _capture_session_id(value):
    try:
        capture_session_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("capture_session_id is required") from exc
    if capture_session_id <= 0:
        raise ValueError("capture_session_id must be positive")
    return capture_session_id


@staff_member_required
@require_GET
def ai_analyze_endpoint(request, endpoint_host):
    try:
        get_endpoint_by_host(endpoint_host, request)
        capture_session_id = _capture_session_id(
            request.GET.get("capture_session_id")
        )
        analysis = generate_handler_from_captures(
            endpoint_host,
            capture_session_id,
        )

        return JsonResponse({
            "success": True,
            "status": "draft",
            "endpoint_host": endpoint_host,
            "capture_session_id": capture_session_id,
            "analysis": analysis,
            "handler_code": analysis.get("handler_code"),
        }, json_dumps_params={'indent': 2})
    except ValueError as exc:
        return JsonResponse({
            "success": False,
            "error": str(exc),
        }, status=400)


@staff_member_required
@require_POST
def ai_generate_handler(request, endpoint_host):
    try:
        get_endpoint_by_host(endpoint_host, request)
        payload = json.loads(request.body or b"{}")
        capture_session_id = _capture_session_id(
            payload.get("capture_session_id")
        )
        analysis = generate_handler_from_captures(
            endpoint_host,
            capture_session_id,
        )

        if not analysis.get("handler_code"):
            return JsonResponse({
                "success": False,
                "error": analysis.get("error") or "Could not generate handler draft",
            }, status=400)

        return JsonResponse({
            "success": True,
            "status": "draft",
            "endpoint_host": endpoint_host,
            "capture_session_id": capture_session_id,
            "handler_code": analysis["handler_code"],
            "analysis": analysis,
        }, json_dumps_params={'indent': 2})
    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse({
            "success": False,
            "error": str(exc),
        }, status=400)

