import graphene
from graphene.types.generic import GenericScalar
import graphql_jwt
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import PermissionDenied
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from graphql_jwt.shortcuts import get_token
from graphql_jwt import utils
from django.conf import settings as django_settings
from datetime import timedelta
from .models import Package, Client

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()

class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = "__all__"

class ClientType(DjangoObjectType):
    class Meta:
        model = Client
        fields = "__all__"

class Query(graphene.ObjectType):
    all_packages = graphene.List(PackageType)
    package = graphene.Field(PackageType, id=graphene.Int())
    all_clients = graphene.List(ClientType)
    client = graphene.Field(ClientType, id=graphene.Int())
    me = graphene.Field(UserType)

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_all_clients(root, info):
        if not info.context.user.is_superuser:
            raise PermissionDenied()
        return Client.objects.all()

    def resolve_client(root, info, id):
        user = info.context.user
        if user.is_superuser:
            return Client.objects.get(pk=id)
        if not hasattr(user, 'client') or user.client.id != id:
            raise PermissionDenied()
        return Client.objects.get(pk=id)

    def resolve_all_packages(root, info):
        user = info.context.user
        if user.is_superuser:
            return Package.objects.all()
        if hasattr(user, 'client'):
            return Package.objects.filter(client=user.client)
        return Package.objects.none()

    def resolve_package(root, info, id):
        user = info.context.user
        package = Package.objects.get(pk=id)
        if user.is_superuser:
            return package
        if not hasattr(user, 'client') or package.client != user.client:
            raise PermissionDenied()
        return package

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
        user = User.objects.create_user(username=email, email=email, password=password)

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
    email_auth = EmailAuth.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
