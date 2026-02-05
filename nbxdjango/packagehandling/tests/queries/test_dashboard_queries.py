"""
Tests for dashboard queries with user-based permissions.
"""

from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from packagehandling.factories import (
    ClientFactory,
    ConsolidateFactory,
    PackageFactory,
    UserFactory,
)
from packagehandling.models import Consolidate
from packagehandling.schema.query_parts.dashboard_queries import (
    DashboardQueries,
    DashboardResolver,
)


@pytest.mark.django_db
class TestDashboardQueries:
    """Tests for dashboard queries with user-based permissions."""

    def test_dashboard_requires_authentication(self):
        """Test that dashboard requires authentication."""
        info = Mock()
        info.context.user = Mock()
        info.context.user.is_authenticated = False

        with pytest.raises(PermissionDenied) as exc_info:
            DashboardQueries.resolve_dashboard(None, info)
        assert "Authentication required" in str(exc_info.value)

    def test_dashboard_for_admin_shows_all_data(self):
        """Test that admin sees all data."""
        admin_user = UserFactory(is_superuser=True)

        # Create multiple clients with packages
        client1 = ClientFactory()
        client2 = ClientFactory()

        # Create packages for different clients
        PackageFactory(client=client1, real_price=100.0, service_price=120.0)
        PackageFactory(client=client1, real_price=50.0, service_price=60.0)
        PackageFactory(client=client2, real_price=75.0, service_price=90.0)

        # Create consolidations
        ConsolidateFactory(client=client1, status=Consolidate.Status.PENDING)
        ConsolidateFactory(client=client2, status=Consolidate.Status.IN_TRANSIT)

        info = Mock()
        info.context.user = admin_user

        dashboard = DashboardQueries.resolve_dashboard(None, info)
        stats = dashboard.stats

        # Admin should see all data
        assert stats.total_packages == 3
        assert stats.total_consolidations == 2
        # 2 created + 1 from admin_user (if has client) or just 2
        assert stats.total_clients >= 2

        # Financial stats
        assert stats.total_real_price == 225.0  # 100 + 50 + 75
        assert stats.total_service_price == 270.0  # 120 + 60 + 90

        # Consolidation stats
        assert stats.consolidations_pending == 1
        assert stats.consolidations_in_transit == 1

    def test_dashboard_for_regular_user_shows_only_own_data(self):
        """Test that regular user sees only their own data."""
        user = UserFactory()
        user_client = ClientFactory(user=user)

        # Create another client with packages (should not be visible)
        other_client = ClientFactory()

        # Create packages for regular user's client
        PackageFactory(client=user_client, real_price=100.0, service_price=120.0)
        PackageFactory(client=user_client, real_price=50.0, service_price=60.0)

        # Create package for other client (should not be visible)
        PackageFactory(client=other_client, real_price=999.0, service_price=999.0)

        # Create consolidations
        ConsolidateFactory(client=user_client, status=Consolidate.Status.PENDING)
        ConsolidateFactory(client=other_client, status=Consolidate.Status.IN_TRANSIT)

        info = Mock()
        info.context.user = user

        dashboard = DashboardQueries.resolve_dashboard(None, info)
        stats = dashboard.stats

        # User should see only their own data
        assert stats.total_packages == 2
        assert stats.total_consolidations == 1

        # Financial stats should be 0 for non-admin
        assert stats.total_real_price == 0.0
        assert stats.total_service_price == 0.0
        assert stats.total_clients == 0

    def test_dashboard_for_user_without_client(self):
        """Test dashboard for user without associated client."""
        user = UserFactory()  # No associated client

        info = Mock()
        info.context.user = user

        dashboard = DashboardQueries.resolve_dashboard(None, info)
        stats = dashboard.stats

        # User without client should see empty data
        assert stats.total_packages == 0
        assert stats.total_consolidations == 0

    def test_dashboard_recent_packages(self):
        """Test recent packages retrieval."""
        user = UserFactory()
        user_client = ClientFactory(user=user)

        # Create packages
        pkg1 = PackageFactory(client=user_client)
        pkg2 = PackageFactory(client=user_client)
        PackageFactory(client=ClientFactory())  # Other user's package

        info = Mock()
        info.context.user = user

        dashboard = DashboardQueries.resolve_dashboard(None, info)
        recent_packages = dashboard.resolve_recent_packages(limit=3)

        assert len(recent_packages) == 2
        package_ids = {p.id for p in recent_packages}
        assert pkg1.id in package_ids
        assert pkg2.id in package_ids

    def test_dashboard_recent_consolidations(self):
        """Test recent consolidations retrieval."""
        user = UserFactory()
        user_client = ClientFactory(user=user)

        # Create consolidations
        cons1 = ConsolidateFactory(client=user_client)
        cons2 = ConsolidateFactory(client=user_client)
        ConsolidateFactory(client=ClientFactory())  # Other user's consolidation

        info = Mock()
        info.context.user = user

        dashboard = DashboardQueries.resolve_dashboard(None, info)
        recent_consolidations = dashboard.resolve_recent_consolidations(limit=3)

        assert len(recent_consolidations) == 2
        consolidation_ids = {c.id for c in recent_consolidations}
        assert cons1.id in consolidation_ids
        assert cons2.id in consolidation_ids


@pytest.mark.django_db
class TestDashboardResolver:
    """Tests for DashboardResolver class."""

    def test_resolver_is_admin_flag(self):
        admin_user = UserFactory(is_superuser=True)
        resolver = DashboardResolver(admin_user)
        assert resolver.is_admin is True

    def test_resolver_regular_user_is_not_admin(self):
        user = UserFactory()
        ClientFactory(user=user)
        resolver = DashboardResolver(user)
        assert resolver.is_admin is False

    def test_resolver_gets_client_for_user_with_client(self):
        user = UserFactory()
        client = ClientFactory(user=user)
        resolver = DashboardResolver(user)
        assert resolver.client == client

    def test_resolver_no_client_for_user_without_client(self):
        user = UserFactory()
        resolver = DashboardResolver(user)
        assert resolver.client is None

    def test_admin_sees_all_packages(self):
        admin_user = UserFactory(is_superuser=True)
        client1 = ClientFactory()
        client2 = ClientFactory()
        PackageFactory(client=client1)
        PackageFactory(client=client2)

        resolver = DashboardResolver(admin_user)
        assert resolver._get_package_queryset().count() == 2

    def test_user_sees_only_own_packages(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)
        other_client = ClientFactory()
        PackageFactory(client=user_client)
        PackageFactory(client=other_client)

        resolver = DashboardResolver(user)
        assert resolver._get_package_queryset().count() == 1

    def test_admin_sees_all_consolidations(self):
        admin_user = UserFactory(is_superuser=True)
        client1 = ClientFactory()
        client2 = ClientFactory()
        ConsolidateFactory(client=client1)
        ConsolidateFactory(client=client2)

        resolver = DashboardResolver(admin_user)
        assert resolver._get_consolidation_queryset().count() == 2

    def test_user_sees_only_own_consolidations(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)
        other_client = ClientFactory()
        ConsolidateFactory(client=user_client)
        ConsolidateFactory(client=other_client)

        resolver = DashboardResolver(user)
        assert resolver._get_consolidation_queryset().count() == 1

    def test_recent_packages_count_calculation(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)

        # Create packages within recent period (last 30 days)
        PackageFactory(client=user_client)
        PackageFactory(client=user_client)

        # Create old package (more than 30 days ago)
        old_package = PackageFactory(client=user_client)
        old_package.created_at = timezone.now() - timedelta(days=31)
        old_package.save(update_fields=["created_at"])

        resolver = DashboardResolver(user)
        stats = resolver.stats

        # Total should be 3, recent should be 2
        assert stats.total_packages == 3
        assert stats.recent_packages == 2

    def test_package_status_counts(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)

        # Package without consolidation (pending)
        PackageFactory(client=user_client)

        # Package in consolidation with in_transit status
        in_transit_consolidation = ConsolidateFactory(client=user_client, status=Consolidate.Status.IN_TRANSIT)
        PackageFactory(client=user_client, consolidate=in_transit_consolidation)

        # Package in consolidation with delivered status
        delivered_consolidation = ConsolidateFactory(client=user_client, status=Consolidate.Status.DELIVERED)
        PackageFactory(client=user_client, consolidate=delivered_consolidation)

        resolver = DashboardResolver(user)
        stats = resolver.stats

        assert stats.packages_pending == 1  # No consolidation
        assert stats.packages_in_transit == 1
        assert stats.packages_delivered == 1

    def test_consolidation_status_counts(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)

        ConsolidateFactory(client=user_client, status=Consolidate.Status.AWAITING_PAYMENT)
        ConsolidateFactory(client=user_client, status=Consolidate.Status.PENDING)
        ConsolidateFactory(client=user_client, status=Consolidate.Status.PROCESSING)
        ConsolidateFactory(client=user_client, status=Consolidate.Status.IN_TRANSIT)
        ConsolidateFactory(client=user_client, status=Consolidate.Status.DELIVERED)
        ConsolidateFactory(client=user_client, status=Consolidate.Status.CANCELLED)

        resolver = DashboardResolver(user)
        stats = resolver.stats

        assert stats.consolidations_awaiting_payment == 1
        assert stats.consolidations_pending == 1
        assert stats.consolidations_processing == 1
        assert stats.consolidations_in_transit == 1
        # Note: delivered and cancelled are not tracked individually in stats

    def test_user_without_client_empty_querysets(self):
        user = UserFactory()  # No client
        resolver = DashboardResolver(user)

        assert resolver._get_package_queryset().count() == 0
        assert resolver._get_consolidation_queryset().count() == 0
        assert resolver._get_client_queryset().count() == 0

    def test_recent_items_respect_limit(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)

        # Create more than limit packages
        for _ in range(5):
            PackageFactory(client=user_client)
            ConsolidateFactory(client=user_client)

        resolver = DashboardResolver(user)

        # Test with limit 2
        recent_packages = resolver.resolve_recent_packages(limit=2)
        recent_consolidations = resolver.resolve_recent_consolidations(limit=2)

        assert len(recent_packages) == 2
        assert len(recent_consolidations) == 2

    def test_admin_financial_stats(self):
        admin_user = UserFactory(is_superuser=True)
        client1 = ClientFactory()
        client2 = ClientFactory()

        PackageFactory(client=client1, real_price=100.0, service_price=120.0)
        PackageFactory(client=client2, real_price=200.0, service_price=250.0)

        resolver = DashboardResolver(admin_user)
        stats = resolver.stats

        assert stats.total_real_price == 300.0
        assert stats.total_service_price == 370.0

    def test_user_financial_stats_are_zero(self):
        user = UserFactory()
        user_client = ClientFactory(user=user)

        PackageFactory(client=user_client, real_price=100.0, service_price=120.0)

        resolver = DashboardResolver(user)
        stats = resolver.stats

        # Non-admin users should see 0 for financial stats
        assert stats.total_real_price == 0.0
        assert stats.total_service_price == 0.0
