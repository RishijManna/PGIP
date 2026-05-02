from django.core.management import call_command
from django.core.management.base import BaseCommand

from my_app.services.seed_rag import build_seed_rag_index


class Command(BaseCommand):
    help = "Build a local RAG vector index from seeded exams, schemes, and jobs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed-first",
            action="store_true",
            help="Run seed_data before building the RAG index.",
        )

    def handle(self, *args, **options):
        if options["seed_first"]:
            call_command("seed_data", verbosity=0)

        stats = build_seed_rag_index()
        self.stdout.write(
            self.style.SUCCESS(
                "Built seed RAG index: "
                f"{stats['records']} records "
                f"({stats['exams']} exams, {stats['schemes']} schemes, "
                f"{stats['jobs']} jobs) at {stats['path']}."
            )
        )
