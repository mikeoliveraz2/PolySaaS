#!/usr/bin/env python3
"""Flask-based interactive proxy for OSTicket/Oliver dashboard.

Provides URL rewriting, session management, and AJAX interception to enable
browsing external applications through a local proxy.

Usage:
    python -m dose.osticket.proxy

Or import and use:
    from dose.osticket.proxy import app, run
    run(host="127.0.0.1", port=8001)
"""

from flask import Flask, request, Response, render_template_string
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


app = Flask(__name__)

# Session store for maintaining cookies per client
_session_store = {}

# Configuration - can be overridden
REAL_BASE = "https://oliverenterprises.app.saasify.cloud/scp/"
PROXY_PATH = "/admin/osticket/"


def doseify_html(html: str) -> str:
    """Convert incoming HTML: replace real URLs with proxy paths and inject JS interception."""
    import re

    # Replace full URLs first
    html = html.replace("https://oliverenterprises.app.saasify.cloud/scp/", PROXY_PATH)
    html = html.replace("https://oliverenterprises.app.saasify.cloud", "/admin/osticket")

    # Fix href and src attributes: /scp/something -> /admin/osticket/something
    html = re.sub(r'(href|src)="/scp/([^"]*)"',
                   r'\1="/admin/osticket/\2"',
                   html)

    # Fix remaining /path (not /admin/osticket and not /scp) to /admin/osticket/path
    html = re.sub(r'(href|src)="(?!/admin/osticket)(/[^"]*)"',
                   lambda m: f'{m.group(1)}="/admin/osticket{m.group(2)}"',
                   html)

    # Clean up any double slashes in paths (except in https://)
    html = re.sub(r'([^:])//+', r'\1/', html)

    # Inject JavaScript to intercept AJAX/fetch requests and rewrite URLs
    js_intercept = """
    <script>
    (function() {
        // Intercept XMLHttpRequest
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            if (typeof url === 'string') {
                // Convert real URLs to proxy URLs
                url = url.replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/');
                url = url.replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                // Clean up double slashes
                url = url.replace(/([^:])\/+/g, '$1/');
            }
            return originalOpen.apply(this, [method, url, ...args]);
        };

        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = function(resource, config) {
            if (typeof resource === 'string') {
                resource = resource.replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/');
                resource = resource.replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                // Clean up double slashes
                resource = resource.replace(/([^:])\/+/g, '$1/');
            }
            return originalFetch.apply(this, [resource, config]);
        };

        // Intercept jQuery AJAX if it exists
        if (window.jQuery && window.jQuery.ajax) {
            const originalAjax = window.jQuery.ajax;
            window.jQuery.ajax = function(settings) {
                if (settings && settings.url) {
                    settings.url = settings.url.replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/');
                    settings.url = settings.url.replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                    // Clean up double slashes
                    settings.url = settings.url.replace(/([^:])\/+/g, '$1/');
                }
                return originalAjax.apply(this, [settings]);
            };
        }
    })();
    </script>
    """

    # Inject before closing body tag or at end
    if '</body>' in html:
        html = html.replace('</body>', js_intercept + '</body>')
    else:
        html = html + js_intercept

    return html


@app.route("/", methods=["GET"])
def index():
    html = """
    <html>
    <head>
      <title>Interactive Proxy (Flask)</title>
      <meta charset="utf-8" />
    </head>
    <body style='font-family:Arial,sans-serif; padding:30px;'>
      <h2>OSTicket Flask Proxy</h2>
      <p>Proxy Status: <strong style="color: green;">✓ Running on port 8001</strong></p>
      <p>Real OSTicket: https://oliverenterprises.app.saasify.cloud/scp/</p>
      <p>Proxy Path: /admin/osticket/</p>

      <div style="margin-bottom:12px;">
        <button id="load_btn" type="button" style="font-size:16px;padding:10px 18px;background:#007bff;color:#fff;border:none;border-radius:6px;" onclick="window.location='/admin/osticket/login.php';">Load OSTicket Login</button>
      </div>

      <div style="margin-top: 30px; padding: 15px; background: #f5f5f5; border-radius: 4px;">
        <h3>Debugging Info:</h3>
        <ul>
          <li>To access from Django: http://127.0.0.1:8001/admin/osticket/</li>
          <li>Direct test: Click "Load OSTicket Login" button above</li>
          <li>Check browser console for any errors</li>
        </ul>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/admin/osticket/", defaults={'path': ''})
@app.route("/admin/osticket/<path:path>", methods=["GET", "POST"])
def osticket_proxy(path):
    """Direct proxy for /admin/osticket/ paths."""
    # Normalize path - remove any double slashes or scp/ prefixes
    if path.startswith("scp/"):
        path = path[4:]  # Remove "scp/" prefix

    # Clean up path
    path = path.lstrip('/')

    # Build the real URL - ensure no double slashes
    target = REAL_BASE.rstrip('/') + '/' + path if path else REAL_BASE.rstrip('/') + '/'

    client_id = request.remote_addr

    # Get or create session for this client
    if client_id not in _session_store:
        _session_store[client_id] = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        _session_store[client_id].mount('http://', adapter)
        _session_store[client_id].mount('https://', adapter)

    sess = _session_store[client_id]

    try:
        if request.method == "POST":
            resp = sess.post(target, data=request.form, timeout=15, allow_redirects=False)
        else:
            resp = sess.get(target, timeout=15, allow_redirects=False)
    except Exception as e:
        return Response(f"Error: {e}", status=502)

    # Handle redirects manually to rewrite Location header
    if resp.status_code in [301, 302, 303, 307, 308]:
        location = resp.headers.get('Location', '')
        if location:
            # Convert real domain redirects to proxy paths
            location = location.replace("https://oliverenterprises.app.saasify.cloud/scp/", "/admin/osticket/")
            location = location.replace("https://oliverenterprises.app.saasify.cloud", "/admin/osticket")
            # Clean up double slashes in path
            while '//' in location:
                location = location.replace('//', '/')
            # Return redirect to proxy path
            return Response(f"Redirecting to {location}", status=resp.status_code, headers={'Location': location})

    ctype = resp.headers.get("content-type", "")
    if "html" in ctype:
        # Doseify the HTML: replace real URLs with proxy paths
        doseified = doseify_html(resp.text)
        return Response(doseified, content_type="text/html; charset=utf-8")
    else:
        return Response(resp.content, content_type=ctype)


def run(host="127.0.0.1", port=8001):
    """Start the Flask proxy server."""
    app.run(host=host, port=port)


if __name__ == "__main__":
    run()
