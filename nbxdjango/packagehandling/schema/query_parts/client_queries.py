import graphene
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from ...models import Client
from ..types import ClientType


class ClientQueries(graphene.ObjectType):
    all_clients = graphene.List(
        ClientType,
        search=graphene.String(),
        page=graphene.Int(),
        page_size=graphene.Int(),
    )
    client = graphene.Field(ClientType, id=graphene.Int())

    def resolve_all_clients(root, info, search=None, page=1, page_size=10):
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

        start = (page - 1) * page_size
        end = start + page_size
        return queryset[start:end]

    def resolve_client(root, info, id):
        user = info.context.user
        if user.is_superuser:
            return Client.objects.get(pk=id)
        if not hasattr(user, "client") or user.client.id != id:
            raise PermissionDenied()
        return Client.objects.get(pk=id)
