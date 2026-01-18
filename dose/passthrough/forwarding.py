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
        # Special handling for PolySysMon: strip passthrough prefix
        full_path = request.get_full_path()
        polysysmon_prefixes = ["/pt/admin/polysysmon", "/pt/dose/polysysmon"]
        is_polysysmon = any(full_path.startswith(prefix) for prefix in polysysmon_prefixes)

        if is_polysysmon:
            for prefix in polysysmon_prefixes:
                if full_path.startswith(prefix):
                    # Always map to backend root: /pt/admin/polysysmon/login → /login
                    clean = full_path[len(prefix):]
                    if not clean or clean == "/":
                        clean = "/"
                    # Ensure clean always starts with /
                    if not clean.startswith("/"):
                        clean = "/" + clean
                    target_url = endpoint_url.rstrip("/") + clean
                    print(f"POLYSYSMON PASSTHROUGH → {full_path} → {target_url}")
                    break
        elif full_path in ("/pt/admin/nextcloud/", "/pt/dose/nextcloud/"):
            target_url = endpoint_url
            print(f"FIRST REQUEST → USING SACRED ENDPOINT: {target_url}")
        else:
            clean = full_path
            clean = clean.replace("/pt/admin/nextcloud", "", 1)
            clean = clean.replace("/pt/dose/nextcloud", "", 1)
            clean = clean.replace("/pt/admin/monitor-logger", "", 1)
            clean = clean.replace("/pt/dose/monitor-logger", "", 1)
            if not clean or clean == "/":
                clean = "/"
            target_url = endpoint_url.rstrip("/") + clean
            print(f"SUBSEQUENT REQUEST → CLEANED PATH: {clean}")
            print(f"                   → FINAL TARGET: {target_url}")

        print(f"SENDING REQUEST TO → {target_url}")

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

        print(f"EXTERNAL SERVICE RESPONDED → STATUS: {resp.status_code}")
        print(f"CONTENT LENGTH: {len(resp.content)} bytes")
        print(f"CONTENT PREVIEW: {resp.content[:500].decode('utf-8', errors='ignore')}")

        content = resp.content.decode('utf-8', errors='ignore')

        if handler:
            print(f"HANDLER RUNNING → {handler.__class__.__name__}")
            # Always pass endpoint_url for dynamic asset rewriting
            processed = handler.process_html_response(content, request, endpoint_url=endpoint_url)
            if isinstance(processed, HttpResponse):
                print("HANDLER RETURNED HttpResponse — RETURNING DIRECTLY")
                return processed
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