import graphene
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models import Value as V
from django.db.models.functions import Concat

from ...models import Client
from ..types import ClientConnection, ClientType


class ClientQueries(graphene.ObjectType):
    all_clients = graphene.Field(
        ClientConnection,
        search=graphene.String(),
        page=graphene.Int(),
        page_size=graphene.Int(),
        order_by=graphene.String(),
    )
    client = graphene.Field(ClientType, id=graphene.Int())

    def resolve_all_clients(root, info, search=None, page=1, page_size=10, order_by=None):
        if page_size not in [10, 20, 50, 100]:
            raise ValueError("Invalid page_size. Valid values are 10, 20, 50, 100.")
        if not info.context.user.is_superuser:
            raise PermissionDenied()

        queryset = Client.objects.all()

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(identification_number__icontains=search)
                | Q(mobile_phone_number__icontains=search)
            )

        if order_by:
            order_by_field = order_by.replace("-", "")
            if order_by_field not in ["full_name", "email", "created_at"]:
                raise ValueError("Invalid order_by value.")

            if order_by_field == "full_name":
                annotation_name = "search_full_name"
                queryset = queryset.annotate(**{annotation_name: Concat("first_name", V(" "), "last_name")})
                order_by_param = f"-{annotation_name}" if order_by.startswith("-") else annotation_name
                queryset = queryset.order_by(order_by_param)
            else:
                queryset = queryset.order_by(order_by)

        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = queryset[start:end]
        has_next = end < total_count
        has_previous = start > 0

        return ClientConnection(
            results=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous,
        )

    def resolve_client(root, info, id):
        user = info.context.user
        if user.is_superuser:
            return Client.objects.get(pk=id)

        # Use select_related to fetch user and client in one query
        client = Client.objects.filter(pk=id).select_related("user").first()
        if not client:
            raise PermissionDenied()
        if client.user != user:
            raise PermissionDenied()
        return client
