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
        result = Query.resolve_all_clients(None, info)
        assert result.total_count == 3
        assert len(result.results) == 3
        assert result.page == 1
        assert result.page_size == 10
        assert not result.has_next
        assert not result.has_previous

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
        result = Query.resolve_all_clients(None, info, page=2, page_size=10)
        assert len(result.results) == 10
        assert result.total_count == 20
        assert result.page == 2
        assert result.page_size == 10
        assert not result.has_next
        assert result.has_previous

    def test_resolve_all_clients_invalid_page_size(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser
        with pytest.raises(ValueError, match="Invalid page_size"):
            Query.resolve_all_clients(None, info, page_size=15)

    def test_resolve_all_clients_search_by_first_name(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="John", last_name="Doe")
        ClientFactory(first_name="Jane", last_name="Smith")
        ClientFactory(first_name="Bob", last_name="Johnson")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, search="John")
        assert len(result.results) == 2  # John Doe and Bob Johnson

    def test_resolve_all_clients_search_by_last_name(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="John", last_name="Doe")
        ClientFactory(first_name="Jane", last_name="Smith")
        ClientFactory(first_name="Bob", last_name="Doe")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="Doe")
        assert len(clients.results) == 2

    def test_resolve_all_clients_search_by_email(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(email="john@example.com")
        ClientFactory(email="jane@example.com")
        ClientFactory(email="bob@other.com")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, search="example")
        assert len(result.results) == 2

    def test_resolve_all_clients_search_by_identification_number(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(identification_number="123456789")
        ClientFactory(identification_number="987654321")
        ClientFactory(identification_number="123999999")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="123")
        assert len(clients.results) == 2

    def test_resolve_all_clients_search_by_mobile_phone(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(mobile_phone_number="+1234567890")
        ClientFactory(mobile_phone_number="+9876543210")
        ClientFactory(mobile_phone_number="+1239999999")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, search="123")
        assert len(result.results) == 2

    def test_resolve_all_clients_search_case_insensitive(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="John")
        ClientFactory(first_name="jane")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, search="JOHN")
        assert len(result.results) == 1

    def test_resolve_all_clients_search_with_pagination(self):
        superuser = UserFactory(is_superuser=True)
        for i in range(15):
            ClientFactory(first_name=f"John{i}")
        ClientFactory(first_name="Jane")
        info = Mock()
        info.context.user = superuser
        clients = Query.resolve_all_clients(None, info, search="John", page=1, page_size=10)
        assert len(clients.results) == 10

    def test_resolve_all_clients_search_no_results(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory.create_batch(3)
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, search="nonexistent")
        assert len(result.results) == 0
        assert result.total_count == 0

    def test_resolve_all_clients_order_by_email(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(email="charlie@example.com")
        ClientFactory(email="alice@example.com")
        ClientFactory(email="bob@example.com")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, order_by="email")
        assert result.results[0].email == "alice@example.com"
        assert result.results[1].email == "bob@example.com"
        assert result.results[2].email == "charlie@example.com"

    def test_resolve_all_clients_order_by_email_desc(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(email="charlie@example.com")
        ClientFactory(email="alice@example.com")
        ClientFactory(email="bob@example.com")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, order_by="-email")
        assert result.results[0].email == "charlie@example.com"
        assert result.results[1].email == "bob@example.com"
        assert result.results[2].email == "alice@example.com"

    def test_resolve_all_clients_order_by_full_name(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="Charlie", last_name="Davis")
        ClientFactory(first_name="Alice", last_name="Brown")
        ClientFactory(first_name="Bob", last_name="Anderson")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, order_by="full_name")
        assert result.results[0].first_name == "Alice"
        assert result.results[1].first_name == "Bob"
        assert result.results[2].first_name == "Charlie"

    def test_resolve_all_clients_order_by_full_name_desc(self):
        superuser = UserFactory(is_superuser=True)
        ClientFactory(first_name="Charlie", last_name="Davis")
        ClientFactory(first_name="Alice", last_name="Brown")
        ClientFactory(first_name="Bob", last_name="Anderson")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, order_by="-full_name")
        assert result.results[0].first_name == "Charlie"
        assert result.results[1].first_name == "Bob"
        assert result.results[2].first_name == "Alice"

    def test_resolve_all_clients_order_by_created_at(self):
        superuser = UserFactory(is_superuser=True)
        from datetime import datetime, timedelta

        ClientFactory(created_at=datetime.now() - timedelta(days=2))
        ClientFactory(created_at=datetime.now() - timedelta(days=1))
        ClientFactory(created_at=datetime.now())
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, order_by="created_at")
        assert result.results[0].created_at < result.results[1].created_at < result.results[2].created_at

    def test_resolve_all_clients_invalid_order_by(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser
        with pytest.raises(ValueError, match="Invalid order_by value"):
            Query.resolve_all_clients(None, info, order_by="invalid_field")

    def test_resolve_all_clients_order_by_with_search_and_pagination(self):
        superuser = UserFactory(is_superuser=True)
        for i in range(15):
            ClientFactory(first_name="John", last_name=f"Name{i:02d}")
        ClientFactory(first_name="Jane", last_name="Smith")
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_clients(None, info, search="John", order_by="full_name", page=1, page_size=10)
        assert len(result.results) == 10
        assert result.total_count == 15
        assert result.has_next
        assert not result.has_previous

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
        result = Query.resolve_all_packages(None, info)
        assert result.total_count == 3

    def test_resolve_all_packages_as_owner(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        PackageFactory.create_batch(2, client=client)
        info = Mock()
        info.context.user = user
        result = Query.resolve_all_packages(None, info)
        assert result.total_count == 2

    def test_resolve_all_packages_as_user_with_no_client(self):
        user = UserFactory()
        info = Mock()
        info.context.user = user
        with pytest.raises(PermissionDenied):
            Query.resolve_all_packages(None, info)

    def test_resolve_all_packages_pagination(self):
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        PackageFactory.create_batch(20, client=client)
        info = Mock()
        info.context.user = superuser
        result = Query.resolve_all_packages(None, info, page=2, page_size=10)
        assert len(result.results) == 10

    def test_resolve_all_packages_as_client_pagination(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        PackageFactory.create_batch(20, client=client)
        other_client = ClientFactory()
        PackageFactory.create_batch(5, client=other_client)
        info = Mock()
        info.context.user = user
        result = Query.resolve_all_packages(None, info, page=2, page_size=10)
        assert len(result.results) == 10

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
