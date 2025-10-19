import graphene

from ...models import Consolidate
from ..types import ConsolidateType


class ConsolidateQueries(graphene.ObjectType):
    all_consolidates = graphene.List(ConsolidateType)
    consolidate_by_id = graphene.Field(ConsolidateType, id=graphene.ID())

    def resolve_all_consolidates(self, info):
        return Consolidate.objects.select_related("client").prefetch_related("packages").all()

    def resolve_consolidate_by_id(self, info, id):
        try:
            return Consolidate.objects.select_related("client").prefetch_related("packages").get(pk=id)
        except Consolidate.DoesNotExist:
            return None
