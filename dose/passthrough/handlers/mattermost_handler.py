# dose/passthrough/handlers/mattermost_handler.py
"""
MATTERMOST PASSTHROUGH HANDLER
===============================

Session: May 24, 2026 Morning

What we accomplished:
---------------------
1. Aggressive CSP removal - Upstream CSP was blocking everything.
2. Header sanitization - Removed X-Frame-Options, X-Content-Type-Options, etc.
3. Broad URL rewriting - Critical for Mattermost's heavy code-splitting.
4. Dynamic chunk routing - Main bundle + hundreds of /static/XXXX.js chunks now route through proxy.
5. Permissive CSP injection on every response.

Current State:
--------------
- Main HTML loads correctly
- Main JS bundle loads correctly
- Most dynamic chunks now route through /pt/... (major win)
- Still occasional 502 when upstream Render instance is asleep

What remains:
-------------
- Occasional upstream 502 (Render free tier sleeps) → User must wake it up
- Very rare edge case chunks that might still slip through regex
- Long-term: Consider implementing a global static file proxy fallback in PT core

"""

import re

class MattermostPassthroughHandler:
    UPSTREAM = "https://polysaas-mattermost.onrender.com"
    PROXY_PREFIX = "/pt/admin/polysaas-mattermost.onrender.com"

    def process_response_headers(self, headers, request):
        """
        Nuclear header cleanup - removes all security restrictions from upstream.
        """
        for key in list(headers.keys()):
            lower = key.lower()
            if any(x in lower for x in [
                'content-security-policy', 
                'x-frame', 
                'frame-options', 
                'x-content-type-options',
                'cross-origin'
            ]):
                print(f"[MM] 🔥 REMOVED restrictive header: {key}")
                del headers[key]

        # Our own extremely permissive policy
        headers['Content-Security-Policy'] = (
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob: ws: wss:; "
            "script-src * 'unsafe-inline' 'unsafe-eval'; "
            "style-src * 'unsafe-inline'; "
            "img-src * data: blob:; "
            "connect-src * ws: wss:; "
            "frame-ancestors *;"
        )
        headers['X-Frame-Options'] = "ALLOWALL"
        headers['Access-Control-Allow-Origin'] = "*"
        
        return headers

    def process_html_response(self, response_content, request, endpoint=None, endpoint_url=None):
        """
        Rewrites all asset URLs so Mattermost's dynamic chunks go through our proxy.
        """
        if isinstance(response_content, bytes):
            html = response_content.decode('utf-8', errors='replace')
        else:
            html = str(response_content)

        print(f"[MM] Rewriting HTML - Original size: {len(html)}")

        # Core fix: Rewrite ALL /static/ paths (this was the main blocker)
        html = re.sub(
            r'(["\'])/static/([^"\']+)', 
            lambda m: f'{m.group(1)}{self.PROXY_PREFIX}/static/{m.group(2)}', 
            html
        )

        # Additional safety net for other root-relative assets
        html = re.sub(
            r'(["\'])/(plugins|images|fonts|api|manifest)/([^"\']+)', 
            lambda m: f'{m.group(1)}{self.PROXY_PREFIX}/{m.group(2)}/{m.group(3)}', 
            html
        )

        print(f"[MM] Final HTML size: {len(html)}")
        return html