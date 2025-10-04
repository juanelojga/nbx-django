import random

from django.core.management.base import BaseCommand
from packagehandling.factories import ClientFactory, PackageFactory


class Command(BaseCommand):
    help = "Creates fake clients, users, and packages"

    def handle(self, *args, **options):
        self.stdout.write("Creating 10 fake clients and users...")
        clients = ClientFactory.create_batch(10)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(clients)} clients and users."
            )
        )

        self.stdout.write("Creating 100 fake packages...")
        packages = []
        for _ in range(100):
            client = random.choice(clients)
            package = PackageFactory(client=client)
            packages.append(package)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {len(packages)} packages.")
        )
