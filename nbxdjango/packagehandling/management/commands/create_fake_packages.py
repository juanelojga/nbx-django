from django.core.management.base import BaseCommand
from packagehandling.factories import PackageFactory

class Command(BaseCommand):
    help = 'Creates fake packages'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='The number of packages to create')

    def handle(self, *args, **options):
        count = options['count']
        packages = PackageFactory.create_batch(count)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(packages)} packages'))
