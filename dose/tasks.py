"""
Celery tasks for the dose app (autodiscovered via mysite.celery app.autodiscover_tasks()).

OpenClaw naming here refers to the product's AI-orchestration / peer stack smoke tests,
not an external OpenClaw gateway binary.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="dose.openclaw_render_smoke")
def openclaw_render_smoke(self):
    """
    Lightweight Celery smoke test for Render (or any broker-backed deploy).

    - No external AI HTTP calls (no API keys required).
    - Log line is easy to grep in the PolySaaS-Celery-Worker Render logs.
    """
    msg = "OpenClaw test task executed successfully (Celery worker smoke test)"
    logger.info("%s task_id=%s", msg, self.request.id)
    return msg
