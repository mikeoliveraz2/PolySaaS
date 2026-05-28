#!/usr/bin/env python3
"""Compare two Mattermost HAR files: Direct vs Passthrough.

Usage:
    python compare_hars.py <direct_har> <passthrough_har>

Output: Only requests that differ between the two HARs.
"""
import json, sys, re
from urllib.parse import urlparse

def load_har(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_url(url, is_passthrough=False):
    """Strip proxy prefix and host so we can compare paths."""
    # Strip proxy prefix for passthrough
    if is_passthrough:
        m = re.match(r'^https?://[^/]+(/pt/admin/[^/]+)(/.*)$', url)
        if m:
            url = m.group(2)
    # Strip host
    parsed = urlparse(url)
    return parsed.path + ('?' + parsed.query if parsed.query else '')

def extract_requests(har, is_passthrough=False):
    reqs = {}
    for entry in har.get('log', {}).get('entries', []):
        req = entry.get('request', {})
        resp = entry.get('response', {})
        url = normalize_url(req.get('url', ''), is_passthrough)
        method = req.get('method', 'GET')
        status = resp.get('status', 0)
        key = f"{method} {url}"
        reqs[key] = {
            'status': status,
            'url': req.get('url', ''),
            'type': entry.get('_resourceType', ''),
        }
    return reqs

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_hars.py <direct_har> <passthrough_har>")
        sys.exit(1)

    direct = extract_requests(load_har(sys.argv[1]), is_passthrough=False)
    pt = extract_requests(load_har(sys.argv[2]), is_passthrough=True)

    direct_only = set(direct.keys()) - set(pt.keys())
    pt_only = set(pt.keys()) - set(direct.keys())
    common = set(direct.keys()) & set(pt.keys())
    status_diff = [k for k in common if direct[k]['status'] != pt[k]['status']]

    print("=" * 70)
    print("LEFT = Direct Mattermost    |    RIGHT = Passthrough")
    print("=" * 70)

    if direct_only:
        print(f"\n--- ONLY in Direct ({len(direct_only)} requests) ---")
        for k in sorted(direct_only):
            print(f"  {direct[k]['status']:>3}  {k}")

    if pt_only:
        print(f"\n--- ONLY in Passthrough ({len(pt_only)} requests) ---")
        for k in sorted(pt_only):
            print(f"  {pt[k]['status']:>3}  {k}")

    if status_diff:
        print(f"\n--- Status DIFFERS ({len(status_diff)} requests) ---")
        for k in sorted(status_diff):
            print(f"  Direct={direct[k]['status']:>3}  Passthrough={pt[k]['status']:>3}  {k}")

    if not (direct_only or pt_only or status_diff):
        print("\nNo differences found in critical requests!")

    print(f"\n--- Summary ---")
    print(f"Direct total:      {len(direct)}")
    print(f"Passthrough total: {len(pt)}")
    print(f"Common:            {len(common)}")

if __name__ == '__main__':
    main()
