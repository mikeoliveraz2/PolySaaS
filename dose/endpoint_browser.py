from urllib.parse import urljoin, urlsplit, urlunsplit

from dose.passthrough.registry import resolve_handler_for_endpoint


def safe_browser_launch_url(endpoint, relative_path: str | None = None) -> str:
    """Return a top-level http(s) URL or an empty string for unsafe targets."""
    candidate = ""
    handler = resolve_handler_for_endpoint(endpoint)
    hook = getattr(handler, "endpoint_browser_launch_url", None)
    if callable(hook):
        try:
            candidate = hook(endpoint) or ""
        except Exception:
            candidate = ""
    if not candidate:
        candidate = getattr(endpoint, "endpoint_url", "") or ""

    parsed = urlsplit(candidate)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return ""

    base = urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))
    path = (relative_path or "").strip()
    if not path or path == "/":
        return base
    requested = urlsplit(path)
    if requested.scheme:
        if (
            requested.netloc.lower() != parsed.netloc.lower()
            or requested.username
            or requested.password
            or requested.scheme not in ("http", "https")
            or (requested.scheme == "http" and parsed.scheme != "http")
        ):
            return ""
        return urlunsplit(
            (
                requested.scheme,
                requested.netloc,
                requested.path or "/",
                requested.query,
                "",
            )
        )
    if not path.startswith("/") or path.startswith("//") or "\\" in path:
        return ""
    origin = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
    return urljoin(origin, path.lstrip("/"))
