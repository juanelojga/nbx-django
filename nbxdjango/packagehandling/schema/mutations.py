import graphene
from graphene.types.generic import GenericScalar
import graphql_jwt
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import PermissionDenied
from graphql import GraphQLError
from graphql_jwt.shortcuts import get_token
from graphql_jwt import utils
from django.conf import settings as django_settings
from datetime import timedelta
from ..models import Client
from .types import ClientType


class CreateClient(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        identification_number = graphene.String(required=True)
        state = graphene.String(required=True)
        city = graphene.String(required=True)
        main_street = graphene.String(required=True)
        secondary_street = graphene.String(required=True)
        building_number = graphene.String(required=True)
        mobile_phone_number = graphene.String(required=True)
        phone_number = graphene.String(required=True)

    client = graphene.Field(lambda: ClientType)

    def mutate(self, info, first_name, last_name, email, password, identification_number, state, city, main_street, secondary_street, building_number, mobile_phone_number, phone_number):
        if not info.context.user.is_superuser:
            raise PermissionDenied()

        User = get_user_model()
        user = User.objects.create_user(username=email, email=email, password=password, is_active=False)

        client = Client(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            identification_number=identification_number,
            state=state,
            city=city,
            main_street=main_street,
            secondary_street=secondary_street,
            building_number=building_number,
            mobile_phone_number=mobile_phone_number,
            phone_number=phone_number,
        )
        client.save()

        return CreateClient(client=client)


class UpdateClient(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        identification_number = graphene.String()
        state = graphene.String()
        city = graphene.String()
        main_street = graphene.String()
        secondary_street = graphene.String()
        building_number = graphene.String()
        mobile_phone_number = graphene.String()
        phone_number = graphene.String()

    client = graphene.Field(lambda: ClientType)

    def mutate(self, info, id, **kwargs):
        user = info.context.user
        client = Client.objects.get(pk=id)

        if not user.is_superuser and client.user != user:
            raise PermissionDenied()

        kwargs.pop('email', None)
        kwargs.pop('user', None)

        for key, value in kwargs.items():
            setattr(client, key, value)

        client.save()

        return UpdateClient(client=client)


class DeleteClient(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied()

        client = Client.objects.get(pk=id)
        client.delete()

        return DeleteClient(ok=True)


class EmailAuth(graphene.Mutation):
    token = graphene.String()
    payload = GenericScalar()
    refreshExpiresIn = graphene.Int()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = authenticate(request=info.context, email=email, password=password)
        if user is None:
            raise GraphQLError("Invalid credentials")

        token = get_token(user)
        refresh_delta = getattr(django_settings, "JWT_REFRESH_EXPIRATION_DELTA", timedelta(days=7))
        return EmailAuth(
            token=token,
            payload=utils.jwt_payload(user),
            refreshExpiresIn=int(refresh_delta.total_seconds()),
        )


class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    create_client = CreateClient.Field()
    update_client = UpdateClient.Field()
    delete_client = DeleteClient.Field()
    email_auth = EmailAuth.Field()
