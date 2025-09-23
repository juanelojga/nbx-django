import factory
import random
from faker import Faker
from .models import Package

fake = Faker()

class PackageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Package

    barcode = factory.Faker('ean', length=13)
    courier = factory.Faker('company')
    other_courier = factory.LazyFunction(lambda: fake.company() if random.random() < 0.3 else None)
    length = factory.Faker('pyfloat', left_digits=2, right_digits=2, positive=True, min_value=10.0, max_value=100.0)
    width = factory.Faker('pyfloat', left_digits=2, right_digits=2, positive=True, min_value=10.0, max_value=100.0)
    height = factory.Faker('pyfloat', left_digits=2, right_digits=2, positive=True, min_value=10.0, max_value=100.0)
    dimension_unit = factory.Faker('random_element', elements=['cm', 'in'])
    weight = factory.Faker('pyfloat', left_digits=2, right_digits=2, positive=True, min_value=0.5, max_value=50.0)
    weight_unit = factory.Faker('random_element', elements=['kg', 'lb'])
    description = factory.Faker('sentence', nb_words=6)
    purchase_link = factory.Faker('url')
    real_price = factory.Faker('pyfloat', left_digits=3, right_digits=2, positive=True, min_value=1.0, max_value=500.0)
    service_price = factory.Faker('pyfloat', left_digits=3, right_digits=2, positive=True, min_value=1.0, max_value=500.0)
    arrival_date = factory.Faker('past_date')
    client_id = factory.Faker('pyint', min_value=1, max_value=100)

if __name__ == '__main__':
    # This part is for demonstration and won't run when imported by Django.
    # To run this, you need to configure Django settings first.
    import os
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nbxdjango.settings')
    django.setup()

    # Create 10 fake Package objects
    packages = PackageFactory.create_batch(10)

    for package in packages:
        print(f"Created Package: {package.barcode} for client {package.client_id}")
