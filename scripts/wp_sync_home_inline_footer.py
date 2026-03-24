#!/usr/bin/env python3
"""
Patch the in-page dark footer HTML on the WordPress front page (polysaas.online home).

Fixes:
  - Logo column: stray </p> after <img> → proper <p><img …></p>
  - Legal row: stray </p> after copyright <span>
  - Applications / Features / Gallery: add missing closing </p> on link paragraphs
  - Features: insert Machine Learning (/machine-learning/) after Dynamic Orchestration

Uses .env.wordpress (same as wp_sync_ml_page.py). Does not change theme template footers;
for header Features dropdown see documentation/website/WORDPRESS-ML-NAV-HOME.md.

  python scripts/wp_sync_home_inline_footer.py
  python scripts/wp_sync_home_inline_footer.py --dry-run
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

LINK_STYLE = 'style="color:#ccc;text-decoration:none;display:block;margin:3px 0"'

FEATURES_BLOCK_OLD = """<h4 style="color:#5eead4;font-size:16px;margin-bottom:8px;font-weight:600">Features</h4>
<p><a href="/bundled-applications/" """ + LINK_STYLE + """>Bundled Applications</a><br />
<a href="/external-applications/" """ + LINK_STYLE + """>External Applications</a><br />
<a href="/ai-as-peers/" """ + LINK_STYLE + """>AI As Peers</a><br />
<a href="/apps-as-peers/" """ + LINK_STYLE + """>Apps As Peers</a><br />
<a href="/polysniffer/" """ + LINK_STYLE + """>PolySniffer</a><br />
<a href="/dynamic-orchestration/" """ + LINK_STYLE + """>Dynamic Orchestration</a><br />
<a href="/atomic-services/" """ + LINK_STYLE + """>Atomic Services</a><br />
<a href="/openapi-2/" """ + LINK_STYLE + """>OpenAPI</a><br />
<a href="/portal/" """ + LINK_STYLE + """>Portal</a><br />
<a href="/architecture/" """ + LINK_STYLE + """>Architecture</a>
</div>"""

FEATURES_BLOCK_NEW = """<h4 style="color:#5eead4;font-size:16px;margin-bottom:8px;font-weight:600">Features</h4>
<p><a href="/bundled-applications/" """ + LINK_STYLE + """>Bundled Applications</a><br />
<a href="/external-applications/" """ + LINK_STYLE + """>External Applications</a><br />
<a href="/ai-as-peers/" """ + LINK_STYLE + """>AI As Peers</a><br />
<a href="/apps-as-peers/" """ + LINK_STYLE + """>Apps As Peers</a><br />
<a href="/polysniffer/" """ + LINK_STYLE + """>PolySniffer</a><br />
<a href="/dynamic-orchestration/" """ + LINK_STYLE + """>Dynamic Orchestration</a><br />
<a href="/machine-learning/" """ + LINK_STYLE + """>Machine Learning</a><br />
<a href="/atomic-services/" """ + LINK_STYLE + """>Atomic Services</a><br />
<a href="/openapi-2/" """ + LINK_STYLE + """>OpenAPI</a><br />
<a href="/portal/" """ + LINK_STYLE + """>Portal</a><br />
<a href="/architecture/" """ + LINK_STYLE + """>Architecture</a></p>
</div>"""

LOGO_IMG_BROKEN = (
    '<img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/'
    'Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS" '
    'style="width:100px;margin-bottom:8px;border-radius:8px;display:block" /></p>'
)
LOGO_IMG_FIXED = (
    '<p><img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/'
    'Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS" '
    'style="width:100px;margin-bottom:8px;border-radius:8px;display:block" /></p>'
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


def wp_credentials() -> tuple[str, str, str]:
    base = (os.environ.get("WP_BASE_URL") or "").rstrip("/")
    user = os.environ.get("WP_USER") or ""
    app_pw = (os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")
    if not base or not user or not app_pw:
        print("Missing WP_BASE_URL, WP_USER, or WP_APP_PASSWORD (.env.wordpress).", file=sys.stderr)
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
    headers = {"Authorization": auth_header, "User-Agent": "PolySaaS-wp-home-footer/1.0"}
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


def resolve_front_page_id(base: str, auth: str) -> int:
    code, data = wp_request(base, auth, "GET", "/settings", timeout=30)
    if code == 200 and isinstance(data, dict) and data.get("show_on_front") == "page":
        pid = int(data.get("page_on_front") or 0)
        if pid > 0:
            return pid
    slug = (os.environ.get("WP_HOME_PAGE_SLUG") or "home").strip()
    code2, pages = wp_request(base, auth, "GET", "/pages", params={"slug": slug, "status": "any"})
    if code2 != 200 or not isinstance(pages, list) or not pages:
        print("Could not resolve front page id.", file=sys.stderr)
        sys.exit(1)
    return int(pages[0]["id"])


def get_raw_content(base: str, auth: str, page_id: int) -> str:
    code, data = wp_request(
        base, auth, "GET", f"/pages/{page_id}", params={"context": "edit"}, timeout=30
    )
    if code != 200 or not isinstance(data, dict):
        print(f"GET page failed: {code}", file=sys.stderr)
        sys.exit(1)
    content = data.get("content")
    if isinstance(content, dict):
        return content.get("raw") or ""
    return content if isinstance(content, str) else ""


def patch_inline_footer(raw: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = raw

    if LOGO_IMG_BROKEN in out:
        out = out.replace(LOGO_IMG_BROKEN, LOGO_IMG_FIXED, 1)
        notes.append("logo <p> wrap")

    bad_copy = '<span style="color:#888">&copy; 2026 PolySaaS Online</span></p>'
    good_copy = '<span style="color:#888">&copy; 2026 PolySaaS Online</span>'
    if bad_copy in out:
        out = out.replace(bad_copy, good_copy, 1)
        notes.append("copyright stray </p>")

    # Applications column: close <p> before Features column
    app_fix = (
        '<a href="/monitor-logger-4/" '
        + LINK_STYLE
        + ">Monitor Logger</a>\n</div>\n<div style=\"text-align:left\">\n<h4 style=\"color:#5eead4"
    )
    app_fixed = (
        '<a href="/monitor-logger-4/" '
        + LINK_STYLE
        + ">Monitor Logger</a></p>\n</div>\n<div style=\"text-align:left\">\n<h4 style=\"color:#5eead4"
    )
    if app_fix in out:
        out = out.replace(app_fix, app_fixed, 1)
        notes.append("applications </p>")

    if FEATURES_BLOCK_OLD in out:
        out = out.replace(FEATURES_BLOCK_OLD, FEATURES_BLOCK_NEW, 1)
        notes.append("features + Machine Learning + </p>")
    elif "/machine-learning/" in out and "Features</h4>" in out:
        notes.append("features already has ML or layout changed — skipped features replace")

    # Gallery: close <p> before grid end
    gal_fix = (
        '<a href="/gallery-videos/" '
        + LINK_STYLE
        + ">Videos</a>\n</div>\n</div>\n<div style=\"border-top:1px solid #333"
    )
    gal_fixed = (
        '<a href="/gallery-videos/" '
        + LINK_STYLE
        + ">Videos</a></p>\n</div>\n</div>\n<div style=\"border-top:1px solid #333"
    )
    if gal_fix in out:
        out = out.replace(gal_fix, gal_fixed, 1)
        notes.append("gallery </p>")

    return out, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch home page inline footer HTML on WordPress.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env_file(REPO_ROOT / ".env.wordpress")
    base, user, app_pw = wp_credentials()
    auth = "Basic " + base64.b64encode(f"{user}:{app_pw}".encode("utf-8")).decode("ascii")
    pid = resolve_front_page_id(base, auth)
    raw = get_raw_content(base, auth, pid)
    new_raw, notes = patch_inline_footer(raw)

    if new_raw == raw:
        print("No changes applied (already patched or markup differs).")
        return 0

    print("Changes:", "; ".join(notes) if notes else "(unknown)")

    if args.dry_run:
        print(f"Dry run: would update page id={pid}, delta {len(new_raw) - len(raw)} chars")
        return 0

    code, out = wp_request(
        base, auth, "POST", f"/pages/{pid}", json_body={"content": new_raw}, timeout=90
    )
    if code != 200:
        print(f"UPDATE failed: {code} {str(out)[:1000]}", file=sys.stderr)
        return 1
    if isinstance(out, dict) and out.get("link"):
        print(f"Updated {out['link']} status={out.get('status')}")
    else:
        print("Updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
