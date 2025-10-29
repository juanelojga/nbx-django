import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.utils import IntegrityError
from django.test import RequestFactory
from graphql.type import GraphQLResolveInfo as ResolveInfo
from packagehandling.factories import ClientFactory, UserFactory
from packagehandling.models import Client
from packagehandling.schema.mutation_parts.client_mutations import (
    CreateClient,
    DeleteClient,
    UpdateClient,
)

User = get_user_model()


@pytest.fixture
def info_with_user_factory():
    def factory(user):
        request_factory = RequestFactory()
        request = request_factory.get("/graphql/")
        request.user = user
        return ResolveInfo(
            field_name="",
            field_nodes=[],
            return_type=None,
            parent_type=None,
            path=None,
            schema=None,
            fragments=None,
            root_value=None,
            operation=None,
            variable_values=None,
            context=request,
            is_awaitable=lambda: False,
        )

    return factory


@pytest.mark.django_db
class TestCreateClient:
    def test_create_client_as_superuser_with_all_fields(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = CreateClient()
        result = mutation.mutate(
            info,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            identification_number="123456789",
            state="California",
            city="Los Angeles",
            main_street="Main St",
            secondary_street="Second St",
            building_number="123",
            mobile_phone_number="+1234567890",
            phone_number="+0987654321",
        )

        assert result.client.first_name == "John"
        assert result.client.last_name == "Doe"
        assert result.client.email == "john.doe@example.com"
        assert result.client.identification_number == "123456789"
        assert result.client.state == "California"
        assert result.client.city == "Los Angeles"
        assert result.client.main_street == "Main St"
        assert result.client.secondary_street == "Second St"
        assert result.client.building_number == "123"
        assert result.client.mobile_phone_number == "+1234567890"
        assert result.client.phone_number == "+0987654321"

        # Verify that a User was created
        created_user = User.objects.get(email="john.doe@example.com")
        assert created_user.username == "john.doe@example.com"
        assert created_user.is_active is False
        assert result.client.user == created_user

        # Verify that Client was saved to database
        assert Client.objects.filter(email="john.doe@example.com").exists()

    def test_create_client_as_superuser_with_required_fields_only(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = CreateClient()
        result = mutation.mutate(
            info,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
        )

        assert result.client.first_name == "Jane"
        assert result.client.last_name == "Smith"
        assert result.client.email == "jane.smith@example.com"
        assert result.client.identification_number is None
        assert result.client.state is None
        assert result.client.city is None
        assert result.client.main_street is None
        assert result.client.secondary_street is None
        assert result.client.building_number is None
        assert result.client.mobile_phone_number is None
        assert result.client.phone_number is None

        # Verify that a User was created
        created_user = User.objects.get(email="jane.smith@example.com")
        assert created_user.username == "jane.smith@example.com"
        assert created_user.is_active is False
        assert result.client.user == created_user

    def test_create_client_as_regular_user_raises_permission_denied(self, info_with_user_factory):
        regular_user = UserFactory(is_superuser=False)
        info = info_with_user_factory(regular_user)

        mutation = CreateClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(
                info,
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
            )

    def test_create_client_with_duplicate_email(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        # Create existing user with email
        UserFactory(email="duplicate@example.com")

        mutation = CreateClient()
        with pytest.raises(IntegrityError):
            mutation.mutate(
                info,
                first_name="John",
                last_name="Doe",
                email="duplicate@example.com",
            )


@pytest.mark.django_db
class TestUpdateClient:
    def test_update_client_as_superuser(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory(first_name="Original", last_name="Name")
        info = info_with_user_factory(superuser)

        mutation = UpdateClient()
        result = mutation.mutate(
            info,
            id=client.id,
            first_name="Updated",
            last_name="Name",
            identification_number="987654321",
            state="New York",
            city="New York City",
            main_street="Updated St",
            secondary_street="Updated Second St",
            building_number="456",
            mobile_phone_number="+1111111111",
            phone_number="+2222222222",
        )

        assert result.client.first_name == "Updated"
        assert result.client.last_name == "Name"
        assert result.client.identification_number == "987654321"
        assert result.client.state == "New York"
        assert result.client.city == "New York City"
        assert result.client.main_street == "Updated St"
        assert result.client.secondary_street == "Updated Second St"
        assert result.client.building_number == "456"
        assert result.client.mobile_phone_number == "+1111111111"
        assert result.client.phone_number == "+2222222222"

        # Verify changes were saved to database
        client.refresh_from_db()
        assert client.first_name == "Updated"
        assert client.identification_number == "987654321"

    def test_update_client_partial_update(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory(first_name="Original", last_name="Name", state="California")
        info = info_with_user_factory(superuser)

        mutation = UpdateClient()
        result = mutation.mutate(
            info,
            id=client.id,
            first_name="Updated",
        )

        assert result.client.first_name == "Updated"
        assert result.client.last_name == "Name"  # Should remain unchanged
        assert result.client.state == "California"  # Should remain unchanged

        client.refresh_from_db()
        assert client.first_name == "Updated"
        assert client.last_name == "Name"

    def test_update_client_as_client_owner(self, info_with_user_factory):
        user = UserFactory(is_superuser=False)
        client = ClientFactory(user=user, first_name="Original")
        info = info_with_user_factory(user)

        mutation = UpdateClient()
        result = mutation.mutate(
            info,
            id=client.id,
            first_name="Updated",
        )

        assert result.client.first_name == "Updated"
        client.refresh_from_db()
        assert client.first_name == "Updated"

    def test_update_client_as_different_user_raises_permission_denied(self, info_with_user_factory):
        user1 = UserFactory(is_superuser=False)
        user2 = UserFactory(is_superuser=False)
        client = ClientFactory(user=user1)
        info = info_with_user_factory(user2)

        mutation = UpdateClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(
                info,
                id=client.id,
                first_name="Updated",
            )

    def test_update_client_ignores_email_and_user_fields(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory(email="original@example.com")
        original_user = client.user
        new_user = UserFactory()
        info = info_with_user_factory(superuser)

        mutation = UpdateClient()
        result = mutation.mutate(
            info,
            id=client.id,
            first_name="Updated",
            email="new@example.com",  # This should be ignored
            user=new_user,  # This should be ignored
        )

        assert result.client.first_name == "Updated"
        assert result.client.email == "original@example.com"  # Should not change
        assert result.client.user == original_user  # Should not change

        client.refresh_from_db()
        assert client.email == "original@example.com"
        assert client.user == original_user

    def test_update_nonexistent_client(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = UpdateClient()
        with pytest.raises(Client.DoesNotExist):
            mutation.mutate(
                info,
                id=999999,  # Non-existent ID
                first_name="Updated",
            )


@pytest.mark.django_db
class TestDeleteClient:
    def test_delete_client_as_superuser(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        client_id = client.id
        info = info_with_user_factory(superuser)

        mutation = DeleteClient()
        result = mutation.mutate(info, id=client_id)

        assert result.ok is True
        assert not Client.objects.filter(id=client_id).exists()

    def test_delete_client_as_regular_user_raises_permission_denied(self, info_with_user_factory):
        regular_user = UserFactory(is_superuser=False)
        client = ClientFactory()
        info = info_with_user_factory(regular_user)

        mutation = DeleteClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(info, id=client.id)

        # Verify client still exists
        assert Client.objects.filter(id=client.id).exists()

    def test_delete_client_as_client_owner_raises_permission_denied(self, info_with_user_factory):
        user = UserFactory(is_superuser=False)
        client = ClientFactory(user=user)
        info = info_with_user_factory(user)

        mutation = DeleteClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(info, id=client.id)

        # Verify client still exists
        assert Client.objects.filter(id=client.id).exists()

    def test_delete_nonexistent_client(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = DeleteClient()
        with pytest.raises(Client.DoesNotExist):
            mutation.mutate(info, id=999999)  # Non-existent ID
