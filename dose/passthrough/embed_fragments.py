"""
Passthrough embed fragments — same head/body/scope contract as forwarding._wrap_in_admin_template.

Used by admin passthrough_embed.html and PolySniffer workspace inline passthrough.
"""
from __future__ import annotations

import logging

from django.utils.safestring import mark_safe

from dose.passthrough.forwarding import _extract_head_and_body, _extract_upstream_root_classes

logger = logging.getLogger(__name__)


def build_scoped_embed_fragments(html_str: str, trigger: str, handler=None, request=None):
    """Return (embed_head, embed_body) matching admin passthrough_embed scope div."""
    head_content, body_content = _extract_head_and_body(html_str or "")
    upstream_root_classes = _extract_upstream_root_classes(html_str or "")
    scope_extra_classes = upstream_root_classes
    if handler and hasattr(handler, "passthrough_embed_scope_classes"):
        try:
            scope_extra_classes = (
                handler.passthrough_embed_scope_classes(
                    request,
                    html_str or "",
                    upstream_root_classes,
                )
                or upstream_root_classes
            )
        except Exception as exc:
            logger.warning("passthrough_embed_scope_classes failed: %s", exc)

    scope_class = "polysaas-passthrough-scope"
    if scope_extra_classes:
        scope_class = f"{scope_class} {scope_extra_classes.strip()}"

    display_mode = ""
    if handler and hasattr(handler, "_polysaas_display_mode"):
        try:
            display_mode = handler._polysaas_display_mode(request) or ""
        except Exception:
            display_mode = ""

    norm = (trigger or "").strip("/")
    embed_body = mark_safe(
        f'<div class="{scope_class}" data-polysaas-embed-trigger="{norm}"'
        f' data-polysaas-display-mode="{display_mode}"'
        f' data-polysniffer-workspace-pt="1">'
        f"{body_content}</div>"
    )
    embed_head = mark_safe(head_content)
    return embed_head, embed_body
