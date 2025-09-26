import graphene
from django.core.exceptions import PermissionDenied
from ..models import Package, Client
from .types import PackageType, ClientType, UserType


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
