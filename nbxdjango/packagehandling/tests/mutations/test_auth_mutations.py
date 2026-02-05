from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from graphql import GraphQLError
from graphql_jwt.refresh_token.models import RefreshToken
from packagehandling.schema.mutation_parts.auth_mutations import (
    CustomRevokeToken,
    EmailAuth,
    ForgotPassword,
    ResetPassword,
)

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="test@example.com", password="strongpassword")


@pytest.mark.django_db
class TestEmailAuth:
    def test_email_auth_with_valid_credentials(self, user):
        mutation = EmailAuth()
        info = MagicMock(context=MagicMock(user=user))

        # Pass arguments as part of GraphQL context's input
        args = {"email": "test@example.com", "password": "strongpassword"}

        # Simulate the mutation call. Ensure args are unpacked as Graphene expects
        result = mutation.mutate(info, **args)

        assert result.token is not None
        assert result.refreshToken is not None
        # Updated to check for email in payload instead of username
        assert result.payload["email"] == "test@example.com"
        assert result.refreshExpiresIn > 0

    def test_email_auth_with_invalid_credentials(self):
        mutation = EmailAuth()
        info = MagicMock(context=MagicMock())

        # Pass arguments as part of GraphQL context's input
        args = {"email": "nonexistent@example.com", "password": "wrongpassword"}

        # Simulate the mutation call. Ensure args are unpacked as Graphene expects
        with pytest.raises(GraphQLError, match="Invalid credentials"):
            mutation.mutate(info, **args)


@pytest.mark.django_db
class TestForgotPassword:
    @patch("packagehandling.schema.mutation_parts.auth_mutations.send_email")
    def test_forgot_password_sends_email_for_valid_user(self, mock_send_email, user):
        mutation = ForgotPassword()
        info = MagicMock()

        result = mutation.mutate(info, email="test@example.com")

        assert result.ok is True
        mock_send_email.assert_called_once()
        assert "reset-password" in mock_send_email.call_args[1]["body"]

    @patch("packagehandling.schema.mutation_parts.auth_mutations.send_email")
    def test_forgot_password_for_nonexistent_user(self, mock_send_email):
        mutation = ForgotPassword()
        info = MagicMock()

        result = mutation.mutate(info, email="nonexistent@example.com")

        assert result.ok is True
        mock_send_email.assert_not_called()


@pytest.mark.django_db
class TestResetPassword:
    def test_reset_password_with_valid_link(self, user):
        mutation = ResetPassword()
        info = MagicMock()

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(str(user.pk).encode())

        result = mutation.mutate(info, uidb64=uidb64, token=token, password="newpassword")

        assert result.ok is True
        user.refresh_from_db()
        assert user.check_password("newpassword")

    def test_reset_password_with_invalid_uid(self):
        mutation = ResetPassword()
        info = MagicMock()

        with pytest.raises(GraphQLError, match="Invalid password reset link."):
            mutation.mutate(info, uidb64="invalid", token="invalid-token", password="newpassword")

    def test_reset_password_with_invalid_token(self, user):
        mutation = ResetPassword()
        info = MagicMock()

        uidb64 = urlsafe_base64_encode(str(user.pk).encode())

        with pytest.raises(GraphQLError, match="Invalid password reset link."):
            mutation.mutate(info, uidb64=uidb64, token="invalid-token", password="newpassword")


@pytest.mark.django_db
class TestCustomRevokeToken:
    @pytest.fixture
    def refresh_token(self, user):
        return RefreshToken.objects.create(user=user)

    @patch("graphql_jwt.settings.jwt_settings")
    def test_revoke_valid_refresh_token(self, mock_jwt_settings, user, refresh_token):
        # Mock the cookie name setting
        mock_jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME = "refreshToken"

        mutation = CustomRevokeToken()
        info = MagicMock()
        info.context.user = user
        info.context.COOKIES = {"refreshToken": refresh_token.token}

        # Check initial state
        assert not refresh_token.revoked  # The token should not be revoked initially

        # Perform the mutation
        result = mutation.mutate(None, info)

        # Assert mutation result
        assert result.revoked is True

    def test_revoke_token_for_unauthenticated_user(self):
        mutation = CustomRevokeToken()
        info = MagicMock()
        info.context.user = MagicMock(is_authenticated=False)

        # Adding root as None
        with pytest.raises(GraphQLError, match="User is not authenticated."):
            mutation.mutate(None, info)

    def test_revoke_nonexistent_refresh_token(self, user):
        mutation = CustomRevokeToken()
        info = MagicMock()
        info.context.user = user
        info.context.COOKIES = {"refreshToken": "nonexistenttoken"}

        # Adding root as None
        with pytest.raises(GraphQLError, match="Refresh token not found."):
            mutation.mutate(None, info)
