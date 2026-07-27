"""Backward-compatible alias for legacy module name.

Prefer DJANGO_SETTINGS_MODULE=mysite.settings_hosted.
"""

from mysite.settings_hosted import *  # noqa: F401,F403
