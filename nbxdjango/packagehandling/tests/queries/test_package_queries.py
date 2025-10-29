from unittest.mock import Mock

import pytest
from django.core.exceptions import PermissionDenied
from packagehandling.factories import ClientFactory, PackageFactory, UserFactory
from packagehandling.schema.queries import Query


@pytest.mark.django_db
class TestPackageQueries:

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


@pytest.mark.django_db
class TestResolveAllPackages:
    def setup_method(self):
        self.info = Mock()

    def test_superuser_can_view_all_packages(self):
        superuser = UserFactory(is_superuser=True)
        self.info.context.user = superuser
        PackageFactory.create_batch(5)
        result = Query.resolve_all_packages(None, self.info)
        assert result.total_count == 5

    def test_superuser_filters_by_client_id(self):
        superuser = UserFactory(is_superuser=True)
        self.info.context.user = superuser
        client1 = ClientFactory()
        client2 = ClientFactory()
        PackageFactory.create_batch(3, client=client1)
        PackageFactory.create_batch(2, client=client2)
        result = Query.resolve_all_packages(None, self.info, client_id=client1.id)
        assert result.total_count == 3

    def test_superuser_with_invalid_client_id(self):
        superuser = UserFactory(is_superuser=True)
        self.info.context.user = superuser
        result = Query.resolve_all_packages(None, self.info, client_id=999)
        assert result.total_count == 0

    def test_client_user_sees_only_their_packages(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        self.info.context.user = user
        PackageFactory.create_batch(2, client=client)
        PackageFactory.create_batch(3)
        result = Query.resolve_all_packages(None, self.info)
        assert result.total_count == 2

    def test_client_user_ignores_client_id_filter(self):
        user = UserFactory()
        client1 = ClientFactory(user=user)
        client2 = ClientFactory()
        self.info.context.user = user
        PackageFactory.create_batch(2, client=client1)
        PackageFactory.create_batch(3, client=client2)
        result = Query.resolve_all_packages(None, self.info, client_id=client2.id)
        assert result.total_count == 2

    def test_user_without_client_raises_permission_denied(self):
        user = UserFactory()
        self.info.context.user = user
        with pytest.raises(PermissionDenied):
            Query.resolve_all_packages(None, self.info)
