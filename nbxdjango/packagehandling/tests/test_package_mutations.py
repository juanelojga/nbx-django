import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory
from graphql.type import GraphQLResolveInfo as ResolveInfo
from packagehandling.factories import (
    ClientFactory,
    ConsolidateFactory,
    PackageFactory,
    UserFactory,
)
from packagehandling.models import Package
from packagehandling.mutations.package_mutations import (
    CreatePackage,
    DeletePackage,
    UpdatePackage,
)


@pytest.fixture
def info_with_user_factory():
    def factory(user):
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
class TestPackageMutations:
    def test_create_package_as_superuser(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client_obj = ClientFactory()
        info = info_with_user_factory(superuser)

        mutation = CreatePackage()
        result = mutation.mutate.__wrapped__(
            mutation,
            info,
            barcode="123456789",
            courier="DHL",
            other_courier="FedEx",
            length=10.5,
            width=5.5,
            height=2.5,
            dimension_unit="cm",
            weight=1.5,
            weight_unit="kg",
            description="Test package",
            purchase_link="http://example.com",
            real_price=100.0,
            service_price=10.0,
            arrival_date="2025-10-27",
            comments="Test comments",
            client_id=client_obj.id,
        )

        assert result.package.barcode == "123456789"
        assert result.package.courier == "DHL"
        assert result.package.other_courier == "FedEx"
        assert result.package.length == 10.5
        assert result.package.width == 5.5
        assert result.package.height == 2.5
        assert result.package.dimension_unit == "cm"
        assert result.package.weight == 1.5
        assert result.package.weight_unit == "kg"
        assert result.package.description == "Test package"
        assert result.package.purchase_link == "http://example.com"
        assert result.package.real_price == 100.0
        assert result.package.service_price == 10.0
        assert str(result.package.arrival_date) == "2025-10-27"
        assert result.package.comments == "Test comments"
        assert Package.objects.filter(barcode="123456789").exists()

    def test_create_package_with_optional_fields(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client_obj = ClientFactory()
        info = info_with_user_factory(superuser)

        mutation = CreatePackage()
        result = mutation.mutate.__wrapped__(
            mutation,
            info,
            barcode="987654321",
            courier="UPS",
            other_courier="Custom Courier",
            description="Another test package",
            client_id=client_obj.id,
        )

        assert result.package.barcode == "987654321"
        assert result.package.courier == "UPS"
        assert result.package.other_courier == "Custom Courier"
        assert result.package.description == "Another test package"
        assert Package.objects.filter(barcode="987654321").exists()

    def test_create_package_missing_required_fields(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        client_obj = ClientFactory()
        info = info_with_user_factory(superuser)

        mutation = CreatePackage()
        with pytest.raises(TypeError) as excinfo:
            mutation.mutate.__wrapped__(info, courier="DHL", client_id=client_obj.id)
        assert "required" in str(excinfo.value)

    def test_create_package_as_regular_user(self, info_with_user_factory):
        user = UserFactory()
        client_obj = ClientFactory()
        info = info_with_user_factory(user)

        mutation = CreatePackage()
        with pytest.raises(PermissionDenied):
            mutation.mutate.__wrapped__(
                mutation,
                info,
                barcode="123456789",
                courier="DHL",
                client_id=client_obj.id,
            )

    def test_update_package_success(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        package = PackageFactory()
        info = info_with_user_factory(superuser)

        mutation = UpdatePackage()
        result = mutation.mutate.__wrapped__(
            mutation,
            info,
            id=package.id,
            courier="FedEx",
            weight=2.5,
            comments="Updated comments",
        )

        assert result.package.courier == "FedEx"
        assert result.package.weight == 2.5
        assert result.package.comments == "Updated comments"
        package.refresh_from_db()
        assert package.courier == "FedEx"
        assert package.weight == 2.5
        assert package.comments == "Updated comments"

    def test_update_package_prohibits_barcode_modification(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        package = PackageFactory()
        info = info_with_user_factory(superuser)

        mutation = UpdatePackage()
        with pytest.raises(ValidationError) as excinfo:
            mutation.mutate.__wrapped__(mutation, info, id=package.id, barcode="new_barcode")
        assert "Barcode cannot be modified" in str(excinfo.value)

    def test_update_package_partial_update(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        package = PackageFactory(courier="DHL")
        info = info_with_user_factory(superuser)

        mutation = UpdatePackage()
        result = mutation.mutate.__wrapped__(mutation, info, id=package.id, courier="UPS")

        assert result.package.courier == "UPS"
        package.refresh_from_db()
        assert package.courier == "UPS"

    def test_update_package_blocked_if_consolidated(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        package = PackageFactory()
        consolidate = ConsolidateFactory(client=package.client)
        consolidate.packages.add(package)
        new_client = ClientFactory()
        info = info_with_user_factory(superuser)

        mutation = UpdatePackage()
        with pytest.raises(ValidationError) as excinfo:
            mutation.mutate.__wrapped__(mutation, info, id=package.id, client_id=new_client.id)
        assert "Client cannot be updated for packages already consolidated." in str(excinfo.value)

    def test_delete_package_as_superuser(self, info_with_user_factory):
        superuser = UserFactory(is_superuser=True)
        package = PackageFactory()
        info = info_with_user_factory(superuser)

        mutation = DeletePackage()
        result = mutation.mutate.__wrapped__(mutation, info, id=package.id)

        assert result.success
        assert not Package.objects.filter(id=package.id).exists()

    def test_delete_package_as_regular_user(self, info_with_user_factory):
        user = UserFactory()
        package = PackageFactory()
        info = info_with_user_factory(user)

        mutation = DeletePackage()
        with pytest.raises(PermissionDenied):
            mutation.mutate.__wrapped__(mutation, info, id=package.id)

    def test_update_package_as_regular_user_permission_denied(self, info_with_user_factory):
        user = UserFactory()
        package = PackageFactory()
        info = info_with_user_factory(user)

        mutation = UpdatePackage()
        with pytest.raises(PermissionDenied):
            mutation.mutate.__wrapped__(mutation, info, id=package.id, comments="New comments")
