"""
Inline passthrough embed for PolySniffer workspace.

Browser-facing prefix: /pt/polysniff/{endpoint_id}/ (not /pt/admin/).
Production handlers run internally via dispatch_polysniff_passthrough (frozen sniff_pt_proxy).
"""
from __future__ import annotations

import json
import re

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from dose.passthrough.embed_fragments import build_scoped_embed_fragments
from dose.passthrough.registry import resolve_handler_for_pt_admin_trigger
from dose.polysniffer.handler_hooks import non_page_path_prefixes
from dose.polysniffer.sniff_native_embed import (
    _is_html_response,
    _split_head_for_inline,
    workspace_shell_prefix,
)
from dose.polysniffer.sniff_pt_proxy import public_polysniff_prefix
from dose.polysniffer.workspace_pt_redirect import (
    rewrite_pt_form_actions_to_workspace,
    subpath_from_passthrough_location,
    workspace_shell_url,
)


def polysniff_proxy_prefix(endpoint_id: int) -> str:
    """Public PolySniffer passthrough prefix — /pt/polysniff/<id>."""
    return public_polysniff_prefix(endpoint_id).rstrip("/")


def build_workspace_shell_guard_script(
    shell_prefix: str,
    proxy_prefix: str,
    endpoint_id: int,
    *,
    non_page_prefixes: tuple[str, ...] = (),
) -> str:
    """Keep passthrough HTML navigations inside the PolySniffer workspace shell."""
    shell = json.dumps((shell_prefix or "").rstrip("/"))
    proxy = json.dumps((proxy_prefix or "").rstrip("/"))
    prefixes = json.dumps(list(non_page_prefixes))
    ep = int(endpoint_id)
    return f"""<script data-ps-workspace-guard="1">
(function() {{
  var SHELL = {shell};
  var PROXY = {proxy};
  var EP = {ep};
  var NON_PAGE = {prefixes};
  // HubSpot login SPA treats /dose/sniff/.../workspace/login as an invalid magic-link path.
  // Present /pt/polysniff/<id>/login/ to the browser before upstream scripts boot.
  try {{
    var p = window.location.pathname || '';
    if (PROXY && p.indexOf('/dose/sniff/') >= 0 && p.indexOf('/workspace/') >= 0) {{
      var tail = p.split('/workspace/')[1] || 'login/';
      if (tail.charAt(0) === '/') tail = tail.slice(1);
      if (tail.toLowerCase().indexOf('login') === 0 && tail.slice(-1) !== '/') tail += '/';
      history.replaceState(null, '', PROXY + '/' + tail + window.location.search + window.location.hash);
    }}
  }} catch (e) {{}}
  function isNonPage(sub) {{
    var low = (sub || '').toLowerCase();
    if (!low || low.charAt(0) !== '/') low = '/' + (low || '');
    for (var i = 0; i < NON_PAGE.length; i++) {{
      var p = NON_PAGE[i];
      if (p.charAt(0) !== '/') p = '/' + p;
      if (low.indexOf(p.toLowerCase()) === 0) return true;
    }}
    var last = low.split('/').pop() || '';
    if (last.indexOf('.') > 0) {{
      var ext = last.split('.').pop();
      if (/^(js|css|map|png|jpg|jpeg|gif|svg|ico|woff2?|json)$/.test(ext)) return true;
    }}
    return false;
  }}
  function shellUrl(pathname, search, hash) {{
    if (!PROXY || pathname.indexOf(PROXY) !== 0) return null;
    var sub = pathname.slice(PROXY.length) || '/';
    if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
    if (isNonPage(sub)) return null;
    return SHELL + sub + (search || '') + (hash || '');
  }}
  function guard(url) {{
    try {{
      var u = new URL(String(url || ''), window.location.origin);
      if (u.origin !== window.location.origin) return url;
      var target = shellUrl(u.pathname, u.search, u.hash);
      if (target) return target;
      if (u.pathname.indexOf('/dose/sniff/' + EP + '/workspace') === 0) return url;
      if (u.pathname.indexOf('/pt/admin/') === 0) {{
        var rest = u.pathname.replace(/^\\/pt\\/admin\\/[^/]+/, '') || '/';
        if (!rest || rest.charAt(0) !== '/') rest = '/' + rest;
        if (!isNonPage(rest)) return SHELL + rest + (u.search || '') + (u.hash || '');
      }}
      var p = u.pathname || '/';
      if (p.indexOf('/pt/') !== 0 && p.indexOf('/admin/') !== 0 && p.indexOf('/dose/') !== 0 &&
          p.indexOf('/accounts/') !== 0 && p.charAt(0) === '/' && !isNonPage(p)) {{
        return SHELL + p + (u.search || '') + (u.hash || '');
      }}
    }} catch (e) {{}}
    return url;
  }}
  var _assign = window.location.assign.bind(window.location);
  var _replace = window.location.replace.bind(window.location);
  window.location.assign = function(u) {{ _assign(guard(u)); }};
  window.location.replace = function(u) {{ _replace(guard(u)); }};
  try {{
    var _href = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
    if (_href && _href.set) {{
      Object.defineProperty(window.location, 'href', {{
        configurable: true,
        get: function() {{ return _href.get.call(window.location); }},
        set: function(v) {{ _href.set.call(window.location, guard(v)); }}
      }});
    }}
  }} catch (e) {{}}
  var _push = history.pushState.bind(history);
  var _rep = history.replaceState.bind(history);
  history.pushState = function(state, title, url) {{
    if (url) {{ var g = guard(url); if (g !== url) {{ _push(state, title, g); return; }} }}
    return _push.apply(history, arguments);
  }};
  history.replaceState = function(state, title, url) {{
    if (url) {{ var g = guard(url); if (g !== url) {{ _rep(state, title, g); return; }} }}
    return _rep.apply(history, arguments);
  }};
  window.__PS_WORKSPACE_SHELL_PREFIX = SHELL;
}})();
</script>"""


def _trigger_host(endpoint) -> str:
    from urllib.parse import urlparse

    return urlparse((getattr(endpoint, "endpoint_url", None) or "").strip()).netloc or ""


def build_inline_passthrough_embed_context(
    request,
    endpoint_id: int,
    endpoint,
    path: str,
    *,
    endpoint_label: str = "",
) -> dict | None:
    """Passthrough HTML as inline embed — /pt/polysniff/{id}/ in browser, handler chain internal."""
    from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough
    from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session

    trigger = _trigger_host(endpoint)
    if not trigger:
        return None

    bind_request_tenant(request)
    session = get_sniff_capture_session(request, endpoint_id)
    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = "passthrough"
    request._polysniffer_workspace_inline = True
    if session:
        request._polysniffer_capture = session

    handler = resolve_handler_for_pt_admin_trigger(trigger)
    if handler is not None:
        handler.endpoint = endpoint

    subpath = (path or "").strip().lstrip("/")
    response = dispatch_polysniff_passthrough(request, endpoint_id, subpath)

    if response.status_code in (301, 302, 303, 307, 308):
        loc = response.get("Location", "")
        rel = subpath_from_passthrough_location(loc, endpoint_id, trigger)
        return {"redirect": workspace_shell_url(endpoint_id, rel)}

    if request.method != "GET" or not _is_html_response(response):
        return None
    try:
        raw_html = response.content.decode("utf-8", errors="ignore")
    except Exception:
        return None
    if not raw_html or len(raw_html) < 50:
        return None

    embed_head, scoped_body = build_scoped_embed_fragments(
        raw_html,
        trigger,
        handler=handler,
        request=request,
    )

    head_html = rewrite_pt_form_actions_to_workspace(str(embed_head), endpoint_id, trigger)
    body_html = rewrite_pt_form_actions_to_workspace(str(scoped_body), endpoint_id, trigger)
    head_static, head_scripts = _split_head_for_inline(head_html)
    orch_bar = render_to_string("polysniffer/sniff_pt_orchestration_bar.html", request=request)
    shell_base = workspace_shell_prefix(endpoint_id)
    proxy_base = polysniff_proxy_prefix(endpoint_id)
    np_prefixes = non_page_path_prefixes(handler, request, f"/{subpath}" if subpath else "/")
    guard = build_workspace_shell_guard_script(
        shell_base,
        proxy_base,
        endpoint_id,
        non_page_prefixes=np_prefixes,
    )
    scoped_base = f'<base href="{proxy_base}/">'
    body_html = re.sub(
        r'(<div class="polysaas-passthrough-scope[^"]*"[^>]*>)',
        r"\1" + scoped_base,
        body_html,
        count=1,
    )
    embed_body = mark_safe(f"{orch_bar}{head_scripts}{body_html}")

    return {
        "passthrough_embed_title": endpoint_label or f"PolySniffer passthrough — ep{endpoint_id}",
        "passthrough_guard_head": mark_safe(guard),
        "passthrough_embed_head": mark_safe(head_static),
        "passthrough_embed_body": embed_body,
        "passthrough_browse_base": proxy_base,
        "passthrough_shell_base": shell_base,
        "passthrough_endpoint_id": endpoint_id,
        "passthrough_non_page_prefixes_json": json.dumps(list(np_prefixes)),
    }
