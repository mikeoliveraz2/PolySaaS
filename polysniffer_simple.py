# polysniffer_simple.py - No Flask, just works
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import time

# Track start time for run duration logging
start_time = time.time()

# Save to polysniffer_service/captures to match Django's expectations
# polysniffer_simple.py is in root, so polysniffer_service is a sibling directory
CAPTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "polysniffer_service", "captures")
os.makedirs(CAPTURE_DIR, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/save'):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            data = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            if not data:
                data = {"ping": "pong"}

            filename = os.path.join(CAPTURE_DIR, f"capture_{datetime.now():%Y-%m-%d_%H-%M-%S}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"\nCAPTURED (GET) → {filename}\n")

            # Log the PolySniffer run
            try:
                # Import Django models for logging
                import django
                from django.conf import settings
                if not settings.configured:
                    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
                    django.setup()

                from dose.models import PolySnifferRun

                # Get current tenant (if available)
                tenant = None
                try:
                    from dose.utils import get_current_tenant
                    # For now, we'll use None since we don't have request context
                    # tenant = get_current_tenant()  # Would need request object
                except:
                    pass

                run_record = PolySnifferRun.objects.create(
                    tenant=tenant,
                    run_timestamp=datetime.now(),
                    status="completed",
                    packets_captured=1,  # Each capture is one "packet"
                    notes=f"PolySniffer capture completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    raw_data_summary=json.dumps({
                        "method": "GET",
                        "endpoint": "unknown",
                        "data_keys": list(data.keys()) if data else [],
                        "run_duration_seconds": time.time() - start_time,
                        "capture_time": datetime.now().isoformat()
                    })[:1000]
                )
                print(f"PolySniffer run logged → ID: {run_record.id} at {run_record.run_timestamp}")
            except Exception as e:
                print(f"Failed to save PolySniffer run log: {e}")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "saved", "file": filename}).encode())
        elif self.path == '/bookmarklet.js':
            # Serve the bookmarklet JavaScript
            bookmarklet_js = """
// PolySniffer Bookmarklet - CSP-proof capture
(function() {
    console.log("🔍 PolySniffer bookmarklet loaded!");

    const save = (data) => {
        console.log("🔍 PolySniffer: Saving data...", Object.keys(data));
        const url = "http://127.0.0.1:5002/save";

        // Extract endpoint ID from URL if present
        const urlParams = new URLSearchParams(window.location.search);
        const endpointId = urlParams.get('endpoint') || 'unknown';
        const tenantId = urlParams.get('tenant') || 'unknown';

        const fullData = {
            ...data,
            endpoint_id: endpointId,
            tenant_id: tenantId,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };

        // Use sendBeacon for reliability (works even if page closes)
        if (navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(fullData)], {type: 'application/json'});
            if (navigator.sendBeacon(url, blob)) {
                console.log("🔍 PolySniffer: Data sent via sendBeacon");
                alert("✓ CAPTURED!\\n\\nCheck the captures folder and click 'Apply Latest Capture' in Dose admin.");
                return;
            }
        }

        // Fallback to fetch
        fetch(url, {
            method: "POST",
            body: JSON.stringify(fullData),
            headers: {"Content-Type": "application/json"},
            mode: "no-cors",
            keepalive: true
        }).then(() => {
            console.log("🔍 PolySniffer: Data sent via fetch");
            alert("✓ CAPTURED!\\n\\nCheck the captures folder and click 'Apply Latest Capture' in Dose admin.");
        }).catch(err => {
            console.error("🔍 PolySniffer: Error:", err);
            alert("⚠ Error sending capture. Check console (F12) for details.");
        });
    };

    // Capture current page state
    const captureData = {
        cookies: document.cookie,
        final_url: window.location.href,
        title: document.title,
        note: "Bookmarklet capture - manual trigger"
    };

    // Try to find any form data on the page
    const forms = document.querySelectorAll('form');
    if (forms.length > 0) {
        captureData.forms = Array.from(forms).map(form => ({
            action: form.action,
            method: form.method,
            inputs: Array.from(form.querySelectorAll('input, select, textarea')).map(input => ({
                name: input.name,
                type: input.type,
                value: input.value ? input.value.substring(0, 100) : '' // Truncate for security
            }))
        }));
    }

    console.log("🔍 PolySniffer: Capturing current state...");
    save(captureData);
})();
"""
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(bookmarklet_js.encode())
        elif self.path == '/':
            # Serve the bookmarklet page
            html = """<!DOCTYPE html>
<html>
<head>
    <title>PolySniffer</title>
    <style>
        body { font-family:system-ui; background:#111; color:#0f0; padding:40px; max-width:800px; margin:0 auto; }
        .bookmarklet { background:#0f0; color:#000; padding:20px; border-radius:4px; margin:20px 0; text-align:center; }
        .bookmarklet a { background:#000; color:#0f0; padding:15px 30px; text-decoration:none; border-radius:4px; display:inline-block; font-weight:bold; font-size:18px; }
        .bookmarklet a:hover { background:#0f0; color:#000; }
        code { background:#333; padding:10px; display:block; margin:10px 0; word-break:break-all; }
        .instructions { background:#222; padding:20px; border-radius:4px; margin:20px 0; }
    </style>
</head>
<body>
    <h1>🔍 PolySniffer</h1>
    <p>Standalone HTTP Traffic Capture Service</p>

    <div class="bookmarklet">
        <h3>📌 Drag This Button to Your Bookmarks Bar</h3>
        <a href="javascript:(function(){var s=document.createElement('script');s.src='http://127.0.0.1:5002/bookmarklet.js';document.body.appendChild(s);})();">🔍 Capture POST</a>
        <p style="font-size:14px; margin-top:15px;">Then click it on any page to capture cookies and form data</p>
    </div>

    <div class="instructions">
        <h3>📋 How to Use:</h3>
        <ol>
            <li>Drag the "🔍 Capture POST" button above to your bookmarks bar</li>
            <li>Go to your OS Ticket login page (or any page you want to capture)</li>
            <li>Log in normally</li>
            <li>Once on the dashboard, click the "🔍 Capture POST" bookmarklet</li>
            <li>You'll see "✓ CAPTURED!" alert</li>
            <li>Go back to Dose admin and click "Apply Latest Capture"</li>
        </ol>
    </div>

    <div style="margin-top:30px; padding:15px; background:#222; border-radius:4px;">
        <strong>Status:</strong> <span style="color:#0f0;">✓ Running on http://127.0.0.1:5002</span><br>
        <strong>Captures folder:</strong> <code>captures/</code>
    </div>
</body>
</html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/save'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

            try:
                data = json.loads(body) if body else {}
            except:
                data = {"raw_body": body}

            # Extract endpoint/tenant from query string or data
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            endpoint_id = params.get('endpoint', [data.get('endpoint_id', 'unknown')])[0]
            tenant_id = params.get('tenant', [data.get('tenant_id', 'unknown')])[0]

            # Include in filename for easy lookup
            filename = os.path.join(CAPTURE_DIR, f"capture_{datetime.now():%Y-%m-%d_%H-%M-%S}_endpoint-{endpoint_id}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ CAPTURED (POST) → {filename}")
            print(f"  Endpoint: {endpoint_id}, Tenant: {tenant_id}\n")

            # Log the PolySniffer run
            try:
                # Import Django models for logging
                import django
                from django.conf import settings
                if not settings.configured:
                    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
                    django.setup()

                from dose.models import PolySnifferRun

                # Get current tenant (if available)
                tenant = None
                try:
                    from dose.utils import get_current_tenant
                    # For now, we'll use None since we don't have request context
                    # tenant = get_current_tenant()  # Would need request object
                except:
                    pass

                run_record = PolySnifferRun.objects.create(
                    tenant=tenant,
                    run_timestamp=datetime.now(),
                    status="completed",
                    packets_captured=1,  # Each capture is one "packet"
                    notes=f"PolySniffer capture completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    raw_data_summary=json.dumps({
                        "method": "POST",
                        "endpoint": endpoint_id,
                        "tenant": tenant_id,
                        "data_keys": list(data.keys()) if data else [],
                        "run_duration_seconds": time.time() - start_time,
                        "capture_time": datetime.now().isoformat()
                    })[:1000]
                )
                print(f"PolySniffer run logged → ID: {run_record.id} at {run_record.run_timestamp}")
            except Exception as e:
                print(f"Failed to save PolySniffer run log: {e}")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "saved", "file": filename}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == "__main__":
    print("\nPolySniffer SIMPLE – listening on http://127.0.0.1:5002")
    print("Test now: http://127.0.0.1:5002/save?test=hello\n")
    server = HTTPServer(('127.0.0.1', 5002), Handler)
    server.serve_forever()

