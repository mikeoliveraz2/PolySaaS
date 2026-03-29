from django.core.management.base import BaseCommand
from django.core.management import call_command
from dose.management.schema_utils import set_search_path


class Command(BaseCommand):
    help = (
        "Runs migrate once: public schema, then each tenant schema (via dose.management.commands.migrate). "
        "Does not duplicate full migrate passes per tenant. "
        "Optional: --makemigrations before migrate (off by default)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--makemigrations",
            action="store_true",
            help="Run makemigrations before migrate (use when you have model changes).",
        )
        parser.add_argument(
            "--no-input",
            "--noinput",
            action="store_true",
            dest="no_input",
            help="Non-interactive migrate (forwarded to migrate).",
        )

    def handle(self, *args, **options):
        if options["makemigrations"]:
            self.stdout.write(self.style.SUCCESS("Running makemigrations..."))
            call_command("makemigrations")

        # Tenant rows live in public; ensure we read them from public before migrate
        set_search_path("public")

        self.stdout.write(
            self.style.SUCCESS(
                "Running migrate (public + all tenant schemas, single coordinated pass)..."
            )
        )
        interactive = options.get("interactive", True) and not options.get("no_input", False)
        call_command(
            "migrate",
            verbosity=options.get("verbosity", 1),
            interactive=interactive,
        )
        self.stdout.write(self.style.SUCCESS("\n[OK] migrate_all_schemas finished."))
