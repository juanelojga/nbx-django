import graphene
from django.core.exceptions import PermissionDenied, ValidationError
from graphql_jwt.decorators import login_required

from ...models import Client, Package
from ..types import PackageType


class CreatePackage(graphene.Mutation):
    package = graphene.Field(PackageType)

    class Arguments:
        barcode = graphene.String(required=True)
        courier = graphene.String(required=True)
        other_courier = graphene.String()
        length = graphene.Float()
        width = graphene.Float()
        height = graphene.Float()
        dimension_unit = graphene.String()
        weight = graphene.Float()
        weight_unit = graphene.String()
        description = graphene.String()
        purchase_link = graphene.String()
        real_price = graphene.Float()
        service_price = graphene.Float()
        arrival_date = graphene.Date()
        comments = graphene.String()
        client_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")

        client_id = kwargs.pop("client_id")
        try:
            client = Client.objects.get(pk=client_id)
        except Client.DoesNotExist:
            raise ValidationError("The provided client does not exist.")

        package = Package.objects.create(client=client, **kwargs)
        return CreatePackage(package=package)


class UpdatePackage(graphene.Mutation):
    package = graphene.Field(PackageType)

    class Arguments:
        id = graphene.ID(required=True)
        courier = graphene.String()
        other_courier = graphene.String()
        length = graphene.Float()
        width = graphene.Float()
        height = graphene.Float()
        dimension_unit = graphene.String()
        weight = graphene.Float()
        weight_unit = graphene.String()
        description = graphene.String()
        purchase_link = graphene.String()
        real_price = graphene.Float()
        service_price = graphene.Float()
        arrival_date = graphene.Date()
        comments = graphene.String()
        client_id = graphene.ID()

    @login_required
    def mutate(self, info, id, **kwargs):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            package = Package.objects.get(pk=id)
        except Package.DoesNotExist:
            raise ValidationError("Package not found.")

        if "barcode" in kwargs:
            raise ValidationError("Barcode cannot be modified.")

        if "client_id" in kwargs:
            # Directly check if the consolidate field is not None
            if package.consolidate:
                raise ValidationError("Client cannot be updated for packages already consolidated.")
            try:
                client = Client.objects.get(pk=kwargs["client_id"])
                package.client = client
            except Client.DoesNotExist:
                raise ValidationError("The provided client does not exist.")
            del kwargs["client_id"]

        for key, value in kwargs.items():
            setattr(package, key, value)

        package.save()
        return UpdatePackage(package=package)


class DeletePackage(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, id):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            package = Package.objects.get(pk=id)
        except Package.DoesNotExist:
            raise ValidationError("Package not found.")

        # Prevent deletion if package is part of a consolidate
        if package.consolidate is not None:
            raise ValidationError("Package cannot be deleted because it belongs to a consolidate.")

        package.delete()
        return DeletePackage(success=True)
