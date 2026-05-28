#!/usr/bin/env python3
"""Compare Direct vs Passthrough HARs — show only differences."""
import json, re, sys
from urllib.parse import urlparse

def extract_urls(path, is_pt=False):
    with open(path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    reqs = {}
    for entry in har.get('log', {}).get('entries', []):
        req = entry['request']
        resp = entry['response']
        url = req['url']
        # Strip host
        p = urlparse(url)
        path_only = p.path + ('?' + p.query if p.query else '')
        # For passthrough, strip proxy prefix
        if is_pt:
            m = re.match(r'^/pt/admin/[^/]+(/.*)$', path_only)
            if m:
                path_only = m.group(1)
        key = f"{req['method']} {path_only}"
        reqs[key] = {'status': resp.get('status', 0), 'orig_url': url}
    return reqs

def main():
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <direct_har> <passthrough_har>")
        sys.exit(1)
    direct = extract_urls(sys.argv[1], is_pt=False)
    pt = extract_urls(sys.argv[2], is_pt=True)
    only_dir = sorted(set(direct) - set(pt))
    only_pt = sorted(set(pt) - set(direct))
    both = sorted(set(direct) & set(pt))
    status_diff = [k for k in both if direct[k]['status'] != pt[k]['status']]

    print("=" * 70)
    print("LEFT = Direct Mattermost    |    RIGHT = Passthrough")
    print("=" * 70)
    if only_dir:
        print(f"\n>>> ONLY in Direct ({len(only_dir)}):")
        for k in only_dir: print(f"  {direct[k]['status']:>3}  {k}")
    if only_pt:
        print(f"\n>>> ONLY in Passthrough ({len(only_pt)}):")
        for k in only_pt: print(f"  {pt[k]['status']:>3}  {k}")
    if status_diff:
        print(f"\n>>> STATUS DIFFERS ({len(status_diff)}):")
        for k in status_diff:
            print(f"  Direct={direct[k]['status']:>3}  PT={pt[k]['status']:>3}  {k}")
    if not (only_dir or only_pt or status_diff):
        print("\nNo differences found — HARs match!")
    print(f"\nSummary: Direct={len(direct)}  Passthrough={len(pt)}  Common={len(both)}")

if __name__ == '__main__':
    main()
