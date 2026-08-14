import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SlackPassthroughHandler:
    """Slack passthrough/native-sniff handler for standard browser flows."""

    _SLACK_HOST_MARKERS = (
        "slack.com",
        "slack-edge.com",
        "slack-files.com",
        "app.slack.com",
        "polysaasworkspace.slack.com",
    )

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        blob = " ".join(
            [
                str(getattr(endpoint, "endpoint_url", "") or ""),
                str(getattr(endpoint, "slug", "") or ""),
                str(getattr(endpoint, "description", "") or ""),
                str(getattr(endpoint, "trigger_path", "") or ""),
            ]
        ).lower()
        return "slack" in blob or any(marker in blob for marker in cls._SLACK_HOST_MARKERS)

    def process_html_response(self, html_str, response, endpoint_url=None, *args, **kwargs):
        content = html_str or ""
        if not endpoint_url:
            return content, None
        origin = (endpoint_url or "").rstrip("/")
        if not origin:
            return content, None
        content = re.sub(r"<base\b[^>]*>", "", content, flags=re.IGNORECASE)
        content = re.sub(
            r'(src|href)=("|\')(/[^"\']*)\2',
            lambda m: f"{m.group(1)}={m.group(2)}{origin}{m.group(3)}{m.group(2)}",
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(
            r'(src|href)=("|\')(https?://[^"\']*slack[^"\']*)\2',
            lambda m: f"{m.group(1)}={m.group(2)}{m.group(3)}{m.group(2)}",
            content,
            flags=re.IGNORECASE,
        )
        return content, None

    def should_exempt_csrf_for_path(self, path_info: str) -> bool:
        return bool(path_info) and path_info.startswith("/api/")

    def native_passthrough_prefixes(self):
        return ()

    @staticmethod
    def _is_static_asset(low_path: str) -> bool:
        return (
            low_path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"))
            or "/assets/" in low_path
            or "/static/" in low_path
            or "/cdn/" in low_path
        )

    def should_process_html_response(self, request, upstream_path, **kwargs) -> bool:
        return not self._is_static_asset((upstream_path or "").lower())

    def should_wrap_in_admin_template(self, request, upstream_path, **kwargs) -> bool:
        return not self._is_static_asset((upstream_path or "").lower())


import dose.polysniffer.handlers.slack_native_sniff  # noqa: F401,E402
