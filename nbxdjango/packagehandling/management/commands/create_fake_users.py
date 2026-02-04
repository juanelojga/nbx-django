from django.core.management.base import BaseCommand
from packagehandling.factories import UserFactory


class Command(BaseCommand):
    help = "Creates fake users (without clients)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of users to create (default: 10)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="password",
            help="Password for created users (default: 'password')",
        )

    def handle(self, *args, **options):
        count = options["count"]
        password = options["password"]

        self.stdout.write(f"Creating {count} fake users...")

        users = UserFactory.create_batch(count, password=password)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(users)} users."))

        for user in users:
            self.stdout.write(f"  - {user.email} (password: {password})")
