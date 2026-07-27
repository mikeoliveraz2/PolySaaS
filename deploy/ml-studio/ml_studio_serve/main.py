"""
Machine Learning Studio — standalone service (phase 1).

Django still owns ML metadata tables (MLEngine, MLDataset, etc.) via the `ml_studio`
admin proxies. This container is the future home for notebooks, training UI, and
heavy dependencies without bloating PolySaaS-Core.
"""
from __future__ import annotations

import logging
import os

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

logger = logging.getLogger("ml_studio_serve")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


def _core_base() -> str:
    return os.environ.get("POLYSAAS_CORE_BASE_URL", "").strip().rstrip("/")


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "ml-studio"})


async def home(_: Request) -> HTMLResponse:
    core = _core_base()
    core_note = (
        f"<p>PolySaaS Core (metadata / admin): <a href=\"{core}/admin/\">{core}/admin/</a> "
        "&mdash; Machine Learning Studio section lists engines, datasets, prompts.</p>"
        if core
        else "<p>Set <code>POLYSAAS_CORE_BASE_URL</code> to link to your Django admin.</p>"
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Machine Learning Studio</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem;
            line-height: 1.5; color: #1a1a1a; }}
    code {{ background: #f4f4f5; padding: 0.15em 0.35em; border-radius: 4px; }}
    .tag {{ color: #666; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Machine Learning Studio</h1>
  <p class="tag">Scaffold &mdash; UI and ML libraries will land here; Core keeps the database models today.</p>
  {core_note}
  <p>API health: <a href="/health"><code>/health</code></a></p>
</body>
</html>"""
    return HTMLResponse(html)


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/", home, methods=["GET"]),
]

app = Starlette(debug=False, routes=routes)
