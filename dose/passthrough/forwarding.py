# dose/passthrough/forwarding.py — FINAL — PRINTS EVERYTHING — EXCEPTIONS SHOW TRUTH
import logging
import traceback
import requests
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def forward_request_standardized(request, endpoint_url, handler=None):
    # PRINT EVERYTHING — ALWAYS — NO MERCY
    print("\n" + "="*120)
    print("FORWARDER (forward_request_standardized) CALLED")
    print(f"USER-CONFIGURED ENDPOINT: {endpoint_url}")
    print(f"INCOMING PATH         : {request.get_full_path()}")
    print(f"REQUEST METHOD        : {request.method}")
    print(f"USER                  : {request.user}")
    print(f"TENANT                : {getattr(request, 'tenant', 'None')}")
    print("="*120)

    try:
        full_path = request.get_full_path()

        # Generic prefix stripping: /pt/{admin|dose}/{trigger}/subpath -> /subpath
        import re
        prefix_match = re.match(r'^/pt/(?:admin|dose)/[^/]+(.*)$', full_path)
        if prefix_match:
            clean = prefix_match.group(1)
            if not clean or clean == "/":
                clean = "/"
            if not clean.startswith("/"):
                clean = "/" + clean
            target_url = endpoint_url.rstrip("/") + clean
            print(f"PASSTHROUGH -> {full_path} -> {target_url}")
        else:
            target_url = endpoint_url
            print(f"PASSTHROUGH -> USING ENDPOINT ROOT: {target_url}")

        print(f"SENDING REQUEST TO -> {target_url}")

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.META.items() if k.startswith("HTTP_") or k in ["CONTENT_TYPE", "CONTENT_LENGTH"]},
            data=request.body,
            cookies=request.COOKIES,
            allow_redirects=True,
            stream=False,
            timeout=30,
        )

        print(f"EXTERNAL SERVICE RESPONDED -> STATUS: {resp.status_code}")
        print(f"CONTENT LENGTH: {len(resp.content)} bytes")
        print(f"CONTENT PREVIEW: {resp.content[:500].decode('utf-8', errors='ignore')}")

        content = resp.content.decode('utf-8', errors='ignore')

        if handler:
            print(f"HANDLER RUNNING -> {handler.__class__.__name__}")
            processed = handler.process_html_response(content, request, endpoint_url=endpoint_url)
            if isinstance(processed, HttpResponse):
                print("HANDLER RETURNED HttpResponse — RETURNING DIRECTLY")
                return processed
            elif isinstance(processed, tuple):
                content = processed[0] if processed[0] else content
                print("HANDLER FINISHED (tuple) — CONTENT MODIFIED")
            else:
                content = processed
                print("HANDLER FINISHED — CONTENT MODIFIED")
        else:
            print("NO HANDLER — RETURNING RAW CONTENT")

        response = HttpResponse(content.encode('utf-8'), status=resp.status_code)
        response['Content-Type'] = 'text/html'
        response['Content-Encoding'] = 'identity'
        response['X-Frame-Options'] = 'ALLOWALL'

        print("FORWARDER SUCCESS — RESPONSE SENT TO BROWSER")
        print("="*120 + "\n")

        return response

    except Exception as e:
        # PRINT THE TRUTH — NEVER LIE
        tb = traceback.format_exc()
        print("\n" + "!"*120)
        print("FORWARDER FAILED — FULL TRUTH BELOW")
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION     : {e}")
        print(f"TARGET URL    : {target_url if 'target_url' in locals() else 'UNKNOWN'}")
        print("TRACEBACK:")
        print(tb)
        print("!"*120 + "\n")

        error_html = f"""
        <div style="padding:40px; font-family:monospace; background:#000; color:#0f0;">
          <h2>FORWARDING FAILED</h2>
          <p><strong>Target:</strong> {target_url if 'target_url' in locals() else 'UNKNOWN'}</p>
          <p><strong>Error:</strong> {e}</p>
          <pre>{tb}</pre>
        </div>
        """

        return HttpResponse(error_html, status=502)