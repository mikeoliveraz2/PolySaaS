"""
Legacy import path — production middleware lives in dose.passthrough.middleware.

Settings should reference:
    dose.passthrough.middleware.ExternalPassthroughMiddleware

This module re-exports the same class so older references keep working.
"""
from dose.passthrough.middleware import ExternalPassthroughMiddleware

__all__ = ["ExternalPassthroughMiddleware"]
