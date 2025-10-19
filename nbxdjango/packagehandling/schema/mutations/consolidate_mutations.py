import graphene

from ...models import Client, Consolidate
from ..types import ConsolidateType


class CreateConsolidate(graphene.Mutation):
    class Arguments:
        description = graphene.String(required=True)
        status = graphene.String(required=True)
        delivery_date = graphene.Date(required=True)
        comment = graphene.String()
        client_id = graphene.ID(required=True)
        package_ids = graphene.List(graphene.ID, required=True)
        extra_attributes = graphene.JSONString()

    consolidate = graphene.Field(ConsolidateType)

    def mutate(
        self,
        info,
        description,
        status,
        delivery_date,
        client_id,
        package_ids,
        comment=None,
        extra_attributes=None,
    ):
        client = Client.objects.get(pk=client_id)
        consolidate = Consolidate(
            description=description,
            status=status,
            delivery_date=delivery_date,
            comment=comment,
            client=client,
            extra_attributes=extra_attributes or {},
        )
        consolidate.save()
        consolidate.packages.set(package_ids)
        return CreateConsolidate(consolidate=consolidate)


class UpdateConsolidate(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        description = graphene.String()
        status = graphene.String()
        delivery_date = graphene.Date()
        comment = graphene.String()
        package_ids = graphene.List(graphene.ID)
        extra_attributes = graphene.JSONString()

    consolidate = graphene.Field(ConsolidateType)

    def mutate(self, info, id, **kwargs):
        consolidate = Consolidate.objects.get(pk=id)
        for key, value in kwargs.items():
            if key == "package_ids":
                consolidate.packages.set(value)
            else:
                setattr(consolidate, key, value)
        consolidate.save()
        return UpdateConsolidate(consolidate=consolidate)


class DeleteConsolidate(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            Consolidate.objects.get(pk=id).delete()
            success = True
        except Consolidate.DoesNotExist:
            success = False
        return DeleteConsolidate(success=success)
