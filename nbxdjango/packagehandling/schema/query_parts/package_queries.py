import graphene
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from ...models import Package
from ..types import PackageConnection, PackageType


class PackageQueries(graphene.ObjectType):
    all_packages = graphene.Field(
        PackageConnection,
        search=graphene.String(),
        page=graphene.Int(),
        page_size=graphene.Int(),
        order_by=graphene.String(),
        client_id=graphene.Int(),
    )
    package = graphene.Field(PackageType, id=graphene.Int())

    def resolve_all_packages(root, info, search=None, page=1, page_size=10, order_by=None, client_id=None):
        if page_size not in [10, 20, 50, 100]:
            raise ValueError("Invalid page_size. Valid values are 10, 20, 50, 100.")

        user = info.context.user
        queryset = Package.objects.all()

        if user.is_superuser:
            if client_id:
                queryset = queryset.filter(client_id=client_id)
        else:
            if hasattr(user, "client"):
                queryset = queryset.filter(client=user.client)
            else:
                raise PermissionDenied("You do not have permission to view this resource.")

        if search:
            queryset = queryset.filter(Q(barcode__icontains=search) | Q(description__icontains=search))

        if order_by:
            order_by_field = order_by.replace("-", "")
            if order_by_field not in ["barcode", "created_at", "status"]:
                raise ValueError("Invalid order_by value.")
            queryset = queryset.order_by(order_by)

        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = queryset[start:end]
        has_next = end < total_count
        has_previous = start > 0

        return PackageConnection(
            results=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous,
        )

    def resolve_package(root, info, id):
        user = info.context.user
        package = Package.objects.get(pk=id)
        if user.is_superuser:
            return package
        if not hasattr(user, "client") or package.client != user.client:
            raise PermissionDenied()
        return package
