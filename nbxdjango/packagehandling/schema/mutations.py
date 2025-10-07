import graphene

from .mutations.auth_mutations import (
    CustomRevokeToken,
    EmailAuth,
    ForgotPassword,
    ResetPassword,
)
from .mutations.client_mutations import CreateClient, DeleteClient, UpdateClient
from .mutations.token_mutations import TokenMutations


class AuthMutations(graphene.ObjectType):
    email_auth = EmailAuth.Field()
    forgot_password = ForgotPassword.Field()
    reset_password = ResetPassword.Field()
    revoke_token = CustomRevokeToken.Field()


class ClientMutations(graphene.ObjectType):
    create_client = CreateClient.Field()
    update_client = UpdateClient.Field()
    delete_client = DeleteClient.Field()


class Mutation(AuthMutations, ClientMutations, TokenMutations, graphene.ObjectType):
    pass
