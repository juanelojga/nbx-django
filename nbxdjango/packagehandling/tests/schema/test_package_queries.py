from unittest.mock import Mock

import pytest
from django.core.exceptions import PermissionDenied
from packagehandling.factories import ClientFactory, PackageFactory, UserFactory
from packagehandling.schema.query_parts.package_queries import PackageQueries


@pytest.mark.django_db
class TestPackageQueries:
    def setup_method(self):
        self.client = ClientFactory()
        self.info = Mock()
        self.info.context = Mock()

    def test_resolve_all_packages_pagination(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory.create_batch(25, client=self.client)
        self.info.context.user = superuser

        # First page
        result = PackageQueries.resolve_all_packages(None, self.info, page=1, page_size=10)
        assert len(result.results) == 10
        assert result.total_count == 25
        assert result.has_next is True
        assert result.has_previous is False

        # Second page
        result = PackageQueries.resolve_all_packages(None, self.info, page=2, page_size=10)
        assert len(result.results) == 10
        assert result.has_next is True
        assert result.has_previous is True

        # Last page
        result = PackageQueries.resolve_all_packages(None, self.info, page=3, page_size=10)
        assert len(result.results) == 5
        assert result.has_next is False
        assert result.has_previous is True

    def test_resolve_all_packages_search(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory(barcode="TRACK123", description="A test package", client=self.client)
        PackageFactory(barcode="DIFFERENT", description="Another thing", client=self.client)
        PackageFactory(barcode="TRACK987", description="More testing", client=self.client)
        self.info.context.user = superuser

        result = PackageQueries.resolve_all_packages(None, self.info, search="TRACK")
        assert result.total_count == 2
        assert len(result.results) == 2

        result = PackageQueries.resolve_all_packages(None, self.info, search="test")
        assert result.total_count == 2

    def test_resolve_all_packages_ordering(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory(barcode="B", client=self.client)
        PackageFactory(barcode="A", client=self.client)
        PackageFactory(barcode="C", client=self.client)
        self.info.context.user = superuser

        # Ascending
        result = PackageQueries.resolve_all_packages(None, self.info, order_by="barcode")
        assert [p.barcode for p in result.results] == ["A", "B", "C"]

        # Descending
        result = PackageQueries.resolve_all_packages(None, self.info, order_by="-barcode")
        assert [p.barcode for p in result.results] == ["C", "B", "A"]

    def test_access_control_superuser(self):
        superuser = UserFactory(is_superuser=True)
        PackageFactory.create_batch(5, client=self.client)
        self.info.context.user = superuser
        result = PackageQueries.resolve_all_packages(None, self.info)
        assert result.total_count == 5

    def test_access_control_client_user(self):
        client_user = UserFactory()
        client = ClientFactory(user=client_user)
        PackageFactory.create_batch(3, client=client)
        PackageFactory.create_batch(2, client=self.client)  # Other packages
        self.info.context.user = client_user
        result = PackageQueries.resolve_all_packages(None, self.info)
        assert result.total_count == 3

    def test_access_control_unauthorized(self):
        unauthorized_user = UserFactory()
        self.info.context.user = unauthorized_user
        with pytest.raises(PermissionDenied):
            PackageQueries.resolve_all_packages(None, self.info)

    def test_validation_invalid_page_size(self):
        superuser = UserFactory(is_superuser=True)
        self.info.context.user = superuser
        with pytest.raises(ValueError, match="Invalid page_size"):
            PackageQueries.resolve_all_packages(None, self.info, page_size=99)

    def test_validation_invalid_order_by(self):
        superuser = UserFactory(is_superuser=True)
        self.info.context.user = superuser
        with pytest.raises(ValueError, match="Invalid order_by value"):
            PackageQueries.resolve_all_packages(None, self.info, order_by="invalid_field")
