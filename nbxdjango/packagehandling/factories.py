import random

import factory
from faker import Faker

from .models import Client, Consolidate, CustomUser, Package

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_superuser = False
    is_staff = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("password")


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

    client = factory.SubFactory(ClientFactory)
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


class ConsolidateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Consolidate

    description = factory.Faker("text", max_nb_chars=200)
    status = factory.Faker(
        "random_element",
        elements=[choice[0] for choice in Consolidate.Status.choices],
    )
    delivery_date = factory.Faker(
        "date_between",
        start_date="-30d",
        end_date="+30d",
    )
    comment = factory.Faker("text", max_nb_chars=100)
    client = factory.SubFactory(ClientFactory)
    extra_attributes = factory.LazyFunction(dict)
