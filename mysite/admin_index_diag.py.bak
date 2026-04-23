"""
Admin index diagnostics (no template changes).

Enable with ADMIN_INDEX_DIAG=1 in the environment. On each successful render of
the Django admin site index, logs one structured line so you can compare local
vs Render (permissions, app_list length, resolved index template, session schema).

Disable in production when not actively debugging.
"""

from __future__ import annotations

import logging
from typing import Any

from django.contrib import admin
from django.utils.deprecation import MiddlewareMixin

log = logging.getLogger("dose.admin_index_diag")


def _flatten_template_name(response: Any) -> str:
    tn = getattr(response, "template_name", None)
    if tn is None:
        return ""
    if isinstance(tn, (list, tuple)):
        return ",".join(str(x) for x in tn)
    return str(tn)


class AdminIndexDiagMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response

        path = (request.path_info or "").rstrip("/") or "/"
        if path != "/admin":
            return response

        rm = getattr(request, "resolver_match", None)
        if not rm or getattr(rm, "namespace", None) != "admin":
            return response
        if getattr(rm, "url_name", None) != "index":
            return response

        ctx = getattr(response, "context_data", None)
        if not isinstance(ctx, dict):
            return response

        app_list = ctx.get("app_list")
        avail = ctx.get("available_apps")
        app_len = len(app_list) if isinstance(app_list, list) else None
        avail_len = len(avail) if isinstance(avail, list) else None

        schema = None
        sess = getattr(request, "session", None)
        if sess is not None:
            try:
                schema = sess.get("schema_name")
            except Exception:
                schema = "<session read error>"

        registry_len = len(getattr(admin.site, "_registry", {}) or {})
        idx_tpl = getattr(admin.site, "index_template", None)

        log.info(
            "admin_index_diag "
            "template=%r index_template_attr=%r app_list_len=%s available_apps_len=%s "
            "registry_len=%s user_id=%s username=%r is_superuser=%s is_staff=%s schema_name=%r",
            _flatten_template_name(response),
            idx_tpl,
            app_len,
            avail_len,
            registry_len,
            getattr(request.user, "pk", None),
            getattr(request.user, "get_username", lambda: "")(),
            getattr(request.user, "is_superuser", False),
            getattr(request.user, "is_staff", False),
            schema,
        )

        return response
