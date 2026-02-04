import random

from django.core.management.base import BaseCommand

from packagehandling.factories import ClientFactory, PackageFactory
from packagehandling.models import Client, Consolidate


class Command(BaseCommand):
    help = "Creates fake packages for clients"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of packages to create (default: 100)",
        )
        parser.add_argument(
            "--client-id",
            type=int,
            help="Create packages for a specific client by ID",
        )
        parser.add_argument(
            "--client-email",
            type=str,
            help="Create packages for a specific client by email",
        )
        parser.add_argument(
            "--consolidate-id",
            type=int,
            help="Assign packages to a specific consolidation by ID",
        )
        parser.add_argument(
            "--with-consolidation",
            action="store_true",
            help="Randomly assign some packages to existing consolidations",
        )

    def handle(self, *args, **options):
        count = options["count"]
        client_id = options["client_id"]
        client_email = options["client_email"]
        consolidate_id = options["consolidate_id"]
        with_consolidation = options["with_consolidation"]

        # Determine the client
        client = None
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                self.stdout.write(f"Using client: {client.full_name} (ID: {client.id})")
            except Client.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Client with ID {client_id} not found"))
                return
        elif client_email:
            try:
                client = Client.objects.get(email=client_email)
                self.stdout.write(f"Using client: {client.full_name} (ID: {client.id})")
            except Client.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Client with email '{client_email}' not found"))
                return

        # Determine the consolidation
        consolidate = None
        if consolidate_id:
            try:
                consolidate = Consolidate.objects.get(id=consolidate_id)
                self.stdout.write(f"Using consolidation: {consolidate} (ID: {consolidate.id})")
                # If consolidation is specified, use its client
                if not client:
                    client = consolidate.client
                    self.stdout.write(f"Using consolidation's client: {client.full_name}")
                elif client != consolidate.client:
                    self.stdout.write(self.style.ERROR(
                        f"Specified client ({client}) does not match consolidation's client ({consolidate.client})"
                    ))
                    return
            except Consolidate.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Consolidation with ID {consolidate_id} not found"))
                return

        # Get available consolidations for the client if needed
        available_consolidates = []
        if with_consolidation and client:
            available_consolidates = list(Consolidate.objects.filter(client=client))
            if available_consolidates:
                self.stdout.write(f"Found {len(available_consolidates)} consolidations for assignment")

        # Get all clients if no specific client
        all_clients = None
        if not client:
            all_clients = list(Client.objects.all())
            if not all_clients:
                self.stdout.write("No clients found. Creating some clients first...")
                all_clients = ClientFactory.create_batch(5)
                self.stdout.write(f"Created {len(all_clients)} new clients")

        # Create packages
        self.stdout.write(f"Creating {count} fake packages...")
        packages = []

        for i in range(count):
            # Determine which client to use
            pkg_client = client
            if not pkg_client:
                pkg_client = random.choice(all_clients)

            # Determine consolidation
            pkg_consolidate = consolidate
            if not pkg_consolidate and with_consolidation and available_consolidates:
                # 50% chance to assign to a consolidation
                if random.random() < 0.5:
                    pkg_consolidate = random.choice(available_consolidates)

            # Create package
            package = PackageFactory(
                client=pkg_client,
                consolidate=pkg_consolidate,
            )
            packages.append(package)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {len(packages)} packages."
        ))

        # Show summary
        if consolidate:
            self.stdout.write(f"All packages assigned to consolidation: {consolidate}")
        elif client:
            count_with_consolidation = sum(1 for p in packages if p.consolidate)
            self.stdout.write(f"Client: {client.full_name}")
            self.stdout.write(f"  - Packages with consolidation: {count_with_consolidation}")
            self.stdout.write(f"  - Packages without consolidation: {len(packages) - count_with_consolidation}")
