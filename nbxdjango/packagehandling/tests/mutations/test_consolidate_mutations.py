import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from packagehandling.factories import (
    ClientFactory,
    ConsolidateFactory,
    PackageFactory,
    UserFactory,
)
from packagehandling.models import Consolidate
from packagehandling.schema.mutation_parts.consolidate_mutations import (
    CreateConsolidate,
)


@pytest.fixture
def info_with_user_factory():
    """
    Fixture to simulate GraphQL's ResolveInfo context with an authenticated user.
    """

    def factory(user):
        from django.test import RequestFactory
        from graphql.type import GraphQLResolveInfo as ResolveInfo

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
class TestCreateConsolidate:
    def test_create_consolidate_success(self, info_with_user_factory):
        """
        Test creating a Consolidate as a superuser with valid data.
        """
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        package1 = PackageFactory(client=client, consolidate=None)
        package2 = PackageFactory(client=client, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        result = mutation.mutate(
            info,
            description="Test consolidate",
            status="pending",
            delivery_date="2025-10-30",
            comment="Test comment",
            package_ids=[package1.id, package2.id],
        )

        assert result.consolidate.description == "Test consolidate"
        assert result.consolidate.status == "pending"
        assert str(result.consolidate.delivery_date) == "2025-10-30"
        assert result.consolidate.comment == "Test comment"
        assert result.consolidate.client == client

        # Verify the packages are linked to the consolidate
        assert set(result.consolidate.packages.all()) == {package1, package2}
        # Verify database entry exists
        assert Consolidate.objects.filter(id=result.consolidate.id).exists()

    def test_create_consolidate_missing_package_ids(self, info_with_user_factory):
        """
        Test that create consolidate raises a ValidationError if no package IDs are provided.
        """
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        with pytest.raises(ValidationError, match="At least one package ID is required."):
            mutation.mutate(
                info,
                description="Test consolidate",
                status="pending",
                delivery_date="2025-10-30",
                package_ids=[],
            )

    def test_create_consolidate_with_nonexistent_package_ids(self, info_with_user_factory):
        """
        Test that create consolidate raises a ValidationError if one or more package IDs do not exist.
        """
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        with pytest.raises(ValidationError, match="One or more packages do not exist."):
            mutation.mutate(
                info,
                description="Test consolidate",
                status="pending",
                delivery_date="2025-10-30",
                package_ids=[999, 1000],  # Nonexistent IDs
            )

    def test_create_consolidate_with_different_clients(self, info_with_user_factory):
        """
        Test that create consolidate raises a ValidationError if packages belong to different clients.
        """
        superuser = UserFactory(is_superuser=True)
        client1 = ClientFactory()
        client2 = ClientFactory()
        package1 = PackageFactory(client=client1, consolidate=None)
        package2 = PackageFactory(client=client2, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        with pytest.raises(ValidationError, match="All packages must belong to the same client."):
            mutation.mutate(
                info,
                description="Test consolidate",
                status="pending",
                delivery_date="2025-10-30",
                package_ids=[package1.id, package2.id],
            )

    def test_create_consolidate_with_already_consolidated_packages(self, info_with_user_factory):
        """
        Test that create consolidate raises a ValidationError if one or more packages are already part of a consolidate.
        """
        superuser = UserFactory(is_superuser=True)
        consolidate = ConsolidateFactory()
        package1 = PackageFactory(client=consolidate.client, consolidate=consolidate)
        package2 = PackageFactory(client=consolidate.client, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        with pytest.raises(ValidationError, match="Package already belongs to a consolidate."):
            mutation.mutate(
                info,
                description="Test consolidate",
                status="pending",
                delivery_date="2025-10-30",
                package_ids=[package1.id, package2.id],
            )

    def test_create_consolidate_as_regular_user_raises_permission_denied(self, info_with_user_factory):
        """
        Test that a regular user is not allowed to create a consolidate.
        """
        regular_user = UserFactory(is_superuser=False)
        client = ClientFactory()
        package1 = PackageFactory(client=client, consolidate=None)
        info = info_with_user_factory(regular_user)

        mutation = CreateConsolidate()
        with pytest.raises(PermissionDenied):
            mutation.mutate(
                info,
                description="Test consolidate",
                status="pending",
                delivery_date="2025-10-30",
                package_ids=[package1.id],
            )
