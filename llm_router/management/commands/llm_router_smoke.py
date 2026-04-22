"""Exercise the in-process LLM router (classification + optional live API call)."""

from django.core.management.base import BaseCommand, CommandError

from llm_router.providers import complete_chat
from llm_router.router import route


class Command(BaseCommand):
    help = "Print RoutePlan for a sample prompt; optionally call the provider (costs API usage)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prompt",
            default="Say hello in one short sentence.",
            help="Prompt text used for routing (and API if --call).",
        )
        parser.add_argument(
            "--task-hint",
            dest="task_hint",
            default="",
            help="Optional hint: code, analysis, chat, agent, ...",
        )
        parser.add_argument(
            "--tier",
            dest="user_tier",
            default="standard",
            help="User tier: free, standard, premium, staff",
        )
        parser.add_argument(
            "--call",
            action="store_true",
            help="If set, invoke the provider after routing (uses API keys).",
        )

    def handle(self, *args, **options):
        prompt = options["prompt"] or ""
        task_hint = (options.get("task_hint") or "").strip() or None
        tier = options.get("user_tier") or "standard"

        plan = route(prompt=prompt, task_hint=task_hint, user_tier=tier)
        self.stdout.write(
            f"RoutePlan: provider={plan.provider!r} model={plan.model!r} "
            f"bucket={plan.task_bucket!r} tier={plan.user_tier!r} reason={plan.reason!r}"
        )

        if not options.get("call"):
            self.stdout.write(self.style.WARNING("Omit --call to avoid API usage. Re-run with --call to invoke."))
            return

        messages = [{"role": "user", "content": prompt}]
        try:
            text = complete_chat(
                plan,
                messages=messages,
                system_prompt="You are a concise assistant.",
                max_tokens=256,
            )
        except Exception as exc:
            raise CommandError(f"Provider call failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("--- response (truncated) ---"))
        self.stdout.write(text[:2000])
