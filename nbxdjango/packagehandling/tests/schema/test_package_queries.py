from unittest.mock import Mock

import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from packagehandling.factories import ClientFactory, PackageFactory, UserFactory
from packagehandling.schema.query_parts.package_queries import PackageQueries


@pytest.mark.django_db
class TestPackageQueries:
    def setup_method(self):
        self.factory = RequestFactory()
        self.queries = PackageQueries()
        self.client = ClientFactory()

    def test_resolve_all_packages_pagination(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory.create_batch(25, client=self.client)
        info = Mock()
        info.context.user = superuser

        # First page
        result = self.queries.resolve_all_packages(None, info, page=1, page_size=10)
        assert len(result.results) == 10
        assert result.total_count == 25
        assert result.has_next is True
        assert result.has_previous is False

        # Second page
        result = self.queries.resolve_all_packages(None, info, page=2, page_size=10)
        assert len(result.results) == 10
        assert result.has_next is True
        assert result.has_previous is True

        # Last page
        result = self.queries.resolve_all_packages(None, info, page=3, page_size=10)
        assert len(result.results) == 5
        assert result.has_next is False
        assert result.has_previous is True

    def test_resolve_all_packages_search(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory(barcode="TRACK123", description="A test package", client=self.client)
        PackageFactory(barcode="DIFFERENT", description="Another thing", client=self.client)
        PackageFactory(barcode="TRACK987", description="More testing", client=self.client)
        info = Mock()
        info.context.user = superuser

        result = self.queries.resolve_all_packages(None, info, search="TRACK")
        assert result.total_count == 2
        assert len(result.results) == 2

        result = self.queries.resolve_all_packages(None, info, search="test")
        assert result.total_count == 2

    def test_resolve_all_packages_ordering(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory(barcode="B", client=self.client)
        PackageFactory(barcode="A", client=self.client)
        PackageFactory(barcode="C", client=self.client)
        info = Mock()
        info.context.user = superuser

        # Ascending
        result = self.queries.resolve_all_packages(None, info, order_by="barcode")
        assert [p.barcode for p in result.results] == ["A", "B", "C"]

        # Descending
        result = self.queries.resolve_all_packages(None, info, order_by="-barcode")
        assert [p.barcode for p in result.results] == ["C", "B", "A"]

    def test_access_control_superuser(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory.create_batch(5, client=self.client)
        info = Mock()
        info.context.user = superuser
        result = self.queries.resolve_all_packages(None, info)
        assert result.total_count == 5

    def test_access_control_client_user(self):
        client_user = UserFactory()
        client = ClientFactory(user=client_user)
        PackageFactory.create_batch(3, client=client)
        PackageFactory.create_batch(2, client=self.client)  # Other packages
        info = Mock()
        info.context.user = client_user
        result = self.queries.resolve_all_packages(None, info)
        assert result.total_count == 3

    def test_access_control_unauthorized(self):
        unauthorized_user = UserFactory()
        info = Mock()
        info.context.user = unauthorized_user
        with pytest.raises(PermissionDenied):
            self.queries.resolve_all_packages(None, info)

    def test_validation_invalid_page_size(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser
        with pytest.raises(ValueError, match="Invalid page_size"):
            self.queries.resolve_all_packages(None, info, page_size=99)

    def test_validation_invalid_order_by(self):
        superuser = UserFactory(is_superuser=True)
        info = Mock()
        info.context.user = superuser
        with pytest.raises(ValueError, match="Invalid order_by value"):
            self.queries.resolve_all_packages(None, info, order_by="invalid_field")
