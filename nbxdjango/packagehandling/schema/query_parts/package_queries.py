import graphene
from django.core.exceptions import PermissionDenied

from ...models import Package
from ..types import PackageType


class PackageQueries(graphene.ObjectType):
    all_packages = graphene.List(PackageType, page=graphene.Int(), page_size=graphene.Int())
    package = graphene.Field(PackageType, id=graphene.Int())

    def resolve_all_packages(root, info, page=1, page_size=10):
        if page_size not in [10, 20, 50, 100]:
            raise ValueError("Invalid page_size. Valid values are 10, 20, 50, 100.")
        user = info.context.user
        start = (page - 1) * page_size
        end = start + page_size

        if user.is_superuser:
            return Package.objects.all()[start:end]
        if hasattr(user, "client"):
            return Package.objects.filter(client=user.client)[start:end]
        return Package.objects.none()

    def resolve_package(root, info, id):
        user = info.context.user
        package = Package.objects.get(pk=id)
        if user.is_superuser:
            return package
        if not hasattr(user, "client") or package.client != user.client:
            raise PermissionDenied()
        return package
