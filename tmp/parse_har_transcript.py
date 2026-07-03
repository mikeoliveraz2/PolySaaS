import json
import sys
from collections import Counter
from urllib.parse import urlparse

path = r"C:\Users\MikeOliver\.cursor\projects\f-PolySaaS\agent-transcripts\7b2463c6-0436-4a6d-9095-63a3088809bc\7b2463c6-0436-4a6d-9095-63a3088809bc.jsonl"
har_lines = []
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        if '"log"' in line and "entries" in line:
            har_lines.append(line)
har_text = har_lines[-1] if har_lines else None
print(f"Found {len(har_lines)} HAR-like lines, using last")

if not har_text:
    print("No HAR found")
    sys.exit(1)

idx = har_text.find('{"log"')
raw = har_text[idx:]
data = None
for end in range(len(raw), 100, -1):
    try:
        data = json.loads(raw[:end])
        break
    except Exception:
        pass

if not data:
    print("parse failed")
    sys.exit(1)

entries = data["log"]["entries"]
pages = data["log"].get("pages", [])
print("Pages:", [(p.get("title"), p.get("startedDateTime")) for p in pages])
print("Total entries:", len(entries))

methods_urls = []
for e in entries:
    url = e["request"]["url"]
    method = e["request"]["method"]
    status = e["response"]["status"]
    rtype = e.get("_resourceType", "")
    t = e.get("time", 0)
    methods_urls.append((method, status, rtype, t, url))

print("\n=== DIRECT app.hubspot.com ===")
for m, s, rt, t, u in methods_urls:
    if "app.hubspot.com" in u and "localhost" not in u:
        print(f"{m} {s} {t:.0f}ms [{rt}] {u[:160]}")

print("\n=== workspace/home or pt/*/home ===")
for m, s, rt, t, u in methods_urls:
    if "/home" in u and ("workspace" in u or "/pt/" in u):
        print(f"{m} {s} {t:.0f}ms [{rt}] {u[:160]}")

print("\n=== portal API ===")
for m, s, rt, t, u in methods_urls:
    if "home/v2/api" in u or "no-intended-portal" in u:
        print(f"{m} {s} {t:.0f}ms [{rt}] {u[:160]}")

print("\n=== POST login ===")
for m, s, rt, t, u in methods_urls:
    if "login" in u.lower() and m == "POST":
        print(f"{m} {s} {t:.0f}ms [{rt}] {u[:160]}")

print("\n=== Document navigations ===")
for m, s, rt, t, u in methods_urls:
    if rt == "document":
        print(f"{m} {s} {t:.0f}ms {u[:160]}")

print("\n=== NotFoundLanding ===")
for m, s, rt, t, u in methods_urls:
    if "NotFound" in u or "notfound" in u.lower():
        print(f"{m} {s} {t:.0f}ms {u[:160]}")

print("\n=== firealarm ===")
for m, s, rt, t, u in methods_urls:
    if "firealarm" in u.lower():
        print(f"{m} {s} {t:.0f}ms {u[:160]}")

print("\n=== cartographer ===")
for m, s, rt, t, u in methods_urls:
    if "cartographer" in u.lower():
        print(f"{m} {s} {t:.0f}ms {u[:160]}")

hosts = Counter(urlparse(u).netloc for _, _, _, _, u in methods_urls)
print("\n=== Top hosts ===")
for h, c in hosts.most_common(12):
    print(c, h)
