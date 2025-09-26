import pytest
from django.core.exceptions import PermissionDenied
from packagehandling.schema.queries import Query
from packagehandling.factories import UserFactory, ClientFactory, PackageFactory
from unittest.mock import Mock

@pytest.mark.django_db
class TestQueries:

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

    def test_resolve_all_clients_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory.create_batch(3)
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info)
        assert clients.count() == 3

    def test_resolve_all_clients_as_regular_user(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user
        with pytest.raises(PermissionDenied):
            Query.resolve_all_clients(None, info)

    def test_resolve_client_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        info = Mock()
        info.context.user = superuser
        resolved_client = Query.resolve_client(None, info, id=client.id)
        assert resolved_client == client

    def test_resolve_client_as_owner(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        info = Mock()
        info.context.user = user
        resolved_client = Query.resolve_client(None, info, id=client.id)
        assert resolved_client == client

    def test_resolve_client_as_other_user(self):
        user1 = UserFactory()
        client = ClientFactory(user=user1)
        user2 = UserFactory()
        info = Mock()
        info.context.user = user2
        with pytest.raises(PermissionDenied):
            Query.resolve_client(None, info, id=client.id)

    def test_resolve_all_packages_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        PackageFactory.create_batch(3, client=client)
        info = Mock()
        info.context.user = superuser
        packages = Query.resolve_all_packages(None, info)
        assert packages.count() == 3

    def test_resolve_all_packages_as_owner(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        PackageFactory.create_batch(2, client=client)
        info = Mock()
        info.context.user = user
        packages = Query.resolve_all_packages(None, info)
        assert packages.count() == 2

    def test_resolve_all_packages_as_user_with_no_client(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user
        packages = Query.resolve_all_packages(None, info)
        assert packages.count() == 0

    def test_resolve_package_as_superuser(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        package = PackageFactory(client=client)
        info = Mock()
        info.context.user = superuser
        resolved_package = Query.resolve_package(None, info, id=package.id)
        assert resolved_package == package

    def test_resolve_package_as_owner(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        package = PackageFactory(client=client)
        info = Mock()
        info.context.user = user
        resolved_package = Query.resolve_package(None, info, id=package.id)
        assert resolved_package == package

    def test_resolve_package_as_other_user(self):
        user1 = UserFactory()
        client = ClientFactory(user=user1)
        package = PackageFactory(client=client)
        user2 = UserFactory()
        info = Mock()
        info.context.user = user2
        with pytest.raises(PermissionDenied):
            Query.resolve_package(None, info, id=package.id)