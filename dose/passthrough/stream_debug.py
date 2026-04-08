"""
Passthrough stream diagnostics — logs what the proxy received from upstream and/or
what Django returns to the browser. Enable globally (POLYSNIFFER_PASSTHROUGH_DEBUG)
or per PassThroughEndpoint.passthrough_stream_debug.

Does not depend on PolySniffer capture IDs or the browser extension.
"""
from __future__ import annotations

import logging
import re
from typing import Any, List, Optional

from django.conf import settings

logger = logging.getLogger("dose.passthrough.stream_debug")

LOG_PREFIX = "[PT-STREAM-DEBUG]"


def passthrough_stream_debug_enabled(endpoint: Any | None) -> bool:
    if getattr(settings, "POLYSNIFFER_PASSTHROUGH_DEBUG", False):
        return True
    if endpoint is not None and getattr(endpoint, "passthrough_stream_debug", False):
        return True
    return False


def _set_cookie_lines_from_requests_response(resp) -> List[str]:
    lines: List[str] = []
    try:
        msg = getattr(resp.raw, "_original_response", None)
        msg = getattr(msg, "msg", None) if msg else None
        if msg is not None:
            raw_list = msg.get_all("Set-Cookie") or []
            for item in raw_list:
                lines.append((item or "")[:180] + ("..." if len(item or "") > 180 else ""))
            return lines
    except Exception:
        pass
    one = resp.headers.get("Set-Cookie")
    if one:
        lines.append(one[:300] + ("..." if len(one) > 300 else ""))
    return lines


def _asset_urls_sample(text: str, limit: int = 50) -> List[str]:
    if not text:
        return []
    out: List[str] = []
    seen = set()
    for m in re.finditer(
        r'(?:src|href)\s*=\s*(["\'])(/[^"\']+)\1', text, flags=re.IGNORECASE
    ):
        u = m.group(2)
        if not u.startswith("/"):
            continue
        if u in seen:
            continue
        seen.add(u)
        if re.search(
            r"\.(js|mjs|css|map|png|jpe?g|gif|svg|ico|webp|woff2?|ttf|eot)(\?|$)",
            u,
            re.I,
        ) or "/dist/" in u or "/core/" in u or "/apps/" in u:
            out.append(u[:220])
        if len(out) >= limit:
            break
    return out


def _token_hints(text: str) -> dict:
    if not text:
        return {}
    return {
        "data_requesttoken_attr": bool(
            re.search(r'data-requesttoken\s*=', text, re.I)
        ),
        "dataset_requesttoken_js": "dataset.requesttoken" in text
        or "document.head.dataset" in text,
    }


def _emit(
    phase: str,
    request,
    endpoint: Any | None,
    *,
    client_path: str,
    upstream_path: Optional[str] = None,
    target_url: Optional[str] = None,
    status_code: Optional[int] = None,
    content_type: Optional[str] = None,
    body_text: Optional[str] = None,
    set_cookie_lines: Optional[List[str]] = None,
) -> None:
    ep_id = getattr(endpoint, "pk", None) if endpoint is not None else None
    ep_trigger = getattr(endpoint, "trigger_path", None) if endpoint is not None else None
    snippet = (body_text or "")[:2800]
    assets = _asset_urls_sample(body_text or "")
    hints = _token_hints(body_text or "")
    lines = [
        f"{LOG_PREFIX} phase={phase}",
        f"  endpoint_id={ep_id} trigger_path={ep_trigger!r}",
        f"  client_path={client_path!r}",
        f"  upstream_path={upstream_path!r}",
        f"  target_url={target_url!r}",
        f"  status_code={status_code}",
        f"  content_type={content_type!r}",
        f"  set_cookie_count={len(set_cookie_lines or [])}",
        f"  requesttoken_hints={hints!r}",
        f"  asset_urls_found({len(assets)}): {assets[:25]}",
        f"  body_snippet_first_bytes={len(snippet)} chars →",
    ]
    blob = "\n".join(lines) + "\n" + snippet
    logger.warning(blob)
    print(blob)


def log_upstream_response_if_debug(
    request,
    endpoint: Any | None,
    *,
    upstream_path: str,
    target_url: str,
    resp,
) -> None:
    if not passthrough_stream_debug_enabled(endpoint):
        return
    try:
        body = (
            resp.content.decode("utf-8", errors="replace") if resp.content else ""
        )
    except Exception:
        body = ""
    ct = resp.headers.get("Content-Type", "")
    _emit(
        "upstream_response",
        request,
        endpoint,
        client_path=getattr(request, "path_info", "") or "",
        upstream_path=upstream_path,
        target_url=target_url,
        status_code=getattr(resp, "status_code", None),
        content_type=ct,
        body_text=body,
        set_cookie_lines=_set_cookie_lines_from_requests_response(resp),
    )


def log_final_response_if_debug(request, response) -> None:
    endpoint = getattr(request, "_passthrough_endpoint", None)
    if not passthrough_stream_debug_enabled(endpoint):
        return
    if not hasattr(response, "content"):
        _emit(
            "response_to_browser",
            request,
            endpoint,
            client_path=getattr(request, "path_info", "") or "",
            status_code=getattr(response, "status_code", None),
            content_type=response.get("Content-Type", ""),
            body_text="[no response.content — streaming or empty]",
            set_cookie_lines=[],
        )
        return
    try:
        body = response.content.decode("utf-8", errors="replace")
    except Exception as exc:
        body = f"[decode error: {exc}]"
    sc_lines: List[str] = []
    try:
        for name, morsel in response.cookies.items():
            sc_lines.append(
                f"{name}=… (path={morsel.get('path', '/')})"[:160]
            )
    except Exception:
        pass
    _emit(
        "response_to_browser",
        request,
        endpoint,
        client_path=getattr(request, "path_info", "") or "",
        status_code=getattr(response, "status_code", None),
        content_type=response.get("Content-Type", ""),
        body_text=body,
        set_cookie_lines=sc_lines,
    )
