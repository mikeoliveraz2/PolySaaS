# polysniffer_works.py — the one that actually writes files

from flask import Flask, request, jsonify, Response
import json, os
from datetime import datetime

app = Flask(__name__)
# Disable Flask's automatic JSON parsing
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

os.makedirs("captures", exist_ok=True)

# Enable CORS for all routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route("/")
def index():
    return "<h1>PolySniffer READY — open Dose and click Sniff</h1>"

@app.route("/save", methods=["GET"])
def save_get():
    """Handle GET requests - NO JSON parsing at all"""
    # Get query parameters directly - no JSON involved
    data = {}
    for key, value in request.args.items():
        data[key] = value

    if not data:
        data = {"note": "empty test GET request"}

    data["_metadata"] = {
        "method": "GET",
        "timestamp": datetime.now().isoformat()
    }

    filename = f"captures/capture_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"CAPTURED (GET) → {filename}")

    # Return JSON response manually to avoid any parsing
    response_data = {"status": "saved", "file": filename}
    return Response(
        json.dumps(response_data),
        mimetype='application/json',
        status=200
    )

@app.route("/save", methods=["POST", "OPTIONS"])
def save_post():
    """Handle POST requests"""
    if request.method == "OPTIONS":
        return Response('{"status": "ok"}', mimetype='application/json', status=200)

    # Get raw body - don't use request.get_json() which requires Content-Type
    raw_data = request.get_data(as_text=True)
    data = None

    # Try to parse as JSON manually
    if raw_data:
        try:
            data = json.loads(raw_data)
        except:
            data = {"raw_body": raw_data}
    else:
        data = {"note": "empty POST request"}

    data["_metadata"] = {
        "method": "POST",
        "timestamp": datetime.now().isoformat(),
        "content_type": request.content_type or "N/A"
    }

    filename = f"captures/capture_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"CAPTURED (POST) → {filename}")

    response_data = {"status": "saved", "file": filename}
    return Response(
        json.dumps(response_data),
        mimetype='application/json',
        status=200
    )

if __name__ == "__main__":
    print("PolySniffer WORKS edition running on http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
