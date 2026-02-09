from datetime import timedelta

import graphene
from django.conf import settings as django_settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from graphene.types.generic import GenericScalar
from graphql import GraphQLError
from graphql_jwt import utils
from graphql_jwt.refresh_token.models import RefreshToken
from graphql_jwt.refresh_token.shortcuts import create_refresh_token
from graphql_jwt.shortcuts import get_token

from ...utils import send_email

# Frontend URL for password reset links
FRONTEND_URL = getattr(django_settings, "FRONTEND_URL", "http://localhost:3000")


class EmailAuth(graphene.Mutation):
    token = graphene.String()
    refreshToken = graphene.String()
    payload = GenericScalar()
    refreshExpiresIn = graphene.Int()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = authenticate(request=info.context, email=email, password=password)
        if user is None:
            raise GraphQLError("Invalid credentials")

        # Generate access token
        token = get_token(user)

        # Generate refresh token
        refresh_token = create_refresh_token(user)

        refresh_delta = getattr(django_settings, "JWT_REFRESH_EXPIRATION_DELTA", timedelta(days=7))

        # Ensure `payload` explicitly includes the email and optional username
        payload = utils.jwt_payload(user)
        payload["email"] = user.email  # Include email explicitly
        if user.username:
            payload["username"] = user.username  # Includes username only if set

        return EmailAuth(
            token=token,
            refreshToken=refresh_token.token,
            payload=payload,
            refreshExpiresIn=int(refresh_delta.total_seconds()),
        )


class ForgotPassword(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, email):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # To prevent user enumeration attacks, we don't reveal that the user doesn't exist.
            return ForgotPassword(ok=True)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        reset_url = f"{FRONTEND_URL}/reset-password?uid={uidb64}&token={token}"

        send_email(
            subject="Reset Your Password",
            body=f"Click the following link to reset your password: {reset_url}",
            recipient_list=[user.email],
        )

        return ForgotPassword(ok=True)


class ResetPassword(graphene.Mutation):
    class Arguments:
        uidb64 = graphene.String(required=True)
        token = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, uidb64, token, password):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        token_generator = PasswordResetTokenGenerator()
        if user is not None and token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            return ResetPassword(ok=True)
        else:
            # Invalid token or user
            raise GraphQLError("Invalid password reset link.")


class CustomRevokeToken(graphene.Mutation):
    revoked = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info):
        from graphql_jwt.settings import jwt_settings

        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("User is not authenticated.")

        cookie_name = jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME
        refresh_token_str = info.context.COOKIES.get(cookie_name)

        if not refresh_token_str:
            raise GraphQLError("Refresh token not found in cookies.")

        try:
            refresh_token = RefreshToken.objects.get(token=refresh_token_str, user=user)
            refresh_token.revoke()
            return CustomRevokeToken(revoked=True)
        except RefreshToken.DoesNotExist:
            raise GraphQLError("Refresh token not found.")


class RefreshWithToken(graphene.Mutation):
    """
    Refresh JWT access token using a refresh token string.
    This mutation accepts the refresh token string directly and returns a new access token.
    Optionally rotates the refresh token for enhanced security.
    """

    token = graphene.String()
    refreshToken = graphene.String()
    payload = GenericScalar()
    refreshExpiresIn = graphene.Int()

    class Arguments:
        refreshToken = graphene.String(required=True)

    def mutate(self, info, refreshToken):
        # Look up the refresh token in the database
        try:
            refresh_token_obj = RefreshToken.objects.get(token=refreshToken)
        except RefreshToken.DoesNotExist:
            raise GraphQLError("Invalid refresh token")

        # Check if the refresh token is expired
        if refresh_token_obj.is_expired(info.context):
            raise GraphQLError("Refresh token has expired")

        # Check if the refresh token is revoked
        if refresh_token_obj.revoked:
            raise GraphQLError("Refresh token has been revoked")

        # Get the user associated with the refresh token
        user = refresh_token_obj.user

        # Generate a new access token
        new_access_token = get_token(user)

        # Generate payload
        payload = utils.jwt_payload(user)
        payload["email"] = user.email
        if user.username:
            payload["username"] = user.username

        # Rotate the refresh token (generate a new one and revoke the old one)
        new_refresh_token = create_refresh_token(user, refresh_token_obj)
        refresh_delta = getattr(django_settings, "JWT_REFRESH_EXPIRATION_DELTA", timedelta(days=7))

        return RefreshWithToken(
            token=new_access_token,
            refreshToken=new_refresh_token.token,
            payload=payload,
            refreshExpiresIn=int(refresh_delta.total_seconds()),
        )
