"""
First-party PolySaaS context for the in-process LLM router / orchestration.

Use these URLs in **system prompts** or tool-planning so models know where
**OpenAPI / Swagger**, **structured logs**, and **passthrough** live — without
scraping the whole site.

Paths are **relative** (same origin). Pass ``request`` to build absolute URLs
for outbound workers or email.
"""

from __future__ import annotations

from typing import Any

from django.urls import NoReverseMatch, reverse


def _abs(request: Any | None, path: str) -> str:
    if request is None:
        return path
    return request.build_absolute_uri(path)


def platform_link_map(request: Any | None = None) -> dict[str, str]:
    """
    Stable entry points for OpenAPI, Swagger UI, REST lists, and admin CRUD.

    Keys are intentionally verbose so prompts can cite them literally.
    """
    rel: dict[str, str] = {}

    # Swagger / OpenAPI: both site root and /dose/ register similar views; use
    # fixed paths to avoid duplicate URL name collisions on ``schema-swagger-ui``.
    rel["site_swagger_ui"] = "/swagger/"
    rel["dose_swagger_ui"] = "/dose/swagger/"
    try:
        rel["site_openapi_json"] = reverse("schema-json", kwargs={"format": ".json"})
    except NoReverseMatch:
        rel["site_openapi_json"] = "/swagger.json"
    try:
        rel["dose_openapi_json"] = reverse("dose-swagger-json")
    except NoReverseMatch:
        rel["dose_openapi_json"] = "/dose/swagger.json"

    # DRF list endpoints (auth + tenant headers as usual for your deployment)
    for key, name in (
        ("dose_api_passthroughendpoints", "passthroughendpoint-list"),
        ("dose_api_requestlogs", "requestlog-list"),
        ("dose_api_errorlogs", "errorlog-list"),
    ):
        try:
            rel[key] = reverse(name)
        except NoReverseMatch:
            pass
    rel.setdefault("dose_api_passthroughendpoints", "/dose/api/passthroughendpoints/")
    rel.setdefault("dose_api_requestlogs", "/dose/api/requestlogs/")
    rel.setdefault("dose_api_errorlogs", "/dose/api/errorlogs/")

    # Admin changelists (staff)
    for key, name in (
        ("admin_passthrough_changelist", "admin:dose_passthroughendpoint_changelist"),
        ("admin_requestlog_changelist", "admin:dose_requestlog_changelist"),
        ("admin_errorlog_changelist", "admin:dose_errorlog_changelist"),
    ):
        try:
            rel[key] = reverse(name)
        except NoReverseMatch:
            pass
    rel.setdefault("admin_passthrough_changelist", "/admin/dose/passthroughendpoint/")
    rel.setdefault("admin_requestlog_changelist", "/admin/dose/requestlog/")
    rel.setdefault("admin_errorlog_changelist", "/admin/dose/errorlog/")

    # HTML passthrough shell (``service`` slug is tenant-specific)
    try:
        rel["dose_passthrough_html_example"] = reverse(
            "passthrough_service", kwargs={"service": "_example_"}
        ).replace("_example_", "{service}")
    except NoReverseMatch:
        rel["dose_passthrough_html_example"] = "/dose/admin/passthrough/{service}/"

    if request is None:
        return rel
    return {k: _abs(request, v) for k, v in rel.items()}


def platform_context_for_system_prompt(request: Any | None = None, *, max_lines: int = 40) -> str:
    """
    Compact bullet list suitable for appending to a system prompt.

    Does **not** fetch OpenAPI content (too large); it only points the model at
    the right URLs so tools / browsing can follow later.
    """
    m = platform_link_map(request)
    lines = [
        "PolySaaS platform references (same origin):",
        f"- Site Swagger UI: {m.get('site_swagger_ui', '')}",
        f"- Site OpenAPI JSON: {m.get('site_openapi_json', '')}",
        f"- Dose Swagger UI (scoped under /dose/): {m.get('dose_swagger_ui', '')}",
        f"- Dose OpenAPI JSON: {m.get('dose_openapi_json', '')}",
        f"- REST: passthrough endpoint registry → {m.get('dose_api_passthroughendpoints', '')}",
        f"- REST: request logs → {m.get('dose_api_requestlogs', '')}",
        f"- REST: error logs → {m.get('dose_api_errorlogs', '')}",
        f"- Admin: PassThrough endpoints → {m.get('admin_passthrough_changelist', '')}",
        f"- Admin: RequestLog → {m.get('admin_requestlog_changelist', '')}",
        f"- Admin: ErrorLog → {m.get('admin_errorlog_changelist', '')}",
        f"- HTML passthrough (slug) → {m.get('dose_passthrough_html_example', '')}",
    ]
    return "\n".join(lines[:max_lines])
