import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from ...models import Client
from ..types import ClientType


class CreateClient(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        identification_number = graphene.String(required=True)
        state = graphene.String(required=True)
        city = graphene.String(required=True)
        main_street = graphene.String(required=True)
        secondary_street = graphene.String(required=True)
        building_number = graphene.String(required=True)

    client = graphene.Field(lambda: ClientType)

    def mutate(
        self,
        info,
        first_name,
        last_name,
        email,
        password,
        identification_number,
        state,
        city,
        main_street,
        secondary_street,
        building_number,
        mobile_phone_number,
        phone_number,
    ):
        if not info.context.user.is_superuser:
            raise PermissionDenied()

        User = get_user_model()
        user = User.objects.create_user(username=email, email=email, password=password, is_active=False)

        client = Client(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            identification_number=identification_number,
            state=state,
            city=city,
            main_street=main_street,
            secondary_street=secondary_street,
            building_number=building_number,
            mobile_phone_number=mobile_phone_number,
            phone_number=phone_number,
        )
        client.save()

        return CreateClient(client=client)


class UpdateClient(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        identification_number = graphene.String()
        state = graphene.String()
        city = graphene.String()
        main_street = graphene.String()
        secondary_street = graphene.String()
        building_number = graphene.String()
        mobile_phone_number = graphene.String()
        phone_number = graphene.String()

    client = graphene.Field(lambda: ClientType)

    def mutate(self, info, id, **kwargs):
        user = info.context.user
        client = Client.objects.get(pk=id)

        if not user.is_superuser and client.user != user:
            raise PermissionDenied()

        kwargs.pop("email", None)
        kwargs.pop("user", None)

        for key, value in kwargs.items():
            setattr(client, key, value)

        client.save()

        return UpdateClient(client=client)


class DeleteClient(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied()

        client = Client.objects.get(pk=id)
        client.delete()

        return DeleteClient(ok=True)
