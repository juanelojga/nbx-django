import random

import factory
from faker import Faker

from .models import Client, CustomUser, Package

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "password")


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client
        django_get_or_create = ("email",)

    user = factory.SubFactory(UserFactory)
    first_name = factory.LazyAttribute(lambda o: o.user.first_name)
    last_name = factory.LazyAttribute(lambda o: o.user.last_name)
    email = factory.LazyAttribute(lambda o: o.user.email)
    identification_number = factory.Faker("ssn")
    state = factory.Faker("state")
    city = factory.Faker("city")
    main_street = factory.Faker("street_name")
    secondary_street = factory.Faker("street_name")
    building_number = factory.Faker("building_number")
    mobile_phone_number = factory.Faker("phone_number")
    phone_number = factory.Faker("phone_number")


class PackageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Package

    barcode = factory.Faker("ean", length=13)
    courier = factory.Faker("company")
    other_courier = factory.LazyFunction(lambda: fake.company() if random.randint(0, 100) < 30 else None)
    length = factory.Faker(
        "pyfloat",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=10.0,
        max_value=100.0,
    )
    width = factory.Faker(
        "pyfloat",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=10.0,
        max_value=100.0,
    )
    height = factory.Faker(
        "pyfloat",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=10.0,
        max_value=100.0,
    )
