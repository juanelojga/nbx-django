import graphene
from django.core.exceptions import PermissionDenied, ValidationError
from packagehandling.utils import send_email as send_consolidate_email

from ...emails.messages import CONSOLIDATE_CREATED_MESSAGE, CONSOLIDATE_CREATED_SUBJECT
from ...models import Consolidate, Package
from ..types import ConsolidateType


class CreateConsolidate(graphene.Mutation):
    class Arguments:
        description = graphene.String(required=True)
        status = graphene.String(required=True)
        delivery_date = graphene.Date(required=False)
        comment = graphene.String(required=False)
        package_ids = graphene.List(graphene.ID, required=True)
        send_email = graphene.Boolean(required=False, default_value=False)

    consolidate = graphene.Field(ConsolidateType)

    def mutate(
        self,
        info,
        description,
        status,
        package_ids,
        send_email=False,
        delivery_date=None,
        comment=None,
    ):
        if not info.context.user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")

        if not package_ids:
            raise ValidationError("At least one package ID is required.")

        packages = Package.objects.filter(id__in=package_ids)

        if len(packages) != len(package_ids):
            raise ValidationError("One or more packages do not exist.")

        client = None
        for package in packages:
            if client is None:
                client = package.client
            elif package.client != client:
                raise ValidationError("All packages must belong to the same client.")
            if package.consolidate is not None:
                raise ValidationError("Package already belongs to a consolidate.")

        # Validate status
        allowed_initial_statuses = [
            Consolidate.Status.AWAITING_PAYMENT.value,
            Consolidate.Status.PENDING.value,
            Consolidate.Status.PROCESSING.value,
        ]

        if status not in [s.value for s in Consolidate.Status]:
            raise ValidationError(f"Invalid status: '{status}' is not a valid Consolidate status.")

        if status not in allowed_initial_statuses:
            raise ValidationError(f"Invalid initial status: a new consolidate cannot start as '{status}'.")

        consolidate = Consolidate(
            description=description,
            status=status,
            delivery_date=delivery_date,
            comment=comment,
            client=client,
        )
        consolidate.save()
        consolidate.packages.set(packages)

        if send_email:
            subject = CONSOLIDATE_CREATED_SUBJECT
            message = CONSOLIDATE_CREATED_MESSAGE
            recipient_list = [client.email]
            try:
                send_consolidate_email(subject, message, recipient_list)
            except Exception as e:
                print(f"Failed to send email for consolidate creation: {e}")

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

        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")

        try:
            Consolidate.objects.get(pk=id).delete()
            success = True
        except Consolidate.DoesNotExist:
            success = False
        return DeleteConsolidate(success=success)
