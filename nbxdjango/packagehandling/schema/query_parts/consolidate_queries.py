import graphene
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from ...models import Consolidate
from ..types import ConsolidateConnection, ConsolidateType


class ConsolidateQueries(graphene.ObjectType):
    all_consolidates = graphene.Field(
        ConsolidateConnection,
        search=graphene.String(),
        page=graphene.Int(),
        page_size=graphene.Int(),
        order_by=graphene.String(),
        status=graphene.String(),
    )
    consolidate_by_id = graphene.Field(ConsolidateType, id=graphene.ID())

    def resolve_all_consolidates(root, info, search=None, page=1, page_size=10, order_by=None, status=None):
        # Validate page_size
        if page_size not in [10, 20, 50, 100]:
            raise ValueError("Invalid page_size. Valid values are 10, 20, 50, 100.")

        user = info.context.user
        queryset = Consolidate.objects.select_related("client").prefetch_related("packages")

        # Permission checks
        if user.is_superuser:
            pass  # Admin can see all consolidates
        elif hasattr(user, "client"):
            queryset = queryset.filter(client=user.client)
        else:
            raise PermissionDenied("You do not have permission to view this resource.")

        # Search filtering
        if search:
            queryset = queryset.filter(
                Q(client__first_name__icontains=search)
                | Q(client__last_name__icontains=search)
                | Q(client__email__icontains=search)
            )

        # Status filtering
        if status:
            queryset = queryset.filter(status=status)

        # Ordering
        if order_by:
            order_by_field = order_by.replace("-", "")
            if order_by_field not in ["delivery_date", "created_at", "status"]:
                raise ValueError("Invalid order_by value.")
            queryset = queryset.order_by(order_by)
        else:
            # Default ordering: newest first
            queryset = queryset.order_by("-created_at")

        # Pagination
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = queryset[start:end]
        has_next = end < total_count
        has_previous = start > 0

        return ConsolidateConnection(
            results=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous,
        )

    def resolve_consolidate_by_id(self, info, id):
        user = info.context.user
        try:
            consolidate = Consolidate.objects.select_related("client").prefetch_related("packages").get(pk=id)
        except Consolidate.DoesNotExist:
            return None

        if user.is_superuser:
            return consolidate
        if hasattr(user, "client") and consolidate.client == user.client:
            return consolidate
        raise PermissionDenied("You do not have permission to view this resource.")
