#!/usr/bin/env python3
"""
Create a Draft WordPress page on polysaas.online (or any WP with REST API).

Use case: "Machine Learning" internal working page — editable in wp-admin, not in menus.
Requires Application Password: wp-admin → Users → Your Profile → Application Passwords.

Env (required):
  WP_BASE_URL       e.g. https://polysaas.online  (no trailing slash)
  WP_USER           WordPress username
  WP_APP_PASSWORD   Application password (spaces optional)

Does not overwrite: if slug ml-platform-internal already exists, exits 0 with a message.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

SLUG = "ml-platform-internal"
TITLE = "Machine Learning (internal draft)"

FALLBACK_HTML = """<!-- Internal draft — not linked from site menus. Expand in wp-admin. -->
<p><strong>Internal working page</strong> for PolySaaS ML / AI platform messaging and table reference.</p>
<p>Paste full layout from <code>documentation/website/machine-learning-page-content.html</code> in the repo.</p>
"""


def load_page_html() -> str:
    """Prefer styled HTML from documentation/website/machine-learning-page-content.html."""
    root = Path(__file__).resolve().parents[1]
    p = root / "documentation" / "website" / "machine-learning-page-content.html"
    if not p.is_file():
        return FALLBACK_HTML
    raw = p.read_text(encoding="utf-8")
    # Remove leading file-level comment (paste instructions) so it does not appear on the site
    s = raw.lstrip()
    if s.startswith("<!--"):
        end = s.find("-->", 4)
        if end != -1:
            raw = s[end + 3 :].lstrip("\n\r")
    return raw


def main() -> int:
    base = (os.environ.get("WP_BASE_URL") or "").rstrip("/")
    user = os.environ.get("WP_USER") or ""
    app_pw = (os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")

    if not base or not user or not app_pw:
        print(
            "Missing env: WP_BASE_URL, WP_USER, WP_APP_PASSWORD\n"
            "See documentation/website/ML-DRAFT-PAGE-WP-ADMIN.md",
            file=sys.stderr,
        )
        return 1

    api = f"{base}/wp-json/wp/v2"
    auth = HTTPBasicAuth(user, app_pw)
    session = requests.Session()
    session.auth = auth
    session.headers["Content-Type"] = "application/json"

    # Check existing by slug
    r = session.get(f"{api}/pages", params={"slug": SLUG, "status": "any"}, timeout=30)
    if r.status_code == 401:
        print("401 Unauthorized — check WP_USER and WP_APP_PASSWORD", file=sys.stderr)
        return 1
    if r.status_code != 200:
        print(f"GET pages failed: {r.status_code} {r.text[:500]}", file=sys.stderr)
        return 1

    existing = r.json()
    if existing:
        pid = existing[0].get("id")
        link = existing[0].get("link") or ""
        status = existing[0].get("status") or ""
        print(f"Page already exists: id={pid} status={status} slug={SLUG}")
        if link:
            print(f"  link: {link}")
        print("Edit in wp-admin → Pages.")
        return 0

    payload = {
        "title": TITLE,
        "slug": SLUG,
        "status": "draft",
        "content": load_page_html(),
    }
    r2 = session.post(f"{api}/pages", data=json.dumps(payload), timeout=60)
    if r2.status_code not in (200, 201):
        print(f"POST page failed: {r2.status_code} {r2.text[:800]}", file=sys.stderr)
        return 1

    data = r2.json()
    print(f"Created draft page id={data.get('id')} slug={SLUG}")
    print("wp-admin → Pages → Drafts → edit 'Machine Learning (internal draft)'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
