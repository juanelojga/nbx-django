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
            client_id=client_obj.id,
        )

        assert result.package.barcode == "123456789"
        assert result.package.courier == "DHL"
        assert Package.objects.filter(barcode="123456789").exists()

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
        result = mutation.mutate.__wrapped__(mutation, info, id=package.id, comments="Updated comments")

        assert result.package.comments == "Updated comments"
        package.refresh_from_db()
        assert package.comments == "Updated comments"

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
