"""Extract and analyze a specific HAR line from agent transcript."""
import json
import re
import sys
from collections import Counter
from urllib.parse import urlparse

TRANSCRIPT = r"C:\Users\MikeOliver\.cursor\projects\f-PolySaaS\agent-transcripts\7b2463c6-0436-4a6d-9095-63a3088809bc\7b2463c6-0436-4a6d-9095-63a3088809bc.jsonl"


def extract_har_from_line(line: str) -> dict | None:
    # Message is JSON; inner text may contain escaped HAR
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    text = obj.get("message", {}).get("content", [{}])[0].get("text", "")
    # Find JSON object starting with { and "log"
    m = re.search(r'(\{\s*"log"\s*:\s*\{)', text)
    if not m:
        return None
    start = m.start(1)
    raw = text[start:]
    for end in range(len(raw), 100, -1):
        try:
            return json.loads(raw[:end])
        except json.JSONDecodeError:
            continue
    return None


def analyze(data: dict, label: str) -> None:
    entries = data["log"]["entries"]
    pages = data["log"].get("pages", [])
    print(f"\n{'='*70}\n{label}\n{'='*70}")
    print("Pages:", [(p.get("title"), p.get("startedDateTime")) for p in pages])
    print("Total entries:", len(entries))

    rows = []
    for e in entries:
        url = e["request"]["url"]
        method = e["request"]["method"]
        status = e["response"]["status"]
        rtype = e.get("_resourceType", "")
        t = e.get("time", 0)
        initiator = e.get("_initiator", {})
        rows.append((method, status, rtype, t, url, initiator))

    def show(title, pred):
        hits = [r for r in rows if pred(*r)]
        if hits:
            print(f"\n--- {title} ({len(hits)}) ---")
            for m, s, rt, t, u, init in hits[:25]:
                stack = init.get("stack", {}).get("callFrames", [{}])
                fn = stack[0].get("functionName", "") if stack else ""
                src = stack[0].get("url", "") if stack else ""
                extra = ""
                if fn or src:
                    extra = f" <- {fn} @ {src.split('/')[-1] if src else ''}"
                print(f"  {m} {s} {t:.0f}ms [{rt}] {u[:130]}{extra}")

    show("DOCUMENT navigations", lambda m, s, rt, t, u, i: rt == "document")
    show("app.hubspot.com (direct)", lambda m, s, rt, t, u, i: "app.hubspot.com" in u and "localhost" not in u)
    show("workspace/home", lambda m, s, rt, t, u, i: "workspace/home" in u or "/pt/" in u and "/home/" in u)
    show("portal API", lambda m, s, rt, t, u, i: "home/v2/api" in u or "no-intended-portal" in u)
    show("home-redirect-ui", lambda m, s, rt, t, u, i: "home-redirect-ui" in u)
    show("POST login", lambda m, s, rt, t, u, i: m == "POST" and "login" in u.lower())
    show("Location redirects (3xx)", lambda m, s, rt, t, u, i: 300 <= s < 400)

    hosts = Counter(urlparse(u).netloc for _, _, _, _, u, _ in rows)
    print("\n--- Top hosts ---")
    for h, c in hosts.most_common(10):
        print(f"  {c:4d}  {h}")


def main():
    line_nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [411, 451, 517]
    with open(TRANSCRIPT, "r", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if n not in line_nums:
                continue
            data = extract_har_from_line(line)
            if data:
                analyze(data, f"Line {n}")
            else:
                print(f"Line {n}: no HAR parsed")


if __name__ == "__main__":
    main()
