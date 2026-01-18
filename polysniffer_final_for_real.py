# polysniffer_final_for_real.py — THIS ONE ACTUALLY WORKS

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

@app.route("/")
def home():
    return "<h1 style='color:lime;background:black;padding:50px'>PolySniffer IS RUNNING - Click Sniff in Dose</h1>"

# Separate route for GET - completely avoids any JSON parsing
@app.route("/save", methods=["GET"])
def save_get():
    """Handle GET requests - NO JSON PARSING"""
    data = {}
    for key, value in request.args.items():
        data[key] = value
    if not data:
        data = {"ping": "pong"}

    filename = os.path.join(CAPTURE_DIR, f"capture_{datetime.now():%Y-%m-%d_%H-%M-%S}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nCAPTURED (GET) → {filename}\n")

    response = jsonify({"status": "saved", "file": filename})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# Separate route for POST
@app.route("/save", methods=["POST", "OPTIONS"])
def save_post():
    """Handle POST requests"""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    # Get raw body first
    raw_data = request.get_data(as_text=True)
    data = None

    # Try to parse as JSON
    if raw_data:
        try:
            data = json.loads(raw_data)
        except:
            data = {"raw_body": raw_data}
    else:
        data = {"note": "empty POST request"}

    filename = os.path.join(CAPTURE_DIR, f"capture_{datetime.now():%Y-%m-%d_%H-%M-%S}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nCAPTURED (POST) → {filename}\n")

    response = jsonify({"status": "saved", "file": filename})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

if __name__ == "__main__":
    print("\nPolySniffer FINAL – listening on http://127.0.0.1:5002")
    print("Test now: http://127.0.0.1:5002/save?test=hello\n")
    app.run(host="127.0.0.1", port=5002)
