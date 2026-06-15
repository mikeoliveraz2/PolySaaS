"""One-off: compare Team Not Found vs Bingo HAR from transcript."""
import json
from pathlib import Path

path = Path(
    r"C:\Users\MikeOliver\.cursor\projects\f-PolySaaS\agent-transcripts"
    r"\4ac14280-9adf-4d56-9b3f-43cb9d50c435\4ac14280-9adf-4d56-9b3f-43cb9d50c435.jsonl"
)
hars = {}
with open(path, encoding="utf-8") as f:
    for line in f:
        if "here is the har for the Team not found" in line:
            key = "notfound"
        elif "here is the bingo har" in line:
            key = "bingo"
        else:
            continue
        if key in hars or len(line) < 500_000:
            continue
        obj = json.loads(line)
        text = obj["message"]["content"][0]["text"]
        # Strip <user_query> wrapper; HAR may be pretty-printed after the preamble.
        for marker in ('{"log"', '{ "log"'):
            idx = text.find(marker)
            if idx >= 0:
                break
        else:
            idx = text.find('"log":')
            if idx >= 0:
                idx = text.rfind("{", 0, idx)
        if idx < 0:
            raise SystemExit(f"no HAR JSON in {key}")
        decoder = json.JSONDecoder()
        hars[key], _end = decoder.raw_decode(text, idx)


def hdr(e, name):
    for h in e["response"].get("headers", []):
        if h["name"].lower() == name:
            return h["value"]
    return ""


def short(url, n=120):
    return url if len(url) <= n else url[: n - 3] + "..."


def analyze(name, har):
    entries = har["log"]["entries"]
    print(f"\n{'=' * 70}\n{name}: {len(entries)} entries\n{'=' * 70}")
    for e in entries:
        url = e["request"]["url"]
        if "config/client" not in url:
            continue
        print(f"\n>>> config/client")
        print(f"    URL: {url}")
        print(f"    Status: {e['response']['status']}")
        print(f"    Cache-Control: {hdr(e, 'cache-control') or '(missing)'}")
        print(f"    ETag: {hdr(e, 'etag') or '(missing)'}")
        print(f"    cache metadata: {e.get('cache')}")
        body = e["response"].get("content", {}).get("text", "")
        if body:
            try:
                data = json.loads(body)
                print(f"    SiteURL: {data.get('SiteURL', '(n/a)')}")
            except Exception:
                print(f"    body len: {len(body)}")

    # team-related API
    for e in entries:
        url = e["request"]["url"]
        if "/teams/name/" in url or "Team not found" in (e["response"].get("content", {}).get("text") or ""):
            print(f"\n>>> team-related: {e['response']['status']} {short(url)}")
            print(f"    Cache-Control: {hdr(e, 'cache-control') or '(missing)'}")

    # disk cache hints in HAR
    disk = []
    for e in entries:
        c = e.get("cache") or {}
        if c:
            disk.append((e["request"]["url"], c))
    print(f"\nEntries with non-empty cache metadata: {len(disk)}")
    for url, c in disk[:15]:
        print(f"  {short(url)} -> {c}")


for k in ("notfound", "bingo"):
    if k in hars:
        analyze(k.upper(), hars[k])
    else:
        print(f"MISSING: {k}")

# diff config/client headers only
if "notfound" in hars and "bingo" in hars:
    print(f"\n{'=' * 70}\nDIFF summary\n{'=' * 70}")
    for label, har in [("NOT FOUND", hars["notfound"]), ("BINGO", hars["bingo"])]:
        urls = {}
        for e in har["log"]["entries"]:
            u = e["request"]["url"]
            urls[u] = {
                "status": e["response"]["status"],
                "cc": hdr(e, "cache-control"),
                "type": e.get("_resourceType", ""),
            }
        print(f"\n{label}: unique URLs {len(urls)}")

    nf_set = {e["request"]["url"] for e in hars["notfound"]["log"]["entries"]}
    bg_set = {e["request"]["url"] for e in hars["bingo"]["log"]["entries"]}
    only_nf = nf_set - bg_set
    only_bg = bg_set - nf_set
    print(f"Only in NOT FOUND: {len(only_nf)}")
    for u in sorted(only_nf):
        if "localhost" in u or "polysaas-mattermost" in u:
            print(f"  {short(u, 140)}")
    print(f"Only in BINGO: {len(only_bg)}")
    for u in sorted(only_bg):
        if "localhost" in u or "polysaas-mattermost" in u:
            print(f"  {short(u, 140)}")

print(f"\n{'=' * 70}\nKEY RESPONSE BODIES\n{'=' * 70}")
for label, har in [("NOT FOUND", hars["notfound"]), ("BINGO", hars["bingo"])]:
    print(f"\n--- {label} ---")
    print(f"Page title: {har['log']['pages'][0]['title']}")
    for e in har["log"]["entries"]:
        url = e["request"]["url"]
        if "config/client" in url:
            raw = (e["response"].get("content") or {}).get("text") or ""
            if raw:
                data = json.loads(raw)
                print(f"config/client SiteURL: {data.get('SiteURL')}")
        if "/teams/name/" in url:
            slug = url.split("/teams/name/")[-1].split("?")[0]
            raw = (e["response"].get("content") or {}).get("text") or ""
            print(f"teams/name/{slug} -> HTTP {e['response']['status']}")
            if raw:
                print(f"  body preview: {raw[:200]}")
        if url.endswith("/api/v4/users/me/teams") or "/users/me/teams" in url and "?" not in url.split("/users/me/teams")[-1]:
            if "/users/me/teams/" not in url.replace("/users/me/teams", "", 1):
                raw = (e["response"].get("content") or {}).get("text") or ""
                print(f"users/me/teams -> HTTP {e['response']['status']} body_len={len(raw)}")
