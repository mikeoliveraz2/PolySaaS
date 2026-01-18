def apply_nextcloud_csp_nuke(response):
    if response.headers.get('Content-Security-Policy'):
        response.headers.pop('Content-Security-Policy')
    if response.headers.get('Content-Security-Policy-Report-Only'):
        response.headers.pop('Content-Security-Policy-Report-Only')
    response.headers['Content-Security-Policy'] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
        "script-src * 'unsafe-inline' 'unsafe-eval' blob:; "
        "style-src * 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src * data: https://fonts.gstatic.com; "
        "img-src * data: blob:; "
        "connect-src * ws: wss:; "
        "frame-ancestors *;"
    )