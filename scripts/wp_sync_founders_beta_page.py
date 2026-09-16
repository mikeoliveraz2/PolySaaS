#!/usr/bin/env python3
"""
Create or update the Founders Beta Circle WordPress page from repo HTML.

Source of truth (staging first):
  documentation/website/founders-beta-circle-page-staging.html

Loads .env.wordpress from repo root if present.

  WP_BASE_URL=https://azure-nightingale-589250.hostingersite.com
  WP_USER=...
  WP_APP_PASSWORD=xxxx xxxx ...

Optional:
  WP_PAGE_TITLE     default: Founders Beta Circle
  WP_PAGE_STATUS    draft|publish|private — create only
  WP_FORCE_STATUS   if set, applied on update too
"""
from __future__ import annotations

import argparse
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
SLUG = "founders-beta-circle"
DEFAULT_TITLE = "Founders Beta Circle"
HTML_REL = Path("documentation/website/founders-beta-circle-page-staging.html")


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def load_page_html() -> str:
    path = REPO_ROOT / HTML_REL
    if not path.is_file():
        print(f"Missing HTML file: {path}", file=sys.stderr)
        sys.exit(1)
    raw = path.read_text(encoding="utf-8")
    stripped = raw.lstrip()
    # Strip leading HTML comment blocks (file header notes)
    while stripped.startswith("<!--"):
        end = stripped.find("-->", 4)
        if end == -1:
            break
        stripped = stripped[end + 3 :].lstrip("\n\r")
    return stripped


def wp_credentials() -> tuple[str, str, str]:
    base = (os.environ.get("WP_BASE_URL") or "").rstrip("/")
    user = os.environ.get("WP_USER") or ""
    app_pw = (os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")
    if not base or not user or not app_pw:
        print(
            "Missing WP_BASE_URL, WP_USER, or WP_APP_PASSWORD.\n"
            "Set them in .env.wordpress (see documentation/website/.env.wordpress.example).",
            file=sys.stderr,
        )
        sys.exit(1)
    return base, user, app_pw


def wp_request(
    base: str,
    auth_header: str,
    method: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: float = 90,
) -> tuple[int, Any]:
    api = f"{base}/wp-json/wp/v2"
    url = api + path
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data: bytes | None = None
    headers = {
        "Authorization": auth_header,
        "User-Agent": "PolySaaS-wp-sync-founders-beta/1.0",
    }
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.getcode()
            text = resp.read().decode("utf-8", errors="replace")
            if not text.strip():
                return code, {}
            return code, json.loads(text)
    except urllib.error.HTTPError as exc:
        err_text = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(err_text) if err_text.strip() else {}
        except json.JSONDecodeError:
            return exc.code, err_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Founders Beta Circle page HTML to WordPress.")
    parser.add_argument("--dry-run", action="store_true", help="Load HTML only; do not call WordPress.")
    args = parser.parse_args()

    load_env_file(REPO_ROOT / ".env.wordpress")
    html = load_page_html()
    title = os.environ.get("WP_PAGE_TITLE") or DEFAULT_TITLE
    create_status = os.environ.get("WP_PAGE_STATUS") or "publish"
    force_status = os.environ.get("WP_FORCE_STATUS") or "publish"

    if args.dry_run:
        print(f"Dry run: HTML length {len(html)} chars, title would be {title!r}")
        return 0

    base, user, app_pw = wp_credentials()
    auth = "Basic " + base64.b64encode(f"{user}:{app_pw}".encode("utf-8")).decode("ascii")

    code, pages = wp_request(
        base,
        auth,
        "GET",
        "/pages",
        params={"slug": SLUG, "status": "any"},
        timeout=30,
    )
    if code == 401:
        print("401 Unauthorized — check WP_USER and WP_APP_PASSWORD", file=sys.stderr)
        return 1
    if code != 200 or not isinstance(pages, list):
        print(f"GET pages failed: {code} {str(pages)[:500]}", file=sys.stderr)
        return 1

    if pages:
        page_id = pages[0]["id"]
        body: dict[str, Any] = {"title": title, "content": html}
        if force_status:
            body["status"] = force_status
        code2, out = wp_request(base, auth, "POST", f"/pages/{page_id}", json_body=body, timeout=90)
        if code2 != 200:
            print(f"UPDATE page failed: {code2} {str(out)[:1000]}", file=sys.stderr)
            return 1
        print(f"Updated page id={page_id} slug={SLUG} status={out.get('status') if isinstance(out, dict) else '?'}")
        if isinstance(out, dict) and out.get("link"):
            print(f"  {out['link']}")
        return 0

    body = {
        "title": title,
        "slug": SLUG,
        "status": create_status,
        "content": html,
    }
    code3, out = wp_request(base, auth, "POST", "/pages", json_body=body, timeout=90)
    if code3 not in (200, 201):
        print(f"CREATE page failed: {code3} {str(out)[:1000]}", file=sys.stderr)
        return 1
    print(f"Created page id={out.get('id') if isinstance(out, dict) else '?'} slug={SLUG}")
    if isinstance(out, dict) and out.get("link"):
        print(f"  {out['link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
