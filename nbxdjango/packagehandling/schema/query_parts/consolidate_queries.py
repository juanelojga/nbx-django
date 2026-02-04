import graphene
from django.core.exceptions import PermissionDenied

from ...models import Consolidate
from ..types import ConsolidateType


class ConsolidateQueries(graphene.ObjectType):
    all_consolidates = graphene.List(ConsolidateType)
    consolidate_by_id = graphene.Field(ConsolidateType, id=graphene.ID())

    def resolve_all_consolidates(self, info):
        user = info.context.user
        if user.is_superuser:
            return Consolidate.objects.select_related("client").prefetch_related("packages").all()
        if hasattr(user, "client"):
            return Consolidate.objects.select_related("client").prefetch_related("packages").filter(client=user.client)
        raise PermissionDenied("You do not have permission to view this resource.")

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
