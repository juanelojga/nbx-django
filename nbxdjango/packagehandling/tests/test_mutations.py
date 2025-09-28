
import pytest
from django.core.exceptions import PermissionDenied
from graphql import GraphQLError
from packagehandling.schema.mutations import CreateClient, EmailAuth, UpdateClient, DeleteClient
from packagehandling.factories import UserFactory, ClientFactory
from packagehandling.models import Client
from unittest.mock import Mock
from django.contrib.auth import get_user_model

from django.test import RequestFactory

@pytest.mark.django_db
class TestMutations:

    def test_create_client_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser

        mutation = CreateClient()
        result = mutation.mutate(
            info,
            first_name="Test",
            last_name="Client",
            email="testclient@example.com",
            password="password",
            identification_number="12345",
            state="CA",
            city="LA",
            main_street="Main",
            secondary_street="Secondary",
            building_number="123",
            mobile_phone_number="1234567890",
            phone_number="0987654321"
        )

        assert result.client.email == "testclient@example.com"
        User = get_user_model()
        assert User.objects.filter(email="testclient@example.com").exists()

    def test_create_client_as_regular_user(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user

        mutation = CreateClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(
                info,
                first_name="Test",
                last_name="Client",
                email="testclient@example.com",
                password="password",
                identification_number="12345",
                state="CA",
                city="LA",
                main_street="Main",
                secondary_street="Secondary",
                building_number="123",
                mobile_phone_number="1234567890",
                phone_number="0987654321"
            )

    def test_create_client_inactive_user(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser

        mutation = CreateClient()
        result = mutation.mutate(
            info,
            first_name="Test",
            last_name="Client",
            email="testclient@example.com",
            password="password",
            identification_number="12345",
            state="CA",
            city="LA",
            main_street="Main",
            secondary_street="Secondary",
            building_number="123",
            mobile_phone_number="1234567890",
            phone_number="0987654321"
        )

        assert not result.client.user.is_active

        factory = RequestFactory()
        request = factory.post('/graphql/')
        info.context = request

        auth_mutation = EmailAuth()
        with pytest.raises(GraphQLError):
            auth_mutation.mutate(info, email="testclient@example.com", password="password")

    def test_email_auth_success(self):
        user = UserFactory()
        user.set_password("password")
        user.save()

        factory = RequestFactory()
        request = factory.post('/graphql/')

        info = Mock()
        info.context = request

        mutation = EmailAuth()
        result = mutation.mutate(info, email=user.email, password="password")

        assert result.token
        assert result.payload
        assert result.refreshExpiresIn

    def test_email_auth_failure(self):
        user = UserFactory(password="password")
        factory = RequestFactory()
        request = factory.post('/graphql/')

        info = Mock()
        info.context = request

        mutation = EmailAuth()
        with pytest.raises(GraphQLError):
            mutation.mutate(info, email=user.email, password="wrongpassword")


    def test_update_client_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        info = Mock()
        info.context.user = superuser

        mutation = UpdateClient()
        result = mutation.mutate(info, id=client.id, first_name="New Name")

        assert result.client.first_name == "New Name"

    def test_update_client_as_owner(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        info = Mock()
        info.context.user = user

        mutation = UpdateClient()
        result = mutation.mutate(info, id=client.id, first_name="New Name")

        assert result.client.first_name == "New Name"

    def test_update_client_as_other_user(self):
        user1 = UserFactory()
        client = ClientFactory(user=user1)
        user2 = UserFactory()
        info = Mock()
        info.context.user = user2

        mutation = UpdateClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(info, id=client.id, first_name="New Name")

    def test_update_client_email_and_user_not_updated(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        info = Mock()
        info.context.user = user

        mutation = UpdateClient()
        result = mutation.mutate(info, id=client.id, email="new@email.com")

        assert result.client.email != "new@email.com"


    def test_delete_client_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        info = Mock()
        info.context.user = superuser

        mutation = DeleteClient()
        result = mutation.mutate(info, id=client.id)

        assert result.ok
        assert not Client.objects.filter(id=client.id).exists()

    def test_delete_client_as_regular_user(self):
        user = UserFactory()
        client = ClientFactory()
        info = Mock()
        info.context.user = user

        mutation = DeleteClient()
        with pytest.raises(PermissionDenied):
            mutation.mutate(info, id=client.id)
