# dose/polysniffer/views/building_pen_embed.py
# Building pen: server fetch → handler rewrite + strip CSP (so /static hits MM proxy
# and inline pen script is allowed) → inject snapshot script → POST final DOM for touch-up.

import json
import logging
import re

import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.csrf import ensure_csrf_cookie

from ..handlers.registry import get_handler
from .core import get_endpoint_any_schema

logger = logging.getLogger(__name__)

# Let webpack/React settle before snapshot (ms).
SETTLE_MS = 3500

_SPINNER_STYLE = (
    '<style id="poly-pen-spinner-style">'
    "@keyframes polyPenSpin{to{transform:rotate(360deg)}}"
    "#poly-pen-overlay{position:fixed;inset:0;z-index:2147483645;background:rgba(17,17,17,.93);"
    "display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px;"
    "color:#0f0;font:600 15px system-ui,sans-serif;}"
    "#poly-pen-overlay .poly-pen-ring{width:44px;height:44px;border:3px solid #333;"
    "border-top-color:#0f0;border-radius:50%;animation:polyPenSpin .7s linear infinite}"
    "</style>"
)
_SPINNER_HTML = (
    '<div id="poly-pen-overlay" aria-live="polite" aria-busy="true">'
    '<div class="poly-pen-ring"></div>'
    "<span>PolySniffer — loading Mattermost…</span>"
    "</div>"
)


def _inject_spinner_overlay(html: str) -> str:
    """Full-screen loading overlay until document.write replaces the page (or on error)."""
    if re.search(r"</head>", html, flags=re.IGNORECASE):
        html = re.sub(r"(?i)</head>", _SPINNER_STYLE + "</head>", html, count=1)
    elif re.search(r"<head[^>]*>", html, flags=re.IGNORECASE):
        html = re.sub(
            r"(?i)(<head[^>]*>)", r"\1" + _SPINNER_STYLE, html, count=1
        )
    else:
        html = _SPINNER_STYLE + html
    if re.search(r"<body[^>]*>", html, flags=re.IGNORECASE):
        html = re.sub(
            r"(?i)(<body[^>]*>)", r"\1" + _SPINNER_HTML, html, count=1
        )
    else:
        html = _SPINNER_HTML + html
    return html


def _inject_extraction_script(
    html: str, request, service_name: str, endpoint_id: int, settle_ms: int = SETTLE_MS
) -> str:
    cfg = {
        "csrf": get_token(request),
        "processUrl": reverse("building_pen_process"),
        "serviceName": service_name.strip().lower(),
        "endpointId": int(endpoint_id),
        "settleMs": int(settle_ms),
    }
    cfg_js = json.dumps(cfg)
    script = (
        "<script>(function(){var C="
        + cfg_js
        + ";console.log('[PolySniffer] Building pen started — waiting for SPA…');"
        "setTimeout(function(){var h=document.documentElement.outerHTML;"
        "fetch(C.processUrl,{method:'POST',credentials:'same-origin',"
        "headers:{'Content-Type':'application/json','X-CSRFToken':C.csrf},"
        "body:JSON.stringify({service_name:C.serviceName,endpoint_id:C.endpointId,html:h})})"
        ".then(function(r){if(!r.ok)return r.text().then(function(t){throw new Error(r.status+' '+t);});"
        "return r.text();})"
        ".then(function(finalHTML){console.log('[PolySniffer] Building pen complete — applying');"
        "document.open();document.write(finalHTML);document.close();})"
        ".catch(function(err){console.error('[PolySniffer] Process failed:',err);"
        "var o=document.getElementById('poly-pen-overlay');if(o)o.remove();"
        "try{var b=document.body;if(b)b.innerHTML="
        "'<h1 style=color:#f66;font-family:sans-serif;padding:2rem>Building pen failed</h1>"
        "<p style=color:#888;padding:0 2rem>See browser console for details.</p>';}catch(x){}});"
        "},C.settleMs);})();</script>"
    )
    if re.search(r"</body>", html, flags=re.IGNORECASE):
        return re.sub(r"(?i)</body>", script + "</body>", html, count=1)
    return html + script


@staff_member_required
@ensure_csrf_cookie
def building_pen_embed(request, service_name, endpoint_id):
    """
    Fetch upstream shell, run process_html_response (rewrites, CSP strip, toolbar), then
    inject script. Without that first pass, /static/* resolves to :8000 and CSP blocks inline JS.
    """
    handler_class = get_handler(service_name)
    if not handler_class:
        return HttpResponse(
            f"<h1>Unsupported service</h1><p>{escape(service_name)}</p>",
            status=400,
            content_type="text/html; charset=utf-8",
        )

    try:
        get_endpoint_any_schema(endpoint_id, request)
    except Http404:
        return HttpResponse(
            "<h1>PassThroughEndpoint not found</h1>"
            f"<p>id=<strong>{escape(str(endpoint_id))}</strong> — "
            "check Admin → Pass through endpoints for this tenant.</p>",
            status=404,
            content_type="text/html; charset=utf-8",
        )

    label = escape(str(endpoint_id))
    try:
        handler = handler_class(endpoint_id, request)
        endpoint_url = (handler.endpoint.endpoint_url or "").strip()
        if not endpoint_url:
            return HttpResponse(
                "<h1>No endpoint URL</h1>"
                "<p>This PassThroughEndpoint has no <code>endpoint_url</code> configured.</p>",
                status=400,
                content_type="text/html; charset=utf-8",
            )

        cookies = handler.get_upstream_cookies(request) or {}
        resp = requests.get(
            endpoint_url,
            cookies=cookies,
            headers={
                "User-Agent": request.META.get("HTTP_USER_AGENT", "Mozilla/5.0"),
            },
            timeout=15,
            allow_redirects=True,
        )
        html = resp.text
        processed, django_response = handler.process_html_response(
            html,
            request,
            endpoint_url=endpoint_url,
            inject_toolbar=True,
            rewrite_assets=True,
        )
        if django_response is not None:
            return django_response
        html_out = _inject_spinner_overlay(processed)
        html_out = _inject_extraction_script(
            html_out, request, service_name, endpoint_id, SETTLE_MS
        )
        return HttpResponse(
            html_out,
            content_type="text/html; charset=utf-8",
            status=resp.status_code if resp.status_code else 200,
        )
    except Exception as exc:
        logger.exception("[building_pen_embed] failed endpoint_id=%s: %s", label, exc)
        return HttpResponse(
            f"<h1>Failed to fetch upstream shell</h1><pre>{escape(str(exc))}</pre>",
            status=502,
            content_type="text/html; charset=utf-8",
        )
