import random

from django.core.management.base import BaseCommand

from packagehandling.factories import ClientFactory, ConsolidateFactory, PackageFactory
from packagehandling.models import Client


class Command(BaseCommand):
    help = "Creates fake consolidations for clients"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of consolidations to create (default: 10)",
        )
        parser.add_argument(
            "--client-id",
            type=int,
            help="Create consolidations for a specific client by ID",
        )
        parser.add_argument(
            "--client-email",
            type=str,
            help="Create consolidations for a specific client by email",
        )
        parser.add_argument(
            "--packages",
            type=int,
            default=0,
            help="Number of packages to create for each consolidation (default: 0)",
        )
        parser.add_argument(
            "--packages-min",
            type=int,
            default=1,
            help="Minimum packages per consolidation when using --packages (default: 1)",
        )
        parser.add_argument(
            "--packages-max",
            type=int,
            default=5,
            help="Maximum packages per consolidation when using --packages (default: 5)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        client_id = options["client_id"]
        client_email = options["client_email"]
        packages_count = options["packages"]
        packages_min = options["packages_min"]
        packages_max = options["packages_max"]

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

        # Get all clients if no specific client
        all_clients = None
        if not client:
            all_clients = list(Client.objects.all())
            if not all_clients:
                self.stdout.write("No clients found. Creating some clients first...")
                all_clients = ClientFactory.create_batch(5)
                self.stdout.write(f"Created {len(all_clients)} new clients")

        # Create consolidations
        self.stdout.write(f"Creating {count} fake consolidations...")
        consolidations = []

        for i in range(count):
            # Determine which client to use
            cons_client = client
            if not cons_client:
                cons_client = random.choice(all_clients)

            # Create consolidation
            consolidation = ConsolidateFactory(client=cons_client)
            consolidations.append(consolidation)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {len(consolidations)} consolidations."
        ))

        # Create packages for consolidations if requested
        total_packages = 0
        if packages_count > 0:
            self.stdout.write(f"Creating packages for consolidations...")
            
            for consolidation in consolidations:
                # Determine number of packages for this consolidation
                num_packages = packages_count
                if packages_min != packages_max:
                    num_packages = random.randint(packages_min, packages_max)
                
                for _ in range(num_packages):
                    PackageFactory(
                        client=consolidation.client,
                        consolidate=consolidation,
                    )
                total_packages += num_packages
                self.stdout.write(
                    f"  - {consolidation}: {num_packages} packages",
                    self.style.HTTP_NOT_MODIFIED,
                )

            self.stdout.write(self.style.SUCCESS(
                f"Total packages created: {total_packages}"
            ))

        # Show summary
        if client:
            self.stdout.write(f"All consolidations belong to: {client.full_name}")
