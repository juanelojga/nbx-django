import graphene

from .query_parts.client_queries import ClientQueries
from .query_parts.consolidate_queries import ConsolidateQueries
from .query_parts.package_queries import PackageQueries
from .query_parts.user_queries import UserQueries


class Query(UserQueries, ClientQueries, PackageQueries, ConsolidateQueries, graphene.ObjectType):
    pass
