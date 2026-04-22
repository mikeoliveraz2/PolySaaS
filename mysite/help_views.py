"""Staff-facing in-app help (Jazzmin user menu links to /help/)."""

from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def help_index(request):
    """Help home — linked from Jazzmin Help → /help/."""
    return render(
        request,
        "mysite/help_index.html",
        {
            "title": "PolySaaS help",
        },
    )


@staff_member_required
def help_llm_router(request):
    """LLM router & OpenClaw-style routing (Options 1 & 2)."""
    return render(
        request,
        "mysite/help_llm_router.html",
        {
            "title": "LLM router & OpenClaw",
        },
    )
