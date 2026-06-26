"""Minimal workspace embed shell for PolySniffer native sniff (no orchestration bar)."""
from __future__ import annotations

import re

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


def workspace_browse_prefix(endpoint_id: int) -> str:
    """Transparent proxy prefix for API/assets (not full workspace chrome)."""
    return f"/dose/sniff/{endpoint_id}/workspace/browse"


def workspace_shell_prefix(endpoint_id: int) -> str:
    """HTML navigation prefix — reloads PolySniffer shell with inline native embed."""
    return f"/dose/sniff/{endpoint_id}/workspace"


def _extract_head_and_body(html: str) -> tuple[str, str]:
    head_content = ""
    body_content = html
    head_match = re.search(r"<head[^>]*>(.*?)</head>", html, re.DOTALL | re.IGNORECASE)
    if head_match:
        head_content = head_match.group(1)
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_content = body_match.group(1)
    elif "<body" in html.lower():
        body_start = re.search(r"<body[^>]*>", html, re.IGNORECASE)
        if body_start:
            body_content = html[body_start.end() :]
            body_content = re.sub(r"</html>\s*$", "", body_content, flags=re.IGNORECASE)
    return head_content, body_content


def _is_html_response(response: HttpResponse) -> bool:
    content_type = (response.get("Content-Type") or "").lower()
    return "text/html" in content_type or "application/xhtml" in content_type


def wrap_native_sniff_for_workspace(
    request,
    endpoint_id: int,
    response: HttpResponse,
    *,
    endpoint_label: str = "",
) -> HttpResponse:
    """
    Wrap native sniff HTML in a minimal iframe-friendly shell (passthrough-style
  content column only — no Jazzmin chrome, no orchestration bar).
    """
    if request.method != "GET" or not _is_html_response(response):
        return response
    try:
        raw_html = response.content.decode("utf-8", errors="ignore")
    except Exception:
        return response
    if not raw_html or len(raw_html) < 50:
        return response

    head_content, body_content = _extract_head_and_body(raw_html)
    browse_base = workspace_browse_prefix(endpoint_id)
    wrapped = render_to_string(
        "polysniffer/sniff_native_embed.html",
        {
            "embed_title": endpoint_label or f"PolySniffer native — ep{endpoint_id}",
            "embed_head": mark_safe(head_content),
            "embed_body": mark_safe(body_content),
            "browse_base": browse_base,
        },
        request=request,
    )
    wrapped_response = HttpResponse(wrapped, status=response.status_code)
    wrapped_response["Content-Type"] = "text/html; charset=utf-8"
    wrapped_response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    for cookie_name in response.cookies:
        wrapped_response.cookies[cookie_name] = response.cookies[cookie_name].value
    if response.has_header("Location"):
        wrapped_response["Location"] = response["Location"]
    return wrapped_response


def build_inline_native_embed_context(
    request,
    endpoint_id: int,
    endpoint,
    path: str,
    *,
    endpoint_label: str = "",
) -> dict | None:
    """Build head/body fragments for native embed inlined in the workspace left pane."""
    from dose.polysniffer.sniff_forward import forward_sniff_native
    from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session

    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = "native"
    bind_request_tenant(request)
    session = get_sniff_capture_session(request, endpoint_id)
    if session:
        request._polysniffer_capture = session

    response = forward_sniff_native(request, endpoint, path or "")
    if request.method != "GET" or not _is_html_response(response):
        return None
    try:
        raw_html = response.content.decode("utf-8", errors="ignore")
    except Exception:
        return None
    if not raw_html or len(raw_html) < 50:
        return None

    head_content, body_content = _extract_head_and_body(raw_html)
    shell_base = workspace_shell_prefix(endpoint_id)
    return {
        "native_embed_title": endpoint_label or f"PolySniffer native — ep{endpoint_id}",
        "native_embed_head": mark_safe(head_content),
        "native_embed_body": mark_safe(body_content),
        "native_browse_base": shell_base,
    }
