"""
Shared pytest fixtures for packagehandling tests.
"""

import pytest
from django.test import RequestFactory
from graphql.type import GraphQLResolveInfo as ResolveInfo


@pytest.fixture
def info_with_user_factory():
    """
    Factory fixture to create a GraphQL ResolveInfo object with a user.

    Usage:
        def test_something(info_with_user_factory):
            user = UserFactory()
            info = info_with_user_factory(user)
            # Use info in mutation/query resolvers
    """

    def factory(user):
        request_factory = RequestFactory()
        request = request_factory.get("/graphql/")
        request.user = user
        return ResolveInfo(
            field_name="",
            field_nodes=[],
            return_type=None,
            parent_type=None,
            path=None,
            schema=None,
            fragments=None,
            root_value=None,
            operation=None,
            variable_values=None,
            context=request,
            is_awaitable=lambda: False,
        )

    return factory
