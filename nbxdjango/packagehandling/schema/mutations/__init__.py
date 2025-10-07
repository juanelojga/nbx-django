import graphene

from .auth_mutations import CustomRevokeToken, EmailAuth, ForgotPassword, ResetPassword
from .client_mutations import CreateClient, DeleteClient, UpdateClient
from .token_mutations import TokenMutations


class Mutation(TokenMutations, graphene.ObjectType):
    email_auth = EmailAuth.Field()
    forgot_password = ForgotPassword.Field()
    reset_password = ResetPassword.Field()
    create_client = CreateClient.Field()
    update_client = UpdateClient.Field()
    delete_client = DeleteClient.Field()
    revoke_token = CustomRevokeToken.Field()


__all__ = ["Mutation"]
