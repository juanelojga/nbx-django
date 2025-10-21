import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied


class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        if not info.context.user.is_superuser:
            raise PermissionDenied()

        User = get_user_model()
        user_to_delete = User.objects.get(pk=id)
        user_to_delete.delete()

        return DeleteUser(ok=True)
