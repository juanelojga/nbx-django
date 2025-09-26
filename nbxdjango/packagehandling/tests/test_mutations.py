
import pytest
from django.core.exceptions import PermissionDenied
from graphql import GraphQLError
from packagehandling.schema.mutations import CreateClient, EmailAuth
from packagehandling.factories import UserFactory
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
