from unittest.mock import Mock

import pytest
from django.core.exceptions import PermissionDenied
from packagehandling.factories import ClientFactory, PackageFactory, UserFactory
from packagehandling.schema.queries import Query


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
        assert len(clients) == 3

    def test_resolve_all_clients_as_regular_user(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user
        with pytest.raises(PermissionDenied):
            Query.resolve_all_clients(None, info)

    def test_resolve_all_clients_pagination(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory.create_batch(20)
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, page=2, page_size=10)
        assert len(clients) == 10

    def test_resolve_all_clients_invalid_page_size(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser
        with pytest.raises(ValueError):
            Query.resolve_all_clients(None, info, page_size=15)

    def test_resolve_all_clients_search_by_first_name(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="John", last_name="Doe")
        ClientFactory(first_name="Jane", last_name="Smith")
        ClientFactory(first_name="Bob", last_name="Johnson")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="John")
        assert len(clients) == 2  # John Doe and Bob Johnson

    def test_resolve_all_clients_search_by_last_name(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="John", last_name="Doe")
        ClientFactory(first_name="Jane", last_name="Smith")
        ClientFactory(first_name="Bob", last_name="Doe")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="Doe")
        assert len(clients) == 2

    def test_resolve_all_clients_search_by_email(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(email="john@example.com")
        ClientFactory(email="jane@example.com")
        ClientFactory(email="bob@other.com")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="example")
        assert len(clients) == 2

    def test_resolve_all_clients_search_by_identification_number(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(identification_number="123456789")
        ClientFactory(identification_number="987654321")
        ClientFactory(identification_number="123999999")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="123")
        assert len(clients) == 2

    def test_resolve_all_clients_search_by_mobile_phone(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(mobile_phone_number="+1234567890")
        ClientFactory(mobile_phone_number="+9876543210")
        ClientFactory(mobile_phone_number="+1239999999")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="123")
        assert len(clients) == 2

    def test_resolve_all_clients_search_case_insensitive(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="John")
        ClientFactory(first_name="jane")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="JOHN")
        assert len(clients) == 1

    def test_resolve_all_clients_search_with_pagination(self):
        superuser = UserFactory(is_superuser=True)
        for i in range(15):
            ClientFactory(first_name=f"John{i}")
        ClientFactory(first_name="Jane")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="John", page=1, page_size=10)
        assert len(clients) == 10

    def test_resolve_all_clients_search_no_results(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory.create_batch(3)
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="nonexistent")
        assert len(clients) == 0

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

    def test_resolve_all_packages_pagination(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        PackageFactory.create_batch(20, client=client)
        info = Mock()
        info.context.user = superuser
        packages = Query.resolve_all_packages(None, info, page=2, page_size=10)
        assert len(packages) == 10

    def test_resolve_all_packages_as_client_pagination(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        PackageFactory.create_batch(20, client=client)
        other_client = ClientFactory()
        PackageFactory.create_batch(5, client=other_client)
        info = Mock()
        info.context.user = user
        packages = Query.resolve_all_packages(None, info, page=2, page_size=10)
        assert len(packages) == 10

    def test_resolve_all_packages_invalid_page_size(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser
        with pytest.raises(ValueError):
            Query.resolve_all_packages(None, info, page_size=15)

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
