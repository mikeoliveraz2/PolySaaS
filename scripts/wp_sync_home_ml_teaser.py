#!/usr/bin/env python3
"""
Insert or update the Machine Learning home teaser on the WordPress front page.

Uses the same credentials as wp_sync_ml_page.py (.env.wordpress at repo root).
HTTP uses the Python standard library only (no requests).

Resolves the page to edit:
  1. GET /wp/v2/settings — if show_on_front is "page", uses page_on_front.
  2. Else GET /wp/v2/pages?slug=<WP_HOME_PAGE_SLUG> (default: home).

Teaser HTML: documentation/website/home-ml-teaser-block.html (file comment stripped).
Wrapped as a Gutenberg Custom HTML block (<!-- wp:html --> ... <!-- /wp:html -->).

On insert, the teaser is placed just above the **last** home CTA (ps-cta-banner —
“Stop Managing Tools…” above the footer); else above the in-page dark footer; else appended.

With --force, any existing teaser is removed and re-inserted at that preferred position
(so you can fix placement without editing WordPress by hand).

Usage:
  python scripts/wp_sync_home_ml_teaser.py
  python scripts/wp_sync_home_ml_teaser.py --dry-run
  python scripts/wp_sync_home_ml_teaser.py --force
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TEASER_REL = Path("documentation/website/home-ml-teaser-block.html")
MARKER = "ps-home-ml-teaser"
WP_HTML_OPEN = "<!-- wp:html -->"
WP_HTML_CLOSE = "<!-- /wp:html -->"
# Repeated on the home page; we anchor to the **last** one (bottom CTA before the dark footer).
CTA_ANCHOR = '<div class="wp-block-group ps-cta-banner"'
# In-page dark footer (Applications / Features columns) — fallback if CTA markup changes.
FOOTER_ANCHOR = '<div style="background:#1a1a2e;padding:60px'

ML_TEASER_WP_HTML = re.compile(
    r"<!--\s*wp:html\s*-->\s*(?=<div\s+class=\"ps-home-ml-teaser\")"
    r".*?"
    r"<!--\s*/wp:html\s*-->",
    re.DOTALL | re.IGNORECASE,
)


def strip_all_ml_teaser_blocks(content: str) -> str:
    """Remove every Custom HTML block that wraps ps-home-ml-teaser."""
    while True:
        m = ML_TEASER_WP_HTML.search(content)
        if not m:
            break
        content = content[: m.start()] + content[m.end() :]
    return content


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


def load_teaser_inner_html() -> str:
    p = REPO_ROOT / TEASER_REL
    if not p.is_file():
        print(f"Missing teaser file: {p}", file=sys.stderr)
        sys.exit(1)
    raw = p.read_text(encoding="utf-8").lstrip()
    if raw.startswith("<!--"):
        end = raw.find("-->", 4)
        if end != -1:
            raw = raw[end + 3 :].lstrip("\n\r")
    return raw.strip()


def wrap_html_block(inner: str) -> str:
    return f"{WP_HTML_OPEN}\n{inner}\n{WP_HTML_CLOSE}\n"


def insert_teaser_into_content(existing: str, wrapped_block: str) -> str:
    """Place teaser above the last ps-cta-banner, else above in-page footer, else at end."""
    pos = existing.rfind(CTA_ANCHOR)
    if pos != -1:
        return existing[:pos].rstrip() + "\n\n" + wrapped_block.rstrip() + "\n\n" + existing[pos:]
    pos = existing.find(FOOTER_ANCHOR)
    if pos != -1:
        return existing[:pos].rstrip() + "\n\n" + wrapped_block.rstrip() + "\n\n" + existing[pos:]
    sep = "\n\n" if existing.strip() else ""
    return existing.rstrip() + sep + wrapped_block


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
    timeout: float = 60,
) -> tuple[int, Any]:
    api = f"{base}/wp-json/wp/v2"
    url = api + path
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data: bytes | None = None
    headers = {
        "Authorization": auth_header,
        "User-Agent": "PolySaaS-wp-sync-home-ml/1.0",
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


def resolve_front_page_id(base: str, auth: str) -> tuple[int, str]:
    slug_fallback = (os.environ.get("WP_HOME_PAGE_SLUG") or "home").strip()
    code, data = wp_request(base, auth, "GET", "/settings", timeout=30)
    if code == 200 and isinstance(data, dict):
        if data.get("show_on_front") == "page":
            pid = int(data.get("page_on_front") or 0)
            if pid > 0:
                return pid, "settings.page_on_front"

    code2, pages = wp_request(
        base,
        auth,
        "GET",
        "/pages",
        params={"slug": slug_fallback, "status": "any"},
        timeout=30,
    )
    if code2 == 401:
        print("401 Unauthorized — check WP_USER and WP_APP_PASSWORD", file=sys.stderr)
        sys.exit(1)
    if code2 != 200 or not isinstance(pages, list):
        print(f"GET pages by slug failed: {code2} {str(pages)[:500]}", file=sys.stderr)
        sys.exit(1)
    if not pages:
        print(
            f"No front page from settings and no page with slug={slug_fallback!r}.\n"
            "Set a static front page in WordPress, or set WP_HOME_PAGE_SLUG in .env.wordpress.",
            file=sys.stderr,
        )
        sys.exit(1)
    return int(pages[0]["id"]), f"slug:{slug_fallback}"


def get_page_raw_content(base: str, auth: str, page_id: int) -> str:
    code, data = wp_request(
        base,
        auth,
        "GET",
        f"/pages/{page_id}",
        params={"context": "edit"},
        timeout=30,
    )
    if code != 200 or not isinstance(data, dict):
        print(f"GET page {page_id} failed: {code} {str(data)[:800]}", file=sys.stderr)
        sys.exit(1)
    content = data.get("content")
    if isinstance(content, dict):
        return (content.get("raw") or "") if content.get("raw") is not None else ""
    if isinstance(content, str):
        return content
    return ""


def merge_teaser(existing: str, teaser_inner: str, force: bool) -> tuple[str, str]:
    wrapped = wrap_html_block(teaser_inner)
    if MARKER in existing and not force:
        return existing, "skip"

    if force and MARKER in existing:
        cleaned = strip_all_ml_teaser_blocks(existing)
        if MARKER in cleaned:
            cleaned = replace_teaser_div(cleaned, "")
        return insert_teaser_into_content(cleaned, wrapped), "replace"

    if MARKER not in existing:
        return insert_teaser_into_content(existing, wrapped), "append"

    return existing, "skip"


def replace_teaser_div(content: str, teaser_inner: str) -> str:
    m = re.search(r'<div\s+class="ps-home-ml-teaser"[^>]*>', content)
    if not m:
        return content
    start = m.start()
    pos = m.end()
    depth = 1
    length = len(content)
    while pos < length and depth > 0:
        next_open = content.find("<div", pos)
        next_close = content.find("</div>", pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                end = next_close + len("</div>")
                return content[:start] + teaser_inner + content[end:]
            pos = next_close + len("</div>")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync ML home teaser block to WordPress front page.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve page and show planned action; no PATCH.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing teaser and re-insert from repo at preferred position (above CTA).",
    )
    args = parser.parse_args()

    load_env_file(REPO_ROOT / ".env.wordpress")
    base, user, app_pw = wp_credentials()
    auth = "Basic " + base64.b64encode(f"{user}:{app_pw}".encode("utf-8")).decode("ascii")

    teaser_inner = load_teaser_inner_html()
    pid, via = resolve_front_page_id(base, auth)
    raw = get_page_raw_content(base, auth, pid)
    new_content, action = merge_teaser(raw, teaser_inner, force=args.force)

    if args.dry_run:
        print(f"Dry run: teaser {len(teaser_inner)} chars, page id={pid} ({via}), would: {action}")
        return 0

    if action == "skip":
        print(f"Front page id={pid} ({via}): teaser already present; use --force to replace. No changes.")
        return 0

    code, out = wp_request(
        base,
        auth,
        "POST",
        f"/pages/{pid}",
        json_body={"content": new_content},
        timeout=90,
    )
    if code != 200:
        print(f"UPDATE page failed: {code} {str(out)[:1200]}", file=sys.stderr)
        return 1
    if not isinstance(out, dict):
        print(f"Unexpected response: {out}", file=sys.stderr)
        return 1
    print(f"Front page id={pid} ({via}): {action} ML teaser. status={out.get('status')}")
    if out.get("link"):
        print(f"  {out['link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
