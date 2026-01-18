# polysniffer_standalone.py

# Double-click to run — captures full login POST + cookies + headers

# Saves everything to ./captures/ as perfect JSON

from flask import Flask, request, render_template_string, jsonify
import webbrowser
import threading
import json
import os
import glob
from datetime import datetime

app = Flask(__name__)
os.makedirs("captures", exist_ok=True)

# Enable CORS - allow HTTPS pages to POST to localhost:5001
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

CAPTURED = {}

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>PolySniffer – Redirecting...</title>
  <style>
    body { margin:0; font-family:system-ui; background:#111; color:#0f0; padding:40px; text-align:center; }
    .info { background:#222; padding:30px; border-radius:8px; max-width:700px; margin:50px auto; }
    .button { background:#0f0; color:#000; padding:15px 30px; border:none; border-radius:4px; cursor:pointer; font-weight:bold; font-size:16px; margin:10px; }
    code { background:#333; padding:5px 10px; border-radius:3px; display:block; margin:10px 0; word-break:break-all; }
  </style>
</head>
<body>
  <div class="info">
    <h1>🔍 PolySniffer</h1>
    <p><strong>Redirecting to target site...</strong></p>
    <p style="color:#ff0; margin:20px 0;">
      <strong>📋 Instructions:</strong><br>
      1. Log in to the target site (will open in 2 seconds)<br>
      2. Open browser DevTools (F12)<br>
      3. Go to <strong>Network</strong> tab<br>
      4. Find the <strong>login POST</strong> request<br>
      5. Right-click → <strong>Copy → Copy as cURL</strong><br>
      6. Paste the cURL command below or save manually
    </p>
    <p style="color:#0ff; margin-top:20px;">
      <strong>💡 Quick Capture:</strong> After logging in, come back here and paste the POST data below.
    </p>
    <textarea id="postData" placeholder="Paste cURL command or POST data here..." style="width:100%; height:100px; background:#333; color:#0f0; border:1px solid #0f0; padding:10px; margin:10px 0; font-family:monospace;"></textarea>
    <button class="button" onclick="saveManual()">💾 Save Capture</button>
    <button class="button" onclick="window.location.href='{{ url }}'">🚀 Go to Target Site Now</button>
    <button class="button" onclick="window.close()">❌ Close</button>
  </div>

  <script>
    const targetUrl = "{{ url }}";
    const tenant = "{{ tenant }}";
    const endpoint = "{{ endpoint }}";

    // Auto-redirect after 2 seconds
    setTimeout(() => {
      window.location.href = targetUrl;
    }, 2000);

    function saveManual() {
      const postData = document.getElementById("postData").value;
      if (!postData) {
        alert("Please paste the POST data or cURL command first.");
        return;
      }

      fetch("/save?tenant=" + tenant + "&endpoint=" + endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          post: { manual_capture: postData },
          cookies: document.cookie || "N/A (cross-origin)",
          final_url: targetUrl,
          capture_method: "manual"
        })
      }).then(r => r.json()).then(data => {
        alert("✅ Capture saved! Check the captures folder.");
        document.getElementById("postData").value = "";
      }).catch(e => {
        alert("Error saving: " + e.message);
      });
    }
  </script>
</body>
</html>
"""

@app.route("/test")
def test():
    """Test endpoint to verify server is running"""
    return jsonify({
        "status": "PolySniffer is running",
        "timestamp": datetime.now().isoformat(),
        "captures_dir": os.path.abspath("captures"),
        "captures_count": len(glob.glob("captures/*.json")) if os.path.exists("captures") else 0
    })

@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PolySniffer</title>
        <style>
            body { font-family:system-ui; background:#111; color:#0f0; padding:40px; max-width:800px; margin:0 auto; }
            .bookmarklet { background:#0f0; color:#000; padding:15px; border-radius:4px; margin:20px 0; }
            code { background:#333; padding:10px; display:block; margin:10px 0; word-break:break-all; }
        </style>
    </head>
    <body>
        <h1>🔍 PolySniffer</h1>
        <p>Standalone HTTP Traffic Capture Service</p>
        <div class="bookmarklet">
            <h3>📌 Bookmarklet for Automatic Capture</h3>
            <p>Drag this button to your bookmarks bar, then click it on any page to capture POST data:</p>
            <a href="javascript:(function(){var s=document.createElement('script');s.src='http://localhost:5001/bookmarklet.js';document.body.appendChild(s);})();" style="background:#000;color:#0f0;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">🔍 Capture POST (CSP-Proof)</a>
            <p style="font-size:12px;margin-top:10px;">Or use: <code>/capture?url=...</code></p>
        </div>
    </body>
    </html>
    """)

@app.route("/capture")
def capture():
    """Inject capture script on target domain via meta refresh - NO IFRAME"""
    url = request.args.get("url")
    tenant = request.args.get("tenant", "unknown")
    endpoint = request.args.get("endpoint", "unknown")

    if not url:
        return "No url provided", 400

    # This injects our capture script on the REAL domain – no iframe, no CSP problems
    js = f"""
    <script>
    const save = (data) => fetch("http://localhost:5001/save?tenant={tenant}&endpoint={endpoint}", {{
        method:"POST",
        body:JSON.stringify(data),
        headers:{{"Content-Type":"application/json"}},
        keepalive:true
    }});

    const originalFetch = window.fetch;

    window.fetch = async (...a) => {{
      const [r, o] = a;
      if (o && o.method === "POST") {{
        save({{
            type:"fetch",
            url:r.url||r,
            body:o.body,
            headers:o.headers,
            method:o.method
        }});
      }}
      return originalFetch(...a);
    }};

    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url) {{
      this._method = method;
      this._url = url;
      originalXHROpen.apply(this, arguments);
    }};

    XMLHttpRequest.prototype.send = function(body) {{
      if (this._method === "POST") {{
        save({{
            type:"xhr",
            url:this._url,
            body:body,
            method:this._method
        }});
      }}
      originalXHRSend.apply(this, arguments);
    }};

    window.addEventListener("unload", () => {{
      navigator.sendBeacon && navigator.sendBeacon(
        "http://localhost:5001/save?tenant={tenant}&endpoint={endpoint}",
        JSON.stringify({{
            final_url:location.href,
            cookies:document.cookie,
            note:"page unload"
        }})
      );
    }});

    setTimeout(() => save({{
        cookies:document.cookie,
        final_url:location.href,
        note:"page loaded"
    }}), 1000);
    </script>
    <h1 style="position:fixed;top:0;left:0;right:0;background:#0f0;color:#000;padding:20px;text-align:center;z-index:99999;font-size:20px;margin:0;">
    ✓ PolySniffer ACTIVE – Log in normally, then close window when done
    </h1>
    """

    return f'<meta http-equiv="refresh" content="0;url={url}">{js}<noscript><meta http-equiv="refresh" content="0;url={url}"></noscript>'

@app.route("/save", methods=["POST", "OPTIONS", "GET"])
def save():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        print("✓ CORS preflight request received")
        return jsonify({"status": "ok"}), 200

    # Test endpoint
    if request.method == "GET":
        return jsonify({"status": "PolySniffer is running", "timestamp": datetime.now().isoformat()})

    print("\n" + "="*60)
    print(f"📥 REQUEST RECEIVED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Method: {request.method}")
    print(f"   Content-Type: {request.content_type}")
    print(f"   Content-Length: {request.content_length}")
    print(f"   Args: {dict(request.args)}")

    try:
        # Try to get JSON data
        if request.is_json:
            data = request.get_json() or {}
        else:
            # Try to parse raw body
            raw_data = request.get_data(as_text=True)
            print(f"   Raw body (first 200 chars): {raw_data[:200]}")
            try:
                data = json.loads(raw_data) if raw_data else {}
            except:
                data = {"raw_body": raw_data}

        tenant = request.args.get("tenant", "na")
        endpoint = request.args.get("endpoint", "na")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"captures/capture_{timestamp}_tenant-{tenant}_endpoint-{endpoint}.json"

        # Add server-side metadata
        data["_server_metadata"] = {
            "received_at": datetime.now().isoformat(),
            "tenant": tenant,
            "endpoint": endpoint,
            "filename": filename,
            "request_method": request.method,
            "content_type": request.content_type
        }

        # Ensure captures directory exists
        os.makedirs("captures", exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ CAPTURED → {filename}")
        print(f"   Cookies: {len(data.get('cookies', ''))} chars")
        print(f"   POST: {'Yes' if data.get('post') else 'No'}")
        print(f"   URL: {data.get('final_url', 'N/A')}")
        print("="*60 + "\n")

        # Return empty response for no-cors mode (browser won't read it anyway)
        return "", 200
    except Exception as e:
        print(f"\n❌ ERROR saving capture: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return "", 500

@app.route("/get-latest/<endpoint>")
def get_latest(endpoint):
    """Get latest capture for an endpoint"""
    import glob
    pattern = f"captures/capture_*_endpoint-{endpoint}.json"
    matches = glob.glob(pattern)
    if not matches:
        return jsonify({"error": "No capture found"}), 404
    latest = max(matches, key=os.path.getctime)
    with open(latest, "r") as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/bookmarklet.js")
def bookmarklet_js():
    """JavaScript for bookmarklet - CSP-proof capture script"""
    return """
    // CSP-proof capture script - works everywhere
    (function() {
        console.log("🔍 PolySniffer bookmarklet loaded!");

        const save = (data) => {
            console.log("🔍 PolySniffer: Attempting to save:", Object.keys(data));
            const url = "http://localhost:5001/save";

            // Try with no-cors first (silent, but should work)
            fetch(url, {
                method: "POST",
                body: JSON.stringify(data),
                headers: {"Content-Type":"application/json"},
                mode: "no-cors",
                keepalive: true
            }).then(() => {
                console.log("🔍 PolySniffer: Request sent (no-cors mode - can't read response)");
            }).catch(err => {
                console.error("🔍 PolySniffer: Fetch error:", err);
                // Fallback: try with sendBeacon
                if (navigator.sendBeacon) {
                    const blob = new Blob([JSON.stringify(data)], {type: 'application/json'});
                    navigator.sendBeacon(url, blob);
                    console.log("🔍 PolySniffer: Fallback to sendBeacon");
                }
            });
        };

        const of = window.fetch;
        window.fetch = async (...a) => {
            const [r, c] = a;
            if (c && c.method === "POST") {
                console.log("🔍 PolySniffer: Intercepted fetch POST:", r.url || r);
                save({type:"fetch", url:r.url||r, body:c.body});
            }
            return of(...a);
        };

        const ox = XMLHttpRequest.prototype.open;
        const os = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.open = function(m,u){
            this._m=m;
            this._u=u;
            ox.apply(this,arguments);
        };
        XMLHttpRequest.prototype.send = function(b){
            if(this._m==="POST") {
                console.log("🔍 PolySniffer: Intercepted XHR POST:", this._u);
                save({type:"xhr", url:this._u, body:b});
            }
            os.apply(this,arguments);
        };

        // Immediately save current state
        const initialData = {
            cookies: document.cookie,
            final_url: location.href,
            note: "CSP-proof capture - bookmarklet loaded",
            timestamp: new Date().toISOString()
        };

        console.log("🔍 PolySniffer: Saving initial state...");
        save(initialData);

        alert("✓ PolySniffer ACTIVE!\\n\\nCheck browser console (F12) for details.\\n\\nEverything will be captured automatically.");
    })();
    """, 200, {'Content-Type': 'application/javascript', 'Access-Control-Allow-Origin': '*'}

if __name__ == "__main__":
    print("🚀 PolySniffer Standalone LIVE on http://localhost:5001")
    print("   Open Dose → click Sniff → log in once → close window → check ./captures/")
    threading.Timer(1, lambda: webbrowser.open("http://localhost:5001")).start()
    app.run(port=5001, debug=False, threaded=True)
