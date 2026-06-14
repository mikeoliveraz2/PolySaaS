"""Compare Team Not Found vs Bingo HARs from transcript."""
import json
import re
from pathlib import Path

path = Path(
    r"C:\Users\MikeOliver\.cursor\projects\f-PolySaaS\agent-transcripts"
    r"\4ac14280-9adf-4d56-9b3f-43cb9d50c435\4ac14280-9adf-4d56-9b3f-43cb9d50c435.jsonl"
)
hars = {}
with open(path, encoding="utf-8") as f:
    for line in f:
        if "here is the har for the Team not found" in line:
            hars["notfound"] = json.loads(line[line.index("{") :])
        elif "here is the bingo har" in line:
            hars["bingo"] = json.loads(line[line.index("{") :])


def cache_info(e):
    c = e.get("cache") or {}
    return {
        "fromCache": bool(e.get("_fromCache")),
        "disk": bool(c.get("fromDiskCache")),
        "sw": bool(c.get("fromServiceWorker")),
        "status": e["response"]["status"],
        "cc": next(
            (
                h["value"]
                for h in e["response"].get("headers", [])
                if h["name"].lower() == "cache-control"
            ),
            "",
        ),
    }


def summarize(name, har):
    entries = har["log"]["entries"]
    print(f"=== {name}: {len(entries)} entries ===")
    cached = [e for e in entries if cache_info(e)["fromCache"] or cache_info(e)["disk"]]
    print(f"  cached (fromCache/disk): {len(cached)}")
    for e in cached:
        ci = cache_info(e)
        url = e["request"]["url"]
        print(f"    {ci['status']} disk={ci['disk']} cache={ci['fromCache']} cc={ci['cc'][:60]}")
        print(f"      {url[:160]}")
    return entries


nf = summarize("NOT FOUND", hars["notfound"])
bg = summarize("BINGO", hars["bingo"])

nf_urls = {e["request"]["url"] for e in nf}
bg_urls = {e["request"]["url"] for e in bg}
print(f"\nURLs only in NOT FOUND ({len(nf_urls - bg_urls)}):")
for u in sorted(nf_urls - bg_urls)[:30]:
    print(f"  {u[:160]}")
print(f"\nURLs only in BINGO ({len(bg_urls - nf_urls)}):")
for u in sorted(bg_urls - nf_urls)[:30]:
    print(f"  {u[:160]}")

nm = {e["request"]["url"]: cache_info(e) for e in nf}
bm = {e["request"]["url"]: cache_info(e) for e in bg}
print("\nSame URL, different cache behavior:")
for url in sorted(set(nm) & set(bm)):
    if nm[url] != bm[url]:
        print(f"  {url[:140]}")
        print(f"    NOT FOUND: {nm[url]}")
        print(f"    BINGO:     {bm[url]}")
