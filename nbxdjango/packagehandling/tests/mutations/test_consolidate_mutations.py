from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from packagehandling.emails.messages import (
    CONSOLIDATE_CREATED_MESSAGE,
    CONSOLIDATE_CREATED_SUBJECT,
)
from packagehandling.factories import (
    ClientFactory,
    ConsolidateFactory,
    PackageFactory,
    UserFactory,
)
from packagehandling.models import Consolidate
from packagehandling.schema.mutation_parts.consolidate_mutations import (
    CreateConsolidate,
    DeleteConsolidate,
)


@pytest.mark.django_db
class TestDeleteConsolidate:
    def test_delete_consolidate_success(self, info_with_user_factory):
        """
        Test successfully deleting a consolidate as a superuser.
        """
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        consolidate = ConsolidateFactory(client=client)
        info = info_with_user_factory(superuser)

        mutation = DeleteConsolidate()
        result = mutation.mutate(info, id=consolidate.id)

        assert result.success is True
        assert not Consolidate.objects.filter(id=consolidate.id).exists()

    def test_delete_consolidate_not_found(self, info_with_user_factory):
        """
        Test attempting to delete a consolidate with a nonexistent ID.
        """
        superuser = UserFactory(is_superuser=True)
        info = info_with_user_factory(superuser)

        mutation = DeleteConsolidate()
        result = mutation.mutate(info, id=9999)  # Nonexistent ID

        assert result.success is False

    def test_delete_consolidate_as_regular_user_raises_permission_denied(self, info_with_user_factory):
        """
        Test that a regular user cannot delete a consolidate.
        """
        regular_user = UserFactory(is_superuser=False)
        client = ClientFactory()
        consolidate = ConsolidateFactory(client=client)
        info = info_with_user_factory(regular_user)

        mutation = DeleteConsolidate()
        with pytest.raises(PermissionDenied):
            mutation.mutate(info, id=consolidate.id)


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

    def test_create_consolidate_invalid_status(self, info_with_user_factory):
        """
        Test that create consolidate raises a ValidationError if an invalid status is provided.
        """
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        package1 = PackageFactory(client=client, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        with pytest.raises(
            ValidationError, match="Invalid status: 'invalid_status' is not a valid Consolidate status."
        ):
            mutation.mutate(
                info,
                description="Invalid status test",
                status="invalid_status",  # Invalid status
                delivery_date="2025-10-30",
                package_ids=[package1.id],
            )

    def test_create_consolidate_invalid_initial_status(self, info_with_user_factory):
        """
        Test that create consolidate raises a ValidationError if an invalid initial status is provided.
        """
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        package1 = PackageFactory(client=client, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        with pytest.raises(
            ValidationError,
            match="Invalid initial status: a new consolidate cannot start as 'delivered'.",
        ):
            mutation.mutate(
                info,
                description="Invalid initial status test",
                status="delivered",  # Invalid initial status
                delivery_date="2025-10-30",
                package_ids=[package1.id],
            )

    def test_create_consolidate_valid_statuses(self, info_with_user_factory):
        """
        Test that create consolidate succeeds with valid initial statuses.
        """
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory()
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()

        for valid_status in [
            Consolidate.Status.AWAITING_PAYMENT,
            Consolidate.Status.PENDING,
            Consolidate.Status.PROCESSING,
        ]:
            # Create new packages for each iteration to avoid conflicts
            package1 = PackageFactory(client=client, consolidate=None)
            package2 = PackageFactory(client=client, consolidate=None)

            result = mutation.mutate(
                info,
                description=f"Test consolidate with status {valid_status}",
                status=valid_status.value,
                delivery_date="2025-10-30",
                comment=None,
                package_ids=[package1.id, package2.id],
            )

            assert result.consolidate.status == valid_status.value
            assert result.consolidate.description == f"Test consolidate with status {valid_status}"
            assert Consolidate.objects.filter(id=result.consolidate.id).exists()

    @patch("packagehandling.schema.mutation_parts.consolidate_mutations.send_consolidate_email")  # Correct target
    def test_create_consolidate_with_email_sending(self, mock_send_email, info_with_user_factory):
        """
        Test creating a Consolidate with send_email=True. Verifies that the email is sent correctly.
        """
        superuser = UserFactory(is_superuser=True)
        client = ClientFactory(email="test.client@example.com")
        package1 = PackageFactory(client=client, consolidate=None)
        package2 = PackageFactory(client=client, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()
        result = mutation.mutate(
            info,
            description="Test consolidate with email",
            status="pending",
            delivery_date="2025-10-30",
            comment="Include email notification",
            package_ids=[package1.id, package2.id],
            send_email=True,  # Set to True
        )

        # Assert that the consolidate was created successfully
        assert result.consolidate.description == "Test consolidate with email"
        assert result.consolidate.client == client

        # Verify that the email function was called
        mock_send_email.assert_called_once_with(
            CONSOLIDATE_CREATED_SUBJECT,
            CONSOLIDATE_CREATED_MESSAGE,
            ["test.client@example.com"],
        )

    @patch("packagehandling.schema.mutation_parts.consolidate_mutations.send_consolidate_email")  # Correct target
    def test_create_consolidate_with_email_sending_fail_silently(self, mock_send_email, info_with_user_factory):
        """
        Test the handling of email-sending logic when `send_email=True` fails.
        """
        mock_send_email.side_effect = Exception("Email sending error.")  # Simulate failure

        superuser = UserFactory(is_superuser=True)
        client = ClientFactory(email="test.client@example.com")
        package1 = PackageFactory(client=client, consolidate=None)
        package2 = PackageFactory(client=client, consolidate=None)
        info = info_with_user_factory(superuser)

        mutation = CreateConsolidate()

        result = mutation.mutate(
            info,
            description="Test consolidate with failing email",
            status="pending",
            delivery_date="2025-10-30",
            comment="Email task fails silently",
            package_ids=[package1.id, package2.id],
            send_email=True,  # Set to True
        )

        # Assert that the consolidate was created despite email failure
        assert result.consolidate.description == "Test consolidate with failing email"
        assert result.consolidate.client == client

        # Verify that the mocked email function was called despite its failure
        mock_send_email.assert_called_once_with(
            CONSOLIDATE_CREATED_SUBJECT,
            CONSOLIDATE_CREATED_MESSAGE,
            ["test.client@example.com"],
        )
