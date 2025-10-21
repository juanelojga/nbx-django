import graphene
from django.core.exceptions import PermissionDenied, ValidationError
from graphql_jwt.decorators import login_required

from ..models import Client, Package
from ..schema.types import PackageType


class CreatePackage(graphene.Mutation):
    package = graphene.Field(PackageType)

    class Arguments:
        barcode = graphene.String(required=True)
        courier = graphene.String(required=True)
        client_id = graphene.ID(required=True)
        comments = graphene.String()
        package_type = graphene.String()
        weight = graphene.Float()
        tracking_number = graphene.String()

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
        barcode = graphene.String()
        courier = graphene.String()
        client_id = graphene.ID()
        comments = graphene.String()
        package_type = graphene.String()
        weight = graphene.Float()
        tracking_number = graphene.String()

    @login_required
    def mutate(self, info, id, **kwargs):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            package = Package.objects.get(pk=id)
        except Package.DoesNotExist:
            raise ValidationError("Package not found.")

        if "client_id" in kwargs:
            if package.consolidates.exists():
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

        package.delete()
        return DeletePackage(success=True)
