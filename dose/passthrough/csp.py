def apply_nextcloud_csp_nuke(response):
    """
    FINAL, NUCLEAR CSP — kills every single CSP header Nextcloud sends.
    This is the one that actually works — no more white screen.
    """
    # Delete EVERY possible CSP header — Nextcloud uses multiple
    csp_headers = [
        'Content-Security-Policy',
        'Content-Security-Policy-Report-Only',
        'X-Content-Security-Policy',
        'X-WebKit-CSP',
        'Report-To',
        'Reporting-Endpoints'
    ]
    for header in csp_headers:
        response.pop(header, None)

    # THE ONE TRUE CSP THAT WINS
    response['Content-Security-Policy'] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob: ws: wss:; "
        "script-src * 'unsafe-inline' 'unsafe-eval' 'strict-dynamic' blob: wasm-unsafe-eval; "
        "style-src * 'unsafe-inline' 'unsafe-eval' https: http: data:; "
        "font-src * data: https: http:; "
        "img-src * data: data: blob:; "
        "connect-src * ws: wss:; "
        "frame-src *; "
        "frame-ancestors *; "
        "media-src * data: blob:; "
        "worker-src * blob: data:; "
        "child-src * blob: data:; "
        "form-action *; "
        "base-uri *; "
        "manifest-src *;"
    )