"""Parse latest HAR from transcript line 730."""
import json
import re
import sys

path = r"C:\Users\MikeOliver\.cursor\projects\f-PolySaaS\agent-transcripts\7b2463c6-0436-4a6d-9095-63a3088809bc\7b2463c6-0436-4a6d-9095-63a3088809bc.jsonl"

with open(path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

har_line = None
for line in reversed(lines):
    if "2026-07-01T23:40" in line and '"role":"user"' in line:
        har_line = line
        break

if not har_line:
    print("No matching HAR line")
    sys.exit(1)

obj = json.loads(har_line)
text = obj["message"]["content"][0]["text"]
start = text.find('{"log"')
if start < 0:
    start = text.find("{")
raw = text[start:]
try:
    har, _end = json.JSONDecoder().raw_decode(raw)
except json.JSONDecodeError:
    # Truncate at last balanced brace if transcript appended extra text
    depth = 0
    end = 0
    for i, ch in enumerate(raw):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
    har = json.loads(raw[:end])
entries = har["log"]["entries"]

print("=== HAR SUMMARY ===")
print("entries:", len(entries))
pages = har["log"].get("pages") or []
if pages:
    print("page:", pages[0].get("title", ""))
    print("started:", pages[0].get("startedDateTime", ""))

print("\n=== KEY REQUESTS ===")
interesting = (
    "sync-session",
    "/login/",
    "/home/",
    "workspace/login",
    "workspace/home",
    "polysniff/4",
)
for e in entries:
    url = e["request"]["url"]
    method = e["request"]["method"]
    status = e["response"]["status"]
    if not any(x in url for x in interesting):
        continue
    if any(x in url for x in (".woff", ".css", ".png", ".svg")) and "/login/" not in url:
        continue
    t = e.get("startedDateTime", "")[-12:]
    print(f"{t} {method:4} {status:3} {url[:130]}")

print("\n=== OVERLAY MARKERS IN HTML ===")
markers = [
    "Sign in on HubSpot.com",
    "direct-login overlay",
    "2026-07-02b-phase3",
    "2026-07-02a",
    "__psSyncHubspotSession",
    "ps-hs-email",
    "_tryProxyLogin",
    "Try passthrough login",
]
for e in entries:
    ct = next(
        (h["value"] for h in e["response"].get("headers", []) if h["name"].lower() == "content-type"),
        "",
    )
    if "text/html" not in ct.lower():
        continue
    body = (e["response"].get("content") or {}).get("text") or ""
    if not body:
        continue
    found = [m for m in markers if m in body]
    if found:
        print(e["request"]["url"][:100])
        print("  ->", found)

print("\n=== POST /login/ body sample ===")
for e in entries:
    if e["request"]["method"] == "POST" and "/login/" in e["request"]["url"]:
        pd = e["request"].get("postData") or {}
        txt = pd.get("text") or ""
        if txt:
            print(txt[:300])
