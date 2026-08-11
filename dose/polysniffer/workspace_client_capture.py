"""Inject fetch/XHR client capture into sniffed HTML (native external tab + passthrough)."""
from __future__ import annotations

import json
import re


def inject_workspace_client_capture(html: str, endpoint_id: int) -> str:
    """Log direct upstream API calls to /dose/sniff/<id>/workspace/ingest/."""
    if "data-polysniffer-client-capture" in html:
        return html
    ingest = f"/admin/polysniffer/sniff/{endpoint_id}/workspace/ingest/"
    shim = f"""
<script data-polysniffer-client-capture="1">
(function() {{
  var INGEST = {json.dumps(ingest)};
  function send(payload) {{
    try {{
      var blob = new Blob([JSON.stringify(payload)], {{type: 'application/json'}});
      if (navigator.sendBeacon && navigator.sendBeacon(INGEST, blob)) return;
    }} catch (e) {{}}
    fetch(INGEST, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
      keepalive: true
    }}).catch(function() {{}});
  }}
  function pathOf(url) {{
    try {{
      var u = new URL(url, window.location.origin);
      var p = u.pathname + (u.search || '');
      if (u.origin !== window.location.origin) {{
        return (u.host + p).slice(0, 500);
      }}
      return p.slice(0, 500);
    }} catch (e) {{ return String(url).slice(0, 500); }}
  }}
  function log(method, url, status, ms) {{
    if (!url || url.indexOf(INGEST) !== -1) return;
    send({{
      method: method || 'GET',
      url: String(url).slice(0, 500),
      path: pathOf(url).slice(0, 500),
      status_code: status || 0,
      duration_ms: ms || 0
    }});
  }}
  var _f = window.fetch;
  window.fetch = function(input, init) {{
    var method = (init && init.method) || 'GET';
    var url = typeof input === 'string' ? input : (input && input.url) || '';
    var t0 = performance.now();
    return _f.apply(this, arguments).then(function(resp) {{
      log(method, url || (resp && resp.url) || '', resp && resp.status, performance.now() - t0);
      return resp;
    }}, function(err) {{
      log(method, url, 0, performance.now() - t0);
      throw err;
    }});
  }};
  var _xo = XMLHttpRequest.prototype.open;
  var _xs = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(method, url) {{
    this._psMethod = method;
    this._psUrl = url;
    this._psT0 = performance.now();
    return _xo.apply(this, arguments);
  }};
  XMLHttpRequest.prototype.send = function() {{
    var xhr = this;
    xhr.addEventListener('loadend', function() {{
      log(xhr._psMethod, xhr._psUrl, xhr.status, performance.now() - (xhr._psT0 || performance.now()));
    }});
    return _xs.apply(this, arguments);
  }};
}})();
</script>
"""
    if re.search(r"(?i)<head[^>]*>", html):
        return re.sub(r"(?i)(<head[^>]*>)", r"\1" + shim, html, count=1)
    return shim + html
