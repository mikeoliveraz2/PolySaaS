#!/usr/bin/env python3
"""Create/update Privacy, Terms, Disclaimer pages on WordPress from staging HTML files."""
from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

PAGES = [
    ("privacy-policy", "Privacy Policy", "documentation/website/privacy-policy-page-staging.html"),
    ("terms-of-service", "Terms of Service", "documentation/website/terms-of-service-page-staging.html"),
    ("disclaimer", "Disclaimer", "documentation/website/disclaimer-page-staging.html"),
]


def load_html(rel: str) -> str:
    path = REPO_ROOT / rel
    raw = path.read_text(encoding="utf-8")
    stripped = raw.lstrip()
    while stripped.startswith("<!--"):
        end = stripped.find("-->", 4)
        if end == -1:
            break
        stripped = stripped[end + 3 :].lstrip("\n\r")
    return stripped


def wp_request(
    base: str,
    auth: str,
    method: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    url = f"{base.rstrip('/')}/wp-json/wp/v2{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = None
    headers = {"Authorization": auth, "User-Agent": "PolySaaS-wp-sync-legal/1.0"}
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90, context=ssl.create_default_context()) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(err) if err.strip() else {}
        except json.JSONDecodeError:
            return exc.code, err


def main() -> int:
    base = (os.environ.get("WP_BASE_URL") or "").rstrip("/")
    user = os.environ.get("WP_USER") or ""
    pw = (os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")
    if not base or not user or not pw:
        print("Missing WP_BASE_URL / WP_USER / WP_APP_PASSWORD", file=sys.stderr)
        return 1
    auth = "Basic " + base64.b64encode(f"{user}:{pw}".encode("utf-8")).decode("ascii")

    code, me = wp_request(base, auth, "GET", "/users/me")
    if code != 200:
        print(f"Auth failed: {code} {str(me)[:400]}", file=sys.stderr)
        return 1
    print(f"Authenticated as {me.get('name') or me.get('slug') or user}")

    for slug, title, rel in PAGES:
        html = load_html(rel)
        code, pages = wp_request(base, auth, "GET", "/pages", params={"slug": slug, "status": "any"})
        if code != 200 or not isinstance(pages, list):
            print(f"GET {slug} failed: {code} {str(pages)[:400]}", file=sys.stderr)
            return 1
        body = {"title": title, "content": html, "status": "publish", "slug": slug}
        if pages:
            page_id = pages[0]["id"]
            code2, out = wp_request(base, auth, "POST", f"/pages/{page_id}", json_body=body)
            action = "Updated"
        else:
            code2, out = wp_request(base, auth, "POST", "/pages", json_body=body)
            action = "Created"
        if code2 not in (200, 201) or not isinstance(out, dict):
            print(f"{action} {slug} failed: {code2} {str(out)[:800]}", file=sys.stderr)
            return 1
        print(f"{action} {slug} id={out.get('id')} status={out.get('status')} {out.get('link')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
