# dose/services/atomic_service_selector.py
"""Filter/group Instruction Atomic Service choices by app + category (KISS)."""
from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

KNOWN_ATOMIC_APPS = ("odoo", "nextcloud", "mattermost", "hubspot", "dolibarr")

CATEGORY_ORDER = (
    ("capture", "Capture"),
    ("orchestration", "Orchestration / HITL"),
    ("write", "Write / Create"),
    ("notify", "Notify"),
    ("integration", "Integration-specific"),
    ("other", "Other"),
)

_PATH_APP_HINTS = (
    (("action_id", "menu_id"), "odoo"),
    (("/web/", "/web?", "/odoo/", "/web/dataset", "/web/action"), "odoo"),
    (("/apps/", "/ocs/", "/remote.php/", "/index.php/apps/", "/dist/"), "nextcloud"),
    (("/api/v4/", "/plugins/", "/channels/"), "mattermost"),
    (("/crm/", "/contacts/", "/hs-fs/", "/hubspot"), "hubspot"),
    (("/htdocs/", "/societe/", "/compta/", "/dolibarr"), "dolibarr"),
)


def _norm_apps(cls) -> tuple:
    raw = getattr(cls, "atomic_apps", None) or ()
    if isinstance(raw, str):
        raw = (raw,)
    return tuple(str(a).strip().lower() for a in raw if str(a).strip())


def service_visible_for_app(cls, app_key: str | None) -> bool:
    """Empty/generic apps → every endpoint. Otherwise current app must match."""
    if not app_key:
        return True
    apps = _norm_apps(cls)
    if not apps or "generic" in apps:
        return True
    return app_key.strip().lower() in apps


def service_category_key(cls) -> str:
    raw = (getattr(cls, "atomic_category", None) or "").strip().lower()
    known = {k for k, _ in CATEGORY_ORDER}
    return raw if raw in known else "other"


def app_key_from_endpoint(endpoint) -> str:
    if endpoint is None:
        return ""
    slug = str(getattr(endpoint, "slug", "") or "").lower().strip()
    if slug in KNOWN_ATOMIC_APPS:
        return slug
    url = str(getattr(endpoint, "endpoint_url", "") or "").lower()
    title = str(getattr(endpoint, "menu_title", "") or "").lower()
    blob = f"{slug} {url} {title}"
    for key in KNOWN_ATOMIC_APPS:
        if key in blob:
            return key
    return ""


def app_key_from_requestpath(requestpath: str, match_type: str = "") -> str:
    mt = (match_type or "").strip().lower()
    if mt in ("action_id", "menu_id"):
        return "odoo"
    path = (requestpath or "").strip().lower()
    if not path:
        return ""
    if not path.startswith("/"):
        path = "/" + path
    for needles, key in _PATH_APP_HINTS:
        if needles == ("action_id", "menu_id"):
            continue
        if any(n in path for n in needles):
            return key
    return ""


def _app_key_from_referer(referer: str) -> str:
    ref = (referer or "").strip()
    if not ref:
        return ""
    try:
        from dose.models import PassThroughEndpoint
    except Exception:
        return ""

    m = re.search(r"/pt/polysniff/(\d+)", ref)
    if m:
        try:
            ep = PassThroughEndpoint.objects.filter(pk=int(m.group(1))).first()
        except Exception:
            ep = None
        return app_key_from_endpoint(ep)

    m = re.search(r"/pt/admin/([^/?#]+)", ref)
    if not m:
        return ""
    host = unquote(m.group(1)).strip().lower()
    if not host:
        return ""
    try:
        for ep in PassThroughEndpoint.objects.filter(is_enabled=True):
            netloc = urlparse(getattr(ep, "endpoint_url", "") or "").netloc.lower()
            if netloc == host or host in netloc or netloc in host:
                return app_key_from_endpoint(ep)
    except Exception:
        return ""
    return ""


def infer_atomic_app_key(request) -> str:
    """Current bundled app for the Instruction selector, or empty (show all)."""
    if request is None:
        return ""
    q = (getattr(request, "GET", None) or {}).get("app") or ""
    q = str(q).strip().lower()
    if q in KNOWN_ATOMIC_APPS:
        return q
    path = str((getattr(request, "GET", None) or {}).get("requestpath") or "")
    match_type = str((getattr(request, "GET", None) or {}).get("match_type") or "")
    hinted = app_key_from_requestpath(path, match_type)
    if hinted:
        return hinted
    meta = getattr(request, "META", None) or {}
    return _app_key_from_referer(meta.get("HTTP_REFERER") or "")


def grouped_executescript_choices(names, *, current_value="", app_key="", registry=None):
    """
    Django grouped choices: category optgroups, Custom Endpoint last.
    Always keeps current_value so existing instructions still edit.
    """
    from dose.services.atomic_services_registry import (
        ATOMIC_SERVICE_REGISTRY,
        CUSTOM_ENDPOINT_LABEL,
        TENANT_SPECIFIC_SERVICES,
    )

    reg = registry if registry is not None else ATOMIC_SERVICE_REGISTRY
    current = (current_value or "").strip()
    grouped = {key: [] for key, _ in CATEGORY_ORDER}
    visible = set()

    def _cls_for(name):
        if name in reg:
            return reg[name]
        for tenant_map in TENANT_SPECIFIC_SERVICES.values():
            if name in tenant_map:
                return tenant_map[name]
        return None

    for name in names:
        cls = _cls_for(name)
        if cls is not None and not service_visible_for_app(cls, app_key) and name != current:
            continue
        cat = service_category_key(cls) if cls is not None else "other"
        grouped[cat].append((name, name))
        visible.add(name)

    if current and current not in visible:
        grouped["other"].insert(0, (current, f"{current} (saved — not in registry)"))

    choices = [("", CUSTOM_ENDPOINT_LABEL)]
    for key, label in CATEGORY_ORDER:
        items = grouped[key]
        if items:
            choices.append((label, items))
    return choices


def count_service_choices(choices) -> int:
    n = 0
    for value, label in choices:
        if isinstance(label, (list, tuple)):
            n += sum(1 for v, _ in label if v)
        elif value:
            n += 1
    return n
