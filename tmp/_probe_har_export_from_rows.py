"""Build the HAR the Export HAR button would produce for the newest capture."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.db import connection

with connection.cursor() as cur:
    cur.execute('SET search_path TO "olient",public;')

from dose.polysniffer.models import TrafficCapture, TrafficLog

cap = TrafficCapture.objects.order_by("-id").first()
rows = TrafficLog.objects.filter(capture_session=cap).order_by("captured_at")
entries = []
failed = 0
for log in rows:
    try:
        if log.har_data and log.har_data.get("log", {}).get("entries"):
            entries.extend(log.har_data["log"]["entries"])
        else:
            entries.append(log.to_har_entry())
    except Exception as exc:
        failed += 1
        print(f"  entry failed for {log.url[:70]}: {exc}")

har = {
    "log": {
        "version": "1.2",
        "creator": {"name": "PolySniffer", "version": "2.0"},
        "entries": entries,
    }
}
blob = json.dumps(har, indent=2)
print(f"capture={cap.id} name={cap.capture_name}")
print(f"rows={rows.count()} entries={len(entries)} failed={failed} har_bytes={len(blob)}")
if entries:
    e = entries[0]
    print("\nfirst entry keys:", sorted(e.keys()))
    print("  request:", e.get("request", {}).get("method"), e.get("request", {}).get("url", "")[:90])
    print("  status:", e.get("response", {}).get("status"))
    print("  req header count:", len(e.get("request", {}).get("headers", [])))
    print("  res header count:", len(e.get("response", {}).get("headers", [])))
    print("  cookies:", len(e.get("request", {}).get("cookies", [])))
    body = e.get("response", {}).get("content", {})
    print("  response content size:", body.get("size"), "mime:", body.get("mimeType"))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_native_export_check.har")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(blob)
print("\nwrote", out)
