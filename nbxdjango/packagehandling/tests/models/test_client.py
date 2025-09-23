import pytest
from django.db.utils import IntegrityError
from packagehandling.models.client import Client
from packagehandling.models.user import CustomUser

@pytest.mark.django_db
def test_client_creation():
    user = CustomUser.objects.create_user(email='client@example.com', password='password123')
    client = Client.objects.create(
        user=user,
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        identification_number='123456789',
        state='CA',
        city='Los Angeles',
        main_street='Main St',
        secondary_street='Second St',
        building_number='123',
        mobile_phone_number='555-123-4567',
        phone_number='555-789-0123',
    )
    assert client.user == user
    assert client.first_name == 'John'
    assert client.last_name == 'Doe'
    assert client.email == 'john.doe@example.com'
    assert client.identification_number == '123456789'
    assert client.state == 'CA'
    assert client.city == 'Los Angeles'
    assert client.main_street == 'Main St'
    assert client.secondary_street == 'Second St'
    assert client.building_number == '123'
    assert client.mobile_phone_number == '555-123-4567'
    assert client.phone_number == '555-789-0123'
    assert client.created_at is not None
    assert client.updated_at is not None

@pytest.mark.django_db
def test_client_full_name_property():
    user = CustomUser.objects.create_user(email='client2@example.com', password='password123')
    client = Client.objects.create(
        user=user,
        first_name='Jane',
        last_name='Smith',
        email='jane.smith@example.com',
        identification_number='987654321',
        state='NY',
        city='New York',
        main_street='Broadway',
        secondary_street='Fifth Ave',
        building_number='456',
        mobile_phone_number='555-987-6543',
        phone_number='555-321-0987',
    )
    assert client.full_name == 'Jane Smith'

@pytest.mark.django_db
def test_client_str_method():
    user = CustomUser.objects.create_user(email='client3@example.com', password='password123')
    client = Client.objects.create(
        user=user,
        first_name='Peter',
        last_name='Jones',
        email='peter.jones@example.com',
        identification_number='112233445',
        state='TX',
        city='Houston',
        main_street='Main St',
        secondary_street='Elm St',
        building_number='789',
        mobile_phone_number='555-111-2233',
        phone_number='555-444-5566',
    )
    assert str(client) == 'Peter Jones'

@pytest.mark.django_db
def test_client_user_one_to_one_constraint():
    user1 = CustomUser.objects.create_user(email='user1@example.com', password='password123')
    Client.objects.create(
        user=user1,
        first_name='Client',
        last_name='One',
        email='client1@example.com',
        identification_number='1',
        state='S1',
        city='C1',
        main_street='MS1',
        secondary_street='SS1',
        building_number='B1',
        mobile_phone_number='M1',
        phone_number='P1',
    )
    with pytest.raises(IntegrityError):
        # Cannot create another client with the same user
        Client.objects.create(
            user=user1,
            first_name='Client',
            last_name='Two',
            email='client2@example.com',
            identification_number='2',
            state='S2',
            city='C2',
            main_street='MS2',
            secondary_street='SS2',
            building_number='B2',
            mobile_phone_number='M2',
            phone_number='P2',
        )

@pytest.mark.django_db
def test_client_user_nullable():
    client = Client.objects.create(
        user=None,
        first_name='No',
        last_name='User',
        email='nouser@example.com',
        identification_number='000000000',
        state='XX',
        city='None',
        main_street='None',
        secondary_street='None',
        building_number='0',
        mobile_phone_number='000-000-0000',
        phone_number='000-000-0000',
    )
    assert client.user is None
