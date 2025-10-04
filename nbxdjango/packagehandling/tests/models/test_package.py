from datetime import date

import pytest
from packagehandling.models.client import Client
from packagehandling.models.package import Package
from packagehandling.models.user import CustomUser


@pytest.fixture
def create_client():
    user = CustomUser.objects.create_user(email="client_package@example.com", password="password123")
    client = Client.objects.create(
        user=user,
        first_name="Package",
        last_name="Client",
        email="package.client@example.com",
        identification_number="12345",
        state="ST",
        city="City",
        main_street="Main",
        secondary_street="Second",
        building_number="1",
        mobile_phone_number="123",
        phone_number="456",
    )
    return client


@pytest.mark.django_db
def test_package_creation(create_client):
    client = create_client
    package = Package.objects.create(
        barcode="1234567890123",
        courier="FedEx",
        other_courier=None,
        length=10.5,
        width=5.0,
        height=2.0,
        dimension_unit="cm",
        weight=1.2,
        weight_unit="kg",
        description="Test package description",
        purchase_link="http://example.com/purchase",
        real_price=100.00,
        service_price=10.00,
        arrival_date=date(2025, 1, 1),
        client=client,
    )
    assert package.barcode == "1234567890123"
    assert package.courier == "FedEx"
    assert package.other_courier is None
    assert package.length == 10.5
    assert package.width == 5.0
    assert package.height == 2.0
    assert package.dimension_unit == "cm"
    assert package.weight == 1.2
    assert package.weight_unit == "kg"
    assert package.description == "Test package description"
    assert package.purchase_link == "http://example.com/purchase"
    assert package.real_price == 100.00
    assert package.service_price == 10.00
    assert package.arrival_date == date(2025, 1, 1)
    assert package.client == client
    assert package.created_at is not None
    assert package.updated_at is not None


@pytest.mark.django_db
def test_package_str_method(create_client):
    client = create_client
    package = Package.objects.create(
        barcode="ABCDEFGHIJKLM",
        courier="DHL",
        length=1.0,
        width=1.0,
        height=1.0,
        dimension_unit="in",
        weight=0.5,
        weight_unit="lb",
        real_price=50.00,
        service_price=5.00,
        arrival_date=date(2025, 1, 2),
        client=client,
    )
    assert str(package) == "Package ABCDEFGHIJKLM"


@pytest.mark.django_db
def test_package_nullable_fields(create_client):
    client = create_client
    package = Package.objects.create(
        barcode="NULLABLE12345",
        courier="UPS",
        length=1.0,
        width=1.0,
        height=1.0,
        dimension_unit="cm",
        weight=1.0,
        weight_unit="kg",
        description=None,
        purchase_link=None,
        other_courier="Some Other Courier",
        real_price=1.00,
        service_price=1.00,
        arrival_date=date(2025, 1, 3),
        client=client,
    )
    assert package.description is None
    assert package.purchase_link is None
    assert package.other_courier == "Some Other Courier"
