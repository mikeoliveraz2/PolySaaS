#!/usr/bin/env python3
"""
Push documentation/website/machine-learning-page-content.html to WordPress (create or update).

Uses the Python standard library only (no requests).

Setup (once):
  1. wp-admin → Users → Profile → Application Passwords → create (e.g. "poly-sync").
  2. Copy repo: documentation/website/.env.wordpress.example → .env.wordpress (repo root).
  3. Fill WP_BASE_URL, WP_USER, WP_APP_PASSWORD. Never commit .env.wordpress (gitignored).

Run (after git pull):
  python scripts/wp_sync_ml_page.py

Optional env:
  WP_PAGE_TITLE     default: Machine Learning
  WP_PAGE_STATUS    draft | publish | private — used only when CREATING a new page.
  WP_FORCE_STATUS   if set, POST update uses this status (e.g. publish).
  WP_SKIP_ML_MEDIA  if set, do not upload Product screenshots or rewrite img src.
  WP_REFRESH_ML_MEDIA — ignore .wp-ml-screenshots.json and re-upload PNGs to Media.

Before updating the page, any img src pointing at raw.githubusercontent.com/.../chat-uploads-for-wp/
is replaced: files are POSTed to /wp/v2/media and src is set to the returned source_url. Mappings
are cached in repo-root .wp-ml-screenshots.json (gitignored).

Loads .env.wordpress from repo root if present (does not override existing env vars).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SLUG = "machine-learning"
DEFAULT_TITLE = "Machine Learning"
HTML_REL = Path("documentation/website/machine-learning-page-content.html")
ML_SCREENSHOTS_DIR = REPO_ROOT / "documentation" / "website" / "assets" / "chat-uploads-for-wp"
SCREENSHOT_CACHE = REPO_ROOT / ".wp-ml-screenshots.json"
RAW_GITHUB_SHOT_RE = re.compile(
    r'(https://raw\.githubusercontent\.com/[^"\s>]+/documentation/website/assets/chat-uploads-for-wp/([^"\s>]+\.png))'
)


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
    p = REPO_ROOT / HTML_REL
    if not p.is_file():
        print(f"Missing HTML file: {p}", file=sys.stderr)
        sys.exit(1)
    raw = p.read_text(encoding="utf-8")
    s = raw.lstrip()
    if s.startswith("<!--"):
        end = s.find("-->", 4)
        if end != -1:
            raw = s[end + 3 :].lstrip("\n\r")
    return raw


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
        "User-Agent": "PolySaaS-wp-sync-ml-page/1.0",
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
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(err_text) if err_text.strip() else {}
        except json.JSONDecodeError:
            return e.code, err_text


def _multipart_png_body(filename: str, content: bytes) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: image/png\r\n"
        "\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = head + content + tail
    return body, f"multipart/form-data; boundary={boundary}"


def wp_upload_media(base: str, auth_header: str, png_path: Path, timeout: float = 120) -> tuple[int, Any]:
    url = f"{base.rstrip('/')}/wp-json/wp/v2/media"
    content = png_path.read_bytes()
    body, ctype = _multipart_png_body(png_path.name, content)
    headers = {
        "Authorization": auth_header,
        "Content-Type": ctype,
        "User-Agent": "PolySaaS-wp-sync-ml-page/1.0",
        "Content-Disposition": f'attachment; filename="{png_path.name}"',
    }
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.getcode()
            text = resp.read().decode("utf-8", errors="replace")
            if not text.strip():
                return code, {}
            return code, json.loads(text)
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(err_text) if err_text.strip() else {}
        except json.JSONDecodeError:
            return e.code, err_text


def _url_head_ok(url: str, timeout: float = 15) -> bool:
    req = urllib.request.Request(url, method="HEAD")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return 200 <= r.getcode() < 400
    except Exception:
        return False


def load_screenshot_cache(*, refresh: bool) -> dict[str, str]:
    if refresh or not SCREENSHOT_CACHE.is_file():
        return {}
    try:
        data = json.loads(SCREENSHOT_CACHE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_screenshot_cache(cache: dict[str, str]) -> None:
    SCREENSHOT_CACHE.write_text(
        json.dumps(cache, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def rewrite_ml_screenshot_src(html: str, base: str, auth_header: str) -> str:
    skip = (os.environ.get("WP_SKIP_ML_MEDIA") or "").strip().lower() in ("1", "true", "yes")
    if skip:
        print("WP_SKIP_ML_MEDIA set — skipping ML screenshot upload and src rewrite.")
        return html

    refresh = (os.environ.get("WP_REFRESH_ML_MEDIA") or "").strip().lower() in ("1", "true", "yes")
    cache = load_screenshot_cache(refresh=refresh)
    by_fname: dict[str, str] = {}
    for m in RAW_GITHUB_SHOT_RE.finditer(html):
        full_url, fname = m.group(1), m.group(2)
        by_fname[fname] = full_url

    if not by_fname:
        return html

    out_cache = dict(cache)
    for fname in sorted(by_fname):
        old_url = by_fname[fname]
        local = ML_SCREENSHOTS_DIR / fname
        if not local.is_file():
            print(f"Warning: missing local file {local.name}, skip rewrite.", file=sys.stderr)
            continue

        wp_url: str | None = None
        if not refresh and fname in cache:
            c = cache[fname]
            if c and _url_head_ok(c):
                wp_url = c
                print(f"Using cached WordPress URL for {fname}")

        if wp_url is None:
            print(f"Uploading media: {fname} …")
            code, out = wp_upload_media(base, auth_header, local)
            if code not in (200, 201):
                print(f"  Upload failed ({code}): {str(out)[:800]}", file=sys.stderr)
                continue
            if not isinstance(out, dict):
                print(f"  Unexpected response for {fname}", file=sys.stderr)
                continue
            wp_url = (out.get("source_url") or "").strip()
            if not wp_url:
                print(f"  No source_url in response for {fname}", file=sys.stderr)
                continue
            print(f"  → {wp_url}")

        out_cache[fname] = wp_url
        html = html.replace(old_url, wp_url)

    save_screenshot_cache(out_cache)
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Machine Learning page HTML to WordPress.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load HTML and print byte length; do not call WordPress.",
    )
    args = parser.parse_args()

    load_env_file(REPO_ROOT / ".env.wordpress")
    base, user, app_pw = wp_credentials()
    auth = "Basic " + base64.b64encode(f"{user}:{app_pw}".encode("utf-8")).decode("ascii")

    html = load_page_html()
    title = os.environ.get("WP_PAGE_TITLE") or DEFAULT_TITLE
    create_status = os.environ.get("WP_PAGE_STATUS") or "draft"
    force_status = os.environ.get("WP_FORCE_STATUS") or ""

    if args.dry_run:
        print(f"Dry run: HTML length {len(html)} chars, title would be {title!r}")
        return 0

    html = rewrite_ml_screenshot_src(html, base, auth)

    code, pages = wp_request(
        base, auth, "GET", "/pages", params={"slug": SLUG, "status": "any"}, timeout=30
    )
    if code == 401:
        print("401 Unauthorized — check WP_USER and WP_APP_PASSWORD", file=sys.stderr)
        return 1
    if code != 200 or not isinstance(pages, list):
        print(f"GET pages failed: {code} {str(pages)[:500]}", file=sys.stderr)
        return 1

    if pages:
        pid = pages[0]["id"]
        prev_status = pages[0].get("status") or "draft"
        body: dict[str, Any] = {"title": title, "content": html}
        if force_status:
            body["status"] = force_status
        code2, out = wp_request(base, auth, "POST", f"/pages/{pid}", json_body=body, timeout=90)
        if code2 != 200:
            print(f"UPDATE page failed: {code2} {str(out)[:1000]}", file=sys.stderr)
            return 1
        if not isinstance(out, dict):
            print(f"Unexpected response: {out}", file=sys.stderr)
            return 1
        st = out.get("status", prev_status)
        print(f"Updated page id={pid} slug={SLUG} status={st}")
        if out.get("link"):
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
    if not isinstance(out, dict):
        print(f"Unexpected response: {out}", file=sys.stderr)
        return 1
    print(f"Created page id={out.get('id')} slug={SLUG} status={out.get('status')}")
    if out.get("link"):
        print(f"  {out['link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
