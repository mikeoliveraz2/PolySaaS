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
            log.warning("admin_index_diag: response has no context_data dict (template_response=%r)", type(response))
            return response

        app_list = ctx.get("app_list")
        avail = ctx.get("available_apps")
        app_len = len(app_list) if isinstance(app_list, list) else None
        avail_len = len(avail) if isinstance(avail, list) else None

        # Names of apps that made it into app_list (empty = all models hidden / no perms)
        app_names = [a.get("name", "?") for a in (app_list or [])]

        schema = None
        sess = getattr(request, "session", None)
        if sess is not None:
            try:
                schema = sess.get("schema_name")
            except Exception:
                schema = "<session read error>"

        registry_len = len(getattr(admin.site, "_registry", {}) or {})
        idx_tpl = getattr(admin.site, "index_template", None)

        # Jazzmin reads JAZZMIN_SETTINGS["hide_apps"] / ["hide_models"] — surface them.
        from django.conf import settings as _settings
        jset = getattr(_settings, "JAZZMIN_SETTINGS", {}) or {}
        hide_apps = jset.get("hide_apps", [])
        hide_models = jset.get("hide_models", [])

        log.info(
            "admin_index_diag "
            "template=%r index_template_attr=%r "
            "app_list_len=%s available_apps_len=%s app_names=%r "
            "registry_len=%s "
            "user_id=%s username=%r is_superuser=%s is_staff=%s "
            "schema_name=%r "
            "jazzmin_hide_apps=%r jazzmin_hide_models=%r",
            _flatten_template_name(response),
            idx_tpl,
            app_len,
            avail_len,
            app_names,
            registry_len,
            getattr(request.user, "pk", None),
            getattr(request.user, "get_username", lambda: "")(),
            getattr(request.user, "is_superuser", False),
            getattr(request.user, "is_staff", False),
            schema,
            hide_apps,
            hide_models,
        )

        return response
