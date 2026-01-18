"""
AI Analysis Views for PolySniffer
Provides endpoints for AI to analyze captures and generate handlers
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from dose.models import PassThroughEndpoint
from .ai_analysis import generate_handler_from_captures


@staff_member_required
def ai_analyze_endpoint(request, endpoint_id):
    """
    Analyze PolySniffer captures for an endpoint and return structured analysis.
    This is what AI (like Cursor) will use to generate handlers.

    GET /admin/polysniffer/ai-analyze/<endpoint_id>/
    """
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)

    try:
        analysis = generate_handler_from_captures(endpoint_id)

        return JsonResponse({
            "success": True,
            "endpoint_id": endpoint_id,
            "endpoint_url": endpoint.endpoint_url,
            "analysis": analysis,
            "handler_code": analysis.get("handler_code"),
            "ready_for_ai": True
        }, indent=2)

    except Exception as e:
        import traceback
        return JsonResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


@staff_member_required
def ai_generate_handler(request, endpoint_id):
    """
    Generate and apply handler code from PolySniffer analysis.
    This is the "magic button" that makes "access denied" go away.

    POST /admin/polysniffer/ai-generate-handler/<endpoint_id>/
    """
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)

    try:
        analysis = generate_handler_from_captures(endpoint_id)

        if not analysis.get("handler_code"):
            return JsonResponse({
                "success": False,
                "error": "Could not generate handler code. Run PolySniffer first to capture authentication flow."
            }, status=400)

        # Save generated handler code to endpoint
        if not endpoint.discovered_subpaths:
            endpoint.discovered_subpaths = {}
        endpoint.discovered_subpaths['ai_generated_handler'] = analysis["handler_code"]
        endpoint.discovered_subpaths['ai_analysis'] = {
            "authentication": analysis["authentication"],
            "request_patterns": analysis["request_patterns"],
            "cookie_analysis": analysis["cookie_analysis"]
        }
        endpoint.save()

        return JsonResponse({
            "success": True,
            "message": "Handler code generated and saved!",
            "handler_code": analysis["handler_code"],
            "analysis_summary": {
                "auth_method": analysis["authentication"].get("method"),
                "session_cookie": analysis["authentication"].get("session_cookie"),
                "csrf_token_field": analysis["authentication"].get("csrf_token_field")
            }
        }, indent=2)

    except Exception as e:
        import traceback
        return JsonResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

