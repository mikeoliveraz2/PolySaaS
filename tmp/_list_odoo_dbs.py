"""List Odoo databases on localhost:8086. No passwords printed."""
import json
import requests

url = "http://localhost:8086/jsonrpc"
payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {"service": "db", "method": "list", "args": []},
    "id": 1,
}
r = requests.post(url, json=payload, timeout=10)
print("http", r.status_code)
try:
    data = r.json()
except Exception:
    print("body_prefix", r.text[:200])
else:
    err = data.get("error")
    if err:
        msg = err.get("message") if isinstance(err, dict) else err
        print("rpc_error", msg)
    print("dbs", data.get("result"))
