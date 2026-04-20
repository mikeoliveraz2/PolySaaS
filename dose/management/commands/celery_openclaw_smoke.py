from django.core.management.base import BaseCommand

from dose.tasks import openclaw_render_smoke


class Command(BaseCommand):
    help = (
        "Enqueue the OpenClaw/Celery smoke test task (dose.openclaw_render_smoke). "
        "Run on the web service or any shell with broker + Django env; watch the worker logs."
    )

    def handle(self, *args, **options):
        async_result = openclaw_render_smoke.delay()
        self.stdout.write(
            self.style.SUCCESS(f"Enqueued dose.openclaw_render_smoke task_id={async_result.id}")
        )
