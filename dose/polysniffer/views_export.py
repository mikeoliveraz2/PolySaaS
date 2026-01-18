"""
Export Views for PolySniffer - Phase 2 AI Integration
Provides endpoints for exporting structured captures as LLM prompts
"""
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from dose.models import PassThroughEndpoint
from .structured_capture import (
    generate_structured_capture,
    generate_llm_prompt,
    generate_grok_url
)


@staff_member_required
def export_structured_capture(request, endpoint_id):
    """
    Export structured capture JSON - copy-paste ready for LLMs.
    
    GET /admin/polysniffer/export-structured/<endpoint_id>/
    """
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)
    
    try:
        structured = generate_structured_capture(endpoint)
        
        return JsonResponse(structured, indent=2, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        import traceback
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


@staff_member_required
def export_llm_prompt(request, endpoint_id):
    """
    Export structured capture as LLM prompt - ready to paste into Cursor, Claude, Grok.
    
    GET /admin/polysniffer/export-llm-prompt/<endpoint_id>/
    """
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)
    
    try:
        structured = generate_structured_capture(endpoint)
        prompt = generate_llm_prompt(structured)
        
        response = HttpResponse(prompt, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="polysniffer-llm-prompt-{endpoint_id}.txt"'
        return response
    
    except Exception as e:
        import traceback
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


@staff_member_required
def get_grok_url(request, endpoint_id):
    """
    Get Grok URL with pre-filled prompt.
    
    GET /admin/polysniffer/grok-url/<endpoint_id>/
    Returns JSON with URL to open in Grok.
    """
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)
    
    try:
        structured = generate_structured_capture(endpoint)
        grok_url = generate_grok_url(structured)
        
        return JsonResponse({
            "success": True,
            "grok_url": grok_url,
            "message": "Open this URL in Grok to generate handler code"
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

