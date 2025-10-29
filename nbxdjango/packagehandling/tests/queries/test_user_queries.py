from unittest.mock import Mock

import pytest
from packagehandling.factories import UserFactory
from packagehandling.schema.queries import Query


@pytest.mark.django_db
class TestUserQueries:

    def test_resolve_me_authenticated(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user
        resolved_user = Query.resolve_me(None, info)
        assert resolved_user == user

    def test_resolve_me_anonymous(self):
        info = Mock()
        info.context.user.is_anonymous = True
        resolved_user = Query.resolve_me(None, info)
        assert resolved_user is None
