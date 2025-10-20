from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from graphql import GraphQLError
from graphql_jwt.refresh_token.models import RefreshToken
from packagehandling.factories import ClientFactory, UserFactory
from packagehandling.models import Client
from packagehandling.mutations.auth_mutations import (
    CustomRevokeToken,
    EmailAuth,
    ForgotPassword,
    ResetPassword,
)
from packagehandling.mutations.client_mutations import (
    CreateClient,
    DeleteClient,
    UpdateClient,
)


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
            identification_number="12345",
            state="CA",
            city="LA",
            main_street="Main",
            secondary_street="Secondary",
            building_number="123",
            mobile_phone_number="1234567890",
            phone_number="0987654321",
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
                phone_number="0987654321",
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
            identification_number="12345",
            state="CA",
            city="LA",
            main_street="Main",
            secondary_street="Secondary",
            building_number="123",
            mobile_phone_number="1234567890",
            phone_number="0987654321",
        )

        assert not result.client.user.is_active

        factory = RequestFactory()
        request = factory.post("/graphql/")
        info.context = request

        auth_mutation = EmailAuth()
        with pytest.raises(GraphQLError):
            auth_mutation.mutate(info, email="testclient@example.com", password="password")

    def test_email_auth_success(self):
        user = UserFactory()
        user.set_password("password")
        user.save()

        factory = RequestFactory()
        request = factory.post("/graphql/")

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
        request = factory.post("/graphql/")

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

    @patch("packagehandling.mutations.auth_mutations.send_email")
    def test_forgot_password_success(self, mock_send_email):
        user = UserFactory()
        info = Mock()

        mutation = ForgotPassword()
        result = mutation.mutate(info, email=user.email)

        assert result.ok
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert kwargs["subject"] == "Reset Your Password"
        assert user.email in kwargs["recipient_list"]

    @patch("packagehandling.mutations.auth_mutations.send_email")
    def test_forgot_password_nonexistent_email(self, mock_send_email):
        info = Mock()

        mutation = ForgotPassword()
        result = mutation.mutate(info, email="nonexistent@example.com")

        assert result.ok
        mock_send_email.assert_not_called()

    def test_reset_password_success(self):
        user = UserFactory()
        user.set_password("old_password")
        user.save()

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        new_password = "new_strong_password"

        info = Mock()
        mutation = ResetPassword()
        result = mutation.mutate(info, uidb64=uidb64, token=token, password=new_password)

        assert result.ok
        user.refresh_from_db()
        assert user.check_password(new_password)

    def test_reset_password_invalid_token(self):
        user = UserFactory()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        new_password = "new_strong_password"

        info = Mock()
        mutation = ResetPassword()
        with pytest.raises(GraphQLError) as excinfo:
            mutation.mutate(info, uidb64=uidb64, token="invalid-token", password=new_password)
        assert "Invalid password reset link." in str(excinfo.value)

        def test_revoke_token_success(self):
            from graphql_jwt.settings import jwt_settings

            user = UserFactory()
            refresh_token = RefreshToken.objects.create(user=user, token="test-token")

            info = Mock()
            info.context.user = user
            info.context.COOKIES = {jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME: refresh_token.token}

            result = CustomRevokeToken.mutate(root=None, info=info)

            assert result.revoked
            assert not RefreshToken.objects.filter(token="test-token").exists()

    def test_revoke_token_no_cookie(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user
        info.context.COOKIES = {}

        with pytest.raises(GraphQLError) as excinfo:
            CustomRevokeToken.mutate(root=None, info=info)
        assert "Refresh token not found in cookies." in str(excinfo.value)

    def test_revoke_token_unauthenticated(self):
        info = Mock()
        info.context.user = AnonymousUser()
        info.context.COOKIES = {}

        with pytest.raises(GraphQLError) as excinfo:
            CustomRevokeToken.mutate(root=None, info=info)
        assert "User is not authenticated." in str(excinfo.value)
