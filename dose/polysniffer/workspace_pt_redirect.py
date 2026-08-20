"""Keep passthrough HTML navigations inside the PolySniffer workspace shell."""
from __future__ import annotations

from urllib.parse import urlparse

from django.http import HttpResponse
from django.shortcuts import redirect

from dose.polysniffer.handler_hooks import path_looks_like_non_page
from dose.polysniffer.sniff_native_embed import workspace_shell_prefix
from dose.polysniffer.sniff_pt_proxy import public_polysniff_prefix


def workspace_pt_proxy_prefix(endpoint_id: int) -> str:
    return f"/dose/sniff/{endpoint_id}/workspace/pt"


def admin_proxy_prefix(trigger: str) -> str:
    return f"/pt/admin/{(trigger or '').strip('/')}"


def subpath_from_passthrough_location(location: str, endpoint_id: int, trigger: str) -> str:
    """Map /pt/polysniff/<host>/path (or legacy /pt/polysniff/<id>/, or /pt/admin/) to upstream subpath."""
    loc = (location or "").strip()
    host = (trigger or "").strip()
    prefixes = (
        public_polysniff_prefix(host).rstrip("/") if host else "",
        f"/pt/polysniff/{endpoint_id}",  # legacy id-keyed prefix
        workspace_pt_proxy_prefix(endpoint_id).rstrip("/"),
        admin_proxy_prefix(trigger).rstrip("/"),
    )
    for prefix in prefixes:
        if not prefix:
            continue
        if loc.startswith(prefix + "/"):
            return loc[len(prefix) + 1 :]
        if loc == prefix:
            return ""
    if loc.startswith(("http://", "https://")):
        parsed = urlparse(loc)
        if parsed.netloc and trigger and parsed.netloc.lower() == trigger.lower():
            return (parsed.path or "/").lstrip("/")
        return ""
    if loc.startswith("/"):
        return loc.lstrip("/")
    return ""


def is_workspace_html_navigation(request, path: str = "", *, handler=None) -> bool:
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return False
    accept = (request.headers.get("Accept") or "").lower()
    if "text/html" not in accept and "*/*" not in accept:
        return False
    if path_looks_like_non_page(path, handler=handler, request=request):
        return False
    return True


def workspace_shell_url(endpoint_id: int, subpath: str = "") -> str:
    shell = workspace_shell_prefix(endpoint_id)
    sub = (subpath or "").strip().strip("/")
    return f"{shell}/{sub}" if sub else shell


def copy_response_cookies(source: HttpResponse, target: HttpResponse) -> None:
    for name in source.cookies:
        target.cookies[name] = source.cookies[name].value
        for key in ("path", "domain", "secure", "httponly", "samesite", "max-age"):
            if source.cookies[name].get(key) is not None:
                target.cookies[name][key] = source.cookies[name][key]


def workspace_redirect_for_pt_response(
    request,
    endpoint_id: int,
    path: str,
    response: HttpResponse,
    *,
    trigger: str = "",
    handler=None,
) -> HttpResponse | None:
    if (request.GET.get("ps_hs_popup") or "").strip() == "1":
        return None
    if not is_workspace_html_navigation(request, path, handler=handler):
        return None

    shell_target = None
    if response.status_code in (301, 302, 303, 307, 308):
        loc = response.get("Location", "")
        sub = subpath_from_passthrough_location(loc, endpoint_id, trigger)
        shell_target = workspace_shell_url(endpoint_id, sub)
    else:
        content_type = (response.get("Content-Type") or "").lower()
        if request.method in ("GET", "POST") and "text/html" in content_type:
            shell_target = workspace_shell_url(endpoint_id, path)

    if not shell_target:
        return None
    current = (request.path_info or "").split("?")[0].rstrip("/")
    if current == shell_target.rstrip("/"):
        return None

    wrapped = redirect(shell_target)
    copy_response_cookies(response, wrapped)
    return wrapped


def rewrite_pt_form_actions_to_workspace(html: str, endpoint_id: int, trigger: str) -> str:
    """Login/forms post via workspace/pt → /pt/polysniff dispatch → shell redirect."""
    host = (trigger or "").strip()
    pub = public_polysniff_prefix(host).rstrip("/") if host else f"/pt/polysniff/{endpoint_id}"
    legacy_pub = f"/pt/polysniff/{endpoint_id}"
    ws = workspace_pt_proxy_prefix(endpoint_id).rstrip("/")
    admin = admin_proxy_prefix(trigger).rstrip("/")
    for old, new in (
        (f'action="{pub}/', f'action="{ws}/'),
        (f"action='{pub}/", f"action='{ws}/"),
        (f'action="{pub}"', f'action="{ws}"'),
        (f"action='{pub}'", f"action='{ws}'"),
        (f'action="{legacy_pub}/', f'action="{ws}/'),
        (f"action='{legacy_pub}/", f"action='{ws}/"),
        (f'action="{legacy_pub}"', f'action="{ws}"'),
        (f"action='{legacy_pub}'", f"action='{ws}'"),
        (f'action="{admin}/', f'action="{ws}/'),
        (f"action='{admin}/", f"action='{ws}/"),
        (f'action="{admin}"', f'action="{ws}"'),
        (f"action='{admin}'", f"action='{ws}'"),
    ):
        html = html.replace(old, new)
    return html
