import graphene
from django.core.exceptions import PermissionDenied
from ..models import Package, Client
from .types import PackageType, ClientType, UserType, MeType


class Query(graphene.ObjectType):
    all_packages = graphene.List(PackageType, page=graphene.Int(), page_size=graphene.Int())
    package = graphene.Field(PackageType, id=graphene.Int())
    all_clients = graphene.List(ClientType, page=graphene.Int(), page_size=graphene.Int())
    client = graphene.Field(ClientType, id=graphene.Int())
    me = graphene.Field(MeType)

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_all_clients(root, info, page=1, page_size=10):
        if page_size not in [10, 20, 50, 100]:
            raise ValueError("Invalid page_size. Valid values are 10, 20, 50, 100.")
        if not info.context.user.is_superuser:
            raise PermissionDenied()
        start = (page - 1) * page_size
        end = start + page_size
        return Client.objects.all()[start:end]

    def resolve_client(root, info, id):
        user = info.context.user
        if user.is_superuser:
            return Client.objects.get(pk=id)
        if not hasattr(user, 'client') or user.client.id != id:
            raise PermissionDenied()
        return Client.objects.get(pk=id)

    def resolve_all_packages(root, info, page=1, page_size=10):
        if page_size not in [10, 20, 50, 100]:
            raise ValueError("Invalid page_size. Valid values are 10, 20, 50, 100.")
        user = info.context.user
        start = (page - 1) * page_size
        end = start + page_size

        if user.is_superuser:
            return Package.objects.all()[start:end]
        if hasattr(user, 'client'):
            return Package.objects.filter(client=user.client)[start:end]
        return Package.objects.none()

    def resolve_package(root, info, id):
        user = info.context.user
        package = Package.objects.get(pk=id)
        if user.is_superuser:
            return package
        if not hasattr(user, 'client') or package.client != user.client:
            raise PermissionDenied()
        return package
