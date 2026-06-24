"""
PolySniffer 2.0 — delegate native sniff body rewrites to endpoint handlers.

Handlers register via register_native_sniff_processor() (no frozen-file edits).
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

NativeSniffProcessor = Callable[..., Optional[bytes]]

_PROCESSORS: dict[type, NativeSniffProcessor] = {}


def register_native_sniff_processor(handler_cls: type, processor: NativeSniffProcessor) -> None:
    _PROCESSORS[handler_cls] = processor
    logger.debug("Registered native sniff processor for %s", handler_cls.__name__)


def apply_native_sniff_rewrites(
    body: bytes,
    *,
    content_type: str,
    request,
    endpoint,
    upstream_path: str,
    proxy_prefix: str,
) -> bytes:
    from dose.passthrough.registry import resolve_handler_for_endpoint

    from dose.polysniffer.sniff_native_rewrite import rewrite_generic_native_fallback

    handler = resolve_handler_for_endpoint(endpoint)
    if handler is not None:
        processor = _PROCESSORS.get(type(handler))
        if processor is not None:
            try:
                rewritten = processor(
                    handler,
                    body,
                    content_type,
                    request,
                    endpoint_url=endpoint.endpoint_url,
                    upstream_path=upstream_path,
                    proxy_prefix=proxy_prefix,
                )
                if rewritten is not None:
                    return rewritten
            except Exception:
                logger.exception(
                    "Native sniff processor failed for %s", type(handler).__name__
                )

    return rewrite_generic_native_fallback(
        body,
        content_type=content_type,
        upstream_path=upstream_path,
        proxy_prefix=proxy_prefix,
        endpoint_url=endpoint.endpoint_url,
    )
