# Simple Port Manager Service (Flask)
# Provides unique port assignment and release for local services

from flask import Flask, request, jsonify
import threading
import json
import os

app = Flask(__name__)
PREASSIGNED_FILE = 'preassigned_ports.json'
PORT_FILE = 'assigned_ports.json'
PORT_RANGE = (5000, 5999)  # Change as needed
lock = threading.Lock()

def load_ports():
    # Load preassigned ports first
    preassigned = {}
    if os.path.exists(PORT_FILE):
        with open(PORT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_ports(ports):
    with open(PORT_FILE, 'w') as f:
        json.dump(ports, f, indent=2)

    assigned = {}
    if os.path.exists(PORT_FILE):
        with open(PORT_FILE, 'r') as f:
            assigned = json.load(f)
    # Merge preassigned and assigned (assigned wins if overlap)
    merged = {**preassigned, **assigned}
    # If merged differs from assigned, save it
    if merged != assigned:
        save_ports(merged)
    return merged

def find_next_port(assigned):
    for port in range(PORT_RANGE[0], PORT_RANGE[1]+1):
        if str(port) not in assigned:
            return port
    return None

@app.route('/request', methods=['POST'])
def request_port():
    data = request.get_json(force=True)
    service = data.get('service')
    if not service:
        return jsonify({'error': 'Missing service name'}), 400
    with lock:
        assigned = load_ports()
        # If already assigned, return existing
        for port, owner in assigned.items():
            if owner == service:
                return jsonify({'port': int(port), 'service': service})
        port = find_next_port(assigned)
        if not port:
            return jsonify({'error': 'No available ports'}), 503
        assigned[str(port)] = service
        save_ports(assigned)
        return jsonify({'port': port, 'service': service})

@app.route('/release', methods=['POST'])
def release_port():
    data = request.get_json(force=True)
    service = data.get('service')
    with lock:
        assigned = load_ports()
        to_remove = [p for p, s in assigned.items() if s == service]
        for p in to_remove:
            del assigned[p]
        save_ports(assigned)
    return jsonify({'released': to_remove})

@app.route('/list', methods=['GET'])
def list_ports():
    with lock:
        assigned = load_ports()
    return jsonify(assigned)

if __name__ == '__main__':
    app.run(port=4000, debug=True)
