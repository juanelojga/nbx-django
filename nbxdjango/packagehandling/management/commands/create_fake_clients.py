from django.core.management.base import BaseCommand
from packagehandling.factories import ClientFactory


class Command(BaseCommand):
    help = "Creates fake clients with associated users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of clients to create (default: 10)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        self.stdout.write(f"Creating {count} fake clients with users...")

        clients = ClientFactory.create_batch(count)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(clients)} clients with associated users."))

        for client in clients:
            self.stdout.write(f"  - {client.full_name} ({client.email})")
