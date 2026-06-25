#!/usr/bin/env python
"""
Compare HubSpot HAR files: direct vs native vs passthrough parity.

Usage:
  python scripts/compare_hubspot_har_parity.py direct.har native.har
  python scripts/compare_hubspot_har_parity.py direct.har native.har passthrough.har

Labels default to direct, native, passthrough when three files are given.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import urlparse


def load_har(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def norm_host(url: str) -> str:
    if not url or url.startswith("data:"):
        return "(data)"
    if url.startswith("/"):
        return "(relative)"
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else "?"


def norm_upstream_path(url: str) -> str:
    """Strip PolySaaS sniff/passthrough prefixes for path-family comparison."""
    u = url.split("?")[0]
    for marker in (
        r"/dose/sniff/\d+/native",
        r"/dose/sniff/\d+/passthrough",
        r"/pt/polysniff/\d+",
        r"/pt/admin/[^/]+",
    ):
        u = re.sub(marker, "", u, count=1)
    if u.startswith("http"):
        p = urlparse(u)
        return p.path or "/"
    return u if u.startswith("/") else "/" + u


def path_family(path: str) -> str:
    low = path.lower()
    if "/api/" in low or "chirp-frontend" in low:
        return "api"
    if "static.hsappstatic.net" in low or "/static/" in low:
        return "cdn/static"
    if "ably.io" in low:
        return "ably"
    if "chatspot" in low:
        return "chatspot-iframe"
    if "/notifications/" in low:
        return "notifications-iframe"
    if "/login" in low or "/oauth" in low:
        return "auth"
    if "/user-guide" in low:
        return "user-guide"
    return "other"


def analyze_har(har: dict, label: str) -> dict:
    entries = har.get("log", {}).get("entries", [])
    pages = har.get("log", {}).get("pages", [])
    title = pages[0].get("title", "?") if pages else "?"

    hosts = Counter()
    families = Counter()
    statuses = Counter()
    sniff_proxy = 0
    cdn_broken = 0
    errors = []

    for e in entries:
        url = e["request"]["url"]
        resp = e["response"]
        st = resp.get("status", 0)
        err = resp.get("_error")

        hosts[norm_host(url)] += 1
        families[path_family(url + norm_upstream_path(url))] += 1

        if err:
            statuses[f"ERR:{err}"] += 1
            errors.append((err, url[:140]))
        else:
            statuses[st] += 1

        if "/dose/sniff/" in url or "/pt/polysniff/" in url or "/pt/admin/" in url:
            sniff_proxy += 1
        if "/native//static" in url or "/passthrough//static" in url:
            cdn_broken += 1

    return {
        "label": label,
        "page_title": title,
        "entry_count": len(entries),
        "hosts": hosts,
        "families": families,
        "statuses": statuses,
        "sniff_proxy_count": sniff_proxy,
        "cdn_broken_count": cdn_broken,
        "errors": errors,
    }


def print_report(analyses: list[dict]) -> None:
    print("=" * 72)
    print("HubSpot HAR parity report")
    print("=" * 72)
    for a in analyses:
        print(f"\n## {a['label']}")
        print(f"   page title: {a['page_title']}")
        print(f"   entries: {a['entry_count']}")
        print(f"   via sniff/pt proxy: {a['sniff_proxy_count']}")
        print(f"   broken CDN URLs: {a['cdn_broken_count']}")
        print(f"   status mix: {dict(a['statuses'].most_common(8))}")
        print("   hosts:")
        for h, c in a["hosts"].most_common(8):
            print(f"     {c:4d}  {h}")
        print("   path families:")
        for f, c in a["families"].most_common():
            print(f"     {c:4d}  {f}")
        if a["errors"]:
            print("   transport errors:")
            for err, url in a["errors"][:6]:
                print(f"     {err[:40]}  {url}")

    if len(analyses) >= 2:
        print("\n" + "=" * 72)
        print("Cross-mode deltas (host counts)")
        print("=" * 72)
        all_hosts = set()
        for a in analyses:
            all_hosts |= set(a["hosts"].keys())
        baseline = analyses[0]
        for host in sorted(all_hosts):
            counts = [a["hosts"].get(host, 0) for a in analyses]
            if len(set(counts)) > 1:
                parts = " | ".join(f"{a['label']}={c}" for a, c in zip(analyses, counts))
                print(f"  DIFF  {host}: {parts}")

        print("\nPath family deltas:")
        all_fam = set()
        for a in analyses:
            all_fam |= set(a["families"].keys())
        for fam in sorted(all_fam):
            counts = [a["families"].get(fam, 0) for a in analyses]
            if len(set(counts)) > 1:
                parts = " | ".join(f"{a['label']}={c}" for a, c in zip(analyses, counts))
                print(f"  DIFF  {fam}: {parts}")

    print("\n" + "=" * 72)
    print("Parity checklist")
    print("=" * 72)
    labels = [a["label"] for a in analyses]
    if "direct" in labels and "native" in labels:
        d = next(a for a in analyses if a["label"] == "direct")
        n = next(a for a in analyses if a["label"] == "native")
        ok = n["cdn_broken_count"] == 0 and n["sniff_proxy_count"] > 0
        print(f"  [{'x' if ok else ' '}] Native uses sniff prefix for navigation (not zero)")
        print(f"  [{'x' if n['cdn_broken_count']==0 else ' '}] Native has no broken //static CDN URLs")
        api_d = d["families"].get("api", 0)
        api_n = n["families"].get("api", 0)
        print(f"  [{'x' if api_n >= api_d * 0.5 else ' '}] Native API volume roughly matches direct ({api_n} vs {api_d})")
    if "native" in labels and "passthrough" in labels:
        n = next(a for a in analyses if a["label"] == "native")
        p = next(a for a in analyses if a["label"] == "passthrough")
        print(f"  [{'x' if p['cdn_broken_count']==0 else ' '}] Passthrough has no broken CDN URLs")
        print(f"  [{'x' if abs(p['entry_count']-n['entry_count']) < max(50,n['entry_count']*0.3) else ' '}] Entry counts within ~30% (native={n['entry_count']} pt={p['entry_count']})")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 1
    paths = argv[1:]
    default_labels = ["direct", "native", "passthrough"]
    if len(paths) == 2:
        labels = ["direct", "native"]
    else:
        labels = default_labels[: len(paths)]
    analyses = [analyze_har(load_har(p), labels[i]) for i, p in enumerate(paths)]
    print_report(analyses)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
