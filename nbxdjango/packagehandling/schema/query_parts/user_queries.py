import graphene

from ..types import MeType


class UserQueries(graphene.ObjectType):
    me = graphene.Field(MeType)

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user
