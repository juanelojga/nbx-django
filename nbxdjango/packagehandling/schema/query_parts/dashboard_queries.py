from datetime import timedelta

import graphene
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.utils import timezone

from ...models import Client, Consolidate, Package
from ..types import ConsolidateType, PackageType


class DashboardStatsType(graphene.ObjectType):
    """Dashboard statistics type."""

    # Package stats
    total_packages = graphene.Int()
    recent_packages = graphene.Int()
    packages_pending = graphene.Int()
    packages_in_transit = graphene.Int()
    packages_delivered = graphene.Int()

    # Consolidation stats
    total_consolidations = graphene.Int()
    consolidations_pending = graphene.Int()
    consolidations_processing = graphene.Int()
    consolidations_in_transit = graphene.Int()
    consolidations_awaiting_payment = graphene.Int()

    # Financial stats (admin only)
    total_real_price = graphene.Float()
    total_service_price = graphene.Float()

    # Client stats (admin only)
    total_clients = graphene.Int()


class DashboardType(graphene.ObjectType):
    """Main dashboard type containing stats and recent items."""

    stats = graphene.Field(DashboardStatsType)
    recent_packages = graphene.List(PackageType, limit=graphene.Int(default_value=5))
    recent_consolidations = graphene.List(ConsolidateType, limit=graphene.Int(default_value=5))


class DashboardQueries(graphene.ObjectType):
    dashboard = graphene.Field(DashboardType)

    def resolve_dashboard(self, info):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        return DashboardResolver(user)


class DashboardResolver:
    """Resolver class for dashboard data with user-based filtering."""

    def __init__(self, user):
        self.user = user
        self.is_admin = user.is_superuser
        self.client = getattr(user, "client", None)

    def _get_package_queryset(self):
        """Get base package queryset filtered by user type."""
        if self.is_admin:
            return Package.objects.all()
        if self.client:
            return Package.objects.filter(client=self.client)
        return Package.objects.none()

    def _get_consolidation_queryset(self):
        """Get base consolidation queryset filtered by user type."""
        if self.is_admin:
            return Consolidate.objects.all()
        if self.client:
            return Consolidate.objects.filter(client=self.client)
        return Consolidate.objects.none()

    def _get_client_queryset(self):
        """Get base client queryset - admin only."""
        if self.is_admin:
            return Client.objects.all()
        return Client.objects.none()

    @property
    def stats(self):
        """Calculate dashboard statistics."""
        package_qs = self._get_package_queryset()
        consolidation_qs = self._get_consolidation_queryset()
        client_qs = self._get_client_queryset()

        # Recent period (last 30 days)
        recent_date = timezone.now() - timedelta(days=30)

        stats_data = {
            # Package stats
            "total_packages": package_qs.count(),
            "recent_packages": package_qs.filter(created_at__gte=recent_date).count(),
            # Consolidation-based package stats
            "packages_pending": package_qs.filter(
                Q(consolidate__isnull=True) | Q(consolidate__status=Consolidate.Status.PENDING)
            ).count(),
            "packages_in_transit": package_qs.filter(consolidate__status=Consolidate.Status.IN_TRANSIT).count(),
            "packages_delivered": package_qs.filter(consolidate__status=Consolidate.Status.DELIVERED).count(),
            # Consolidation stats
            "total_consolidations": consolidation_qs.count(),
            "consolidations_awaiting_payment": consolidation_qs.filter(
                status=Consolidate.Status.AWAITING_PAYMENT
            ).count(),
            "consolidations_pending": consolidation_qs.filter(status=Consolidate.Status.PENDING).count(),
            "consolidations_processing": consolidation_qs.filter(status=Consolidate.Status.PROCESSING).count(),
            "consolidations_in_transit": consolidation_qs.filter(status=Consolidate.Status.IN_TRANSIT).count(),
        }

        # Admin-only stats
        if self.is_admin:
            price_aggregates = package_qs.aggregate(
                total_real=Sum("real_price"),
                total_service=Sum("service_price"),
            )
            stats_data["total_real_price"] = price_aggregates["total_real"] or 0.0
            stats_data["total_service_price"] = price_aggregates["total_service"] or 0.0
            stats_data["total_clients"] = client_qs.count()
        else:
            stats_data["total_real_price"] = 0.0
            stats_data["total_service_price"] = 0.0
            stats_data["total_clients"] = 0

        return DashboardStatsType(**stats_data)

    def resolve_recent_packages(self, limit=5):
        """Get recent packages based on user type."""
        return self._get_package_queryset().select_related("client", "consolidate").order_by("-created_at")[:limit]

    def resolve_recent_consolidations(self, limit=5):
        """Get recent consolidations based on user type."""
        return (
            self._get_consolidation_queryset()
            .select_related("client")
            .prefetch_related("packages")
            .order_by("-created_at")[:limit]
        )
