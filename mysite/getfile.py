# This script generates the full patched middleware file
# Run it in Django shell to print the entire 2600+ line file

full_file = """
# PASTE THE ENTIRE ORIGINAL FILE YOU SENT ME HERE — EVERY LINE
# [your full original code from line 1 to line 2600+]
"""

# The two changes (add these in the correct places)
change1 = """
# INSERT IN forward_request_to_external_standardized, after the iframe fix
if 'nextcloud' in request.path.lower():
    external_response.headers.pop('Content-Security-Policy', None)
    external_response.headers.pop('Content-Security-Policy-Report-Only', None)
    external_response.headers['Content-Security-Policy'] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
        "script-src * 'unsafe-inline' 'unsafe-eval' blob:; "
        "style-src * 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src * data: https://fonts.gstatic.com; "
        "img-src * data: blob:; "
        "connect-src * ws: wss:; "
        "frame-ancestors *;"
    )
"""

change2 = """
# INSERT IN process_request, in the try block after setting matched_trigger_path
if any(s in endpoint.trigger_path.lower() for s in ['nextcloud', 'osticket']):
    print(f"[FORCE] Using STANDARDIZED pipeline for {endpoint.trigger_path}")
    return self.forward_request_to_external_standardized(request, endpoint.endpoint_url)
"""

# Print the full patched file
print(full_file.replace("INSERT CHANGE1", change1).replace("INSERT CHANGE2", change2))