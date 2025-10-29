import graphene

from .mutation_parts.auth_mutations import (
    CustomRevokeToken,
    EmailAuth,
    ForgotPassword,
    ResetPassword,
)
from .mutation_parts.client_mutations import CreateClient, DeleteClient, UpdateClient
from .mutation_parts.consolidate_mutations import (
    CreateConsolidate,
    DeleteConsolidate,
    UpdateConsolidate,
)
from .mutation_parts.package_mutations import (
    CreatePackage,
    DeletePackage,
    UpdatePackage,
)
from .mutation_parts.token_mutations import TokenMutations


class AuthMutations(graphene.ObjectType):
    email_auth = EmailAuth.Field()
    forgot_password = ForgotPassword.Field()
    reset_password = ResetPassword.Field()
    revoke_token = CustomRevokeToken.Field()


class ClientMutations(graphene.ObjectType):
    create_client = CreateClient.Field()
    update_client = UpdateClient.Field()
    delete_client = DeleteClient.Field()


class PackageMutations(graphene.ObjectType):
    create_package = CreatePackage.Field()
    update_package = UpdatePackage.Field()
    delete_package = DeletePackage.Field()


class ConsolidateMutations(graphene.ObjectType):
    create_consolidate = CreateConsolidate.Field()
    update_consolidate = UpdateConsolidate.Field()
    delete_consolidate = DeleteConsolidate.Field()


class Mutation(
    AuthMutations,
    ClientMutations,
    TokenMutations,
    ConsolidateMutations,
    PackageMutations,
    graphene.ObjectType,
):
    pass
