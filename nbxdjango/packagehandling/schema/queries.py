import graphene

from .query_parts.client_queries import ClientQueries
from .query_parts.consolidate_queries import ConsolidateQueries
from .query_parts.dashboard_queries import DashboardQueries
from .query_parts.package_queries import PackageQueries
from .query_parts.user_queries import UserQueries


class Query(UserQueries, ClientQueries, PackageQueries, ConsolidateQueries, DashboardQueries, graphene.ObjectType):
    pass
