# nbxdjango/packagehandling/tests/mutations/test_user_mutations.py

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from graphql.type import GraphQLResolveInfo as ResolveInfo
from packagehandling.schema.mutation_parts.user_mutations import DeleteUser

User = get_user_model()


@pytest.fixture
def info_with_user_factory():
    """Creates a mocked GraphQLResolveInfo with a user attached to the request."""

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


@pytest.mark.django_db
class TestDeleteUser:
    def test_delete_user_as_superuser(self, info_with_user_factory):
        """Test that a superuser can delete a user."""
        superuser = User.objects.create_user(
            username="superuser",
            email="superuser@example.com",
            password="password123",
            is_superuser=True,
        )
        user_to_delete = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
        )
        info = info_with_user_factory(superuser)

        mutation = DeleteUser()
        result = mutation.mutate(info, id=user_to_delete.id)

        assert result.ok is True
        assert not User.objects.filter(id=user_to_delete.id).exists()

    def test_delete_user_as_regular_user_raises_permission_denied(self, info_with_user_factory):
        """Test that a regular user cannot delete another user."""
        regular_user = User.objects.create_user(
            username="regular_user",
            email="regular_user@example.com",
            password="password123",
            is_superuser=False,
        )
        user_to_delete = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
        )
        info = info_with_user_factory(regular_user)

        mutation = DeleteUser()
        with pytest.raises(PermissionDenied):
            mutation.mutate(info, id=user_to_delete.id)

        # Verify user still exists
        assert User.objects.filter(id=user_to_delete.id).exists()

    def test_delete_nonexistent_user(self, info_with_user_factory):
        """Test that attempting to delete a non-existent user raises the correct exception."""
        superuser = User.objects.create_user(
            username="superuser",
            email="superuser@example.com",
            password="password123",
            is_superuser=True,
        )
        info = info_with_user_factory(superuser)

        mutation = DeleteUser()
        with pytest.raises(User.DoesNotExist):
            mutation.mutate(info, id=999999)  # Non-existent ID
