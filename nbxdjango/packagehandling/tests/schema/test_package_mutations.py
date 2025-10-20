import json

import pytest
from graphene_django.utils.testing import graphql_query
from packagehandling.factories import (
    ClientFactory,
    ConsolidateFactory,
    PackageFactory,
    UserFactory,
)
from packagehandling.models import Package


@pytest.mark.django_db
def test_create_package_superuser_only(client):
    user = UserFactory()
    client.force_login(user)

    client_obj = ClientFactory()

    query = """
        mutation CreatePackage($barcode: String!, $courier: String!, $clientId: ID!) {
            createPackage(barcode: $barcode, courier: $courier, clientId: $clientId) {
                package {
                    id
                    barcode
                }
            }
        }
    """
    variables = {
        "barcode": "123456789",
        "courier": "DHL",
        "clientId": client_obj.id,
    }

    response = graphql_query(query, variables=variables, client=client)
    content = json.loads(response.content)

    assert "errors" in content
    assert content["errors"][0]["message"] == "You do not have permission to perform this action."


@pytest.mark.django_db
def test_create_package_success(client):
    password = "password"
    user = UserFactory(is_superuser=True, is_staff=True, password=password)

    token_auth_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
            }
        }
    """
    token_auth_variables = {"email": user.email, "password": password}
    response = graphql_query(token_auth_query, variables=token_auth_variables, client=client)
    token = json.loads(response.content)["data"]["tokenAuth"]["token"]

    client_obj = ClientFactory()

    query = """
        mutation CreatePackage($barcode: String!, $courier: String!, $clientId: ID!) {
            createPackage(barcode: $barcode, courier: $courier, clientId: $clientId) {
                package {
                    id
                    barcode
                    courier
                }
            }
        }
    """
    variables = {
        "barcode": "123456789",
        "courier": "DHL",
        "clientId": client_obj.id,
    }

    response = graphql_query(query, variables=variables, headers={"HTTP_AUTHORIZATION": f"JWT {token}"}, client=client)
    content = json.loads(response.content)

    assert "errors" not in content
    assert content["data"]["createPackage"]["package"]["barcode"] == "123456789"
    assert content["data"]["createPackage"]["package"]["courier"] == "DHL"


@pytest.mark.django_db
def test_update_package_superuser_only(client):
    user = UserFactory()
    client.force_login(user)

    package = PackageFactory()

    query = """
        mutation UpdatePackage($id: ID!, $comments: String) {
            updatePackage(id: $id, comments: $comments) {
                package {
                    id
                    comments
                }
            }
        }
    """
    variables = {"id": package.id, "comments": "New comments"}

    response = graphql_query(query, variables=variables, client=client)
    content = json.loads(response.content)

    assert "errors" in content
    assert content["errors"][0]["message"] == "You do not have permission to perform this action."


@pytest.mark.django_db
def test_delete_package_superuser_only(client):
    user = UserFactory()
    client.force_login(user)

    package = PackageFactory()

    query = """
        mutation DeletePackage($id: ID!) {
            deletePackage(id: $id) {
                success
            }
        }
    """
    variables = {"id": package.id}

    response = graphql_query(query, variables=variables, client=client)
    content = json.loads(response.content)

    assert "errors" in content
    assert content["errors"][0]["message"] == "You do not have permission to perform this action."


@pytest.mark.django_db
def test_update_package_client_blocked_if_consolidated(client):
    password = "password"
    user = UserFactory(is_superuser=True, is_staff=True, password=password)

    token_auth_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
            }
        }
    """
    token_auth_variables = {"email": user.email, "password": password}
    response = graphql_query(token_auth_query, variables=token_auth_variables, client=client)
    token = json.loads(response.content)["data"]["tokenAuth"]["token"]

    package = PackageFactory()
    consolidate = ConsolidateFactory(client=package.client)
    consolidate.packages.add(package)

    new_client = ClientFactory()

    query = """
        mutation UpdatePackage($id: ID!, $clientId: ID) {
            updatePackage(id: $id, clientId: $clientId) {
                package {
                    id
                }
            }
        }
    """
    variables = {"id": package.id, "clientId": new_client.id}

    response = graphql_query(query, variables=variables, headers={"HTTP_AUTHORIZATION": f"JWT {token}"}, client=client)
    content = json.loads(response.content)
    assert "errors" in content
    assert content["errors"][0]["message"] == "Client cannot be updated for packages already consolidated."


@pytest.mark.django_db
def test_update_package_success(client):
    password = "password"
    user = UserFactory(is_superuser=True, is_staff=True, password=password)

    token_auth_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
            }
        }
    """
    token_auth_variables = {"email": user.email, "password": password}
    response = graphql_query(token_auth_query, variables=token_auth_variables, client=client)
    token = json.loads(response.content)["data"]["tokenAuth"]["token"]

    package = PackageFactory()

    query = """
        mutation UpdatePackage($id: ID!, $comments: String) {
            updatePackage(id: $id, comments: $comments) {
                package {
                    id
                    comments
                }
            }
        }
    """
    variables = {"id": package.id, "comments": "Updated comments"}

    response = graphql_query(query, variables=variables, headers={"HTTP_AUTHORIZATION": f"JWT {token}"}, client=client)
    assert response.status_code == 200
    content = json.loads(response.content)
    assert "errors" not in content
    assert content["data"]["updatePackage"]["package"]["comments"] == "Updated comments"


@pytest.mark.django_db
def test_delete_package_success(client):
    password = "password"
    user = UserFactory(is_superuser=True, is_staff=True, password=password)

    token_auth_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
            }
        }
    """
    token_auth_variables = {"email": user.email, "password": password}
    response = graphql_query(token_auth_query, variables=token_auth_variables, client=client)
    token = json.loads(response.content)["data"]["tokenAuth"]["token"]

    package = PackageFactory()

    query = """
        mutation DeletePackage($id: ID!) {
            deletePackage(id: $id) {
                success
            }
        }
    """
    variables = {"id": package.id}

    response = graphql_query(query, variables=variables, headers={"HTTP_AUTHORIZATION": f"JWT {token}"}, client=client)
    assert response.status_code == 200
    content = json.loads(response.content)
    assert "errors" not in content
    assert content["data"]["deletePackage"]["success"] is True
    assert not Package.objects.filter(id=package.id).exists()


@pytest.mark.django_db
def test_update_package_authenticated_user_not_superuser(client):
    password = "password"
    user = UserFactory(password=password)

    token_auth_query = """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
            }
        }
    """
    token_auth_variables = {"email": user.email, "password": password}
    response = graphql_query(token_auth_query, variables=token_auth_variables, client=client)
    token = json.loads(response.content)["data"]["tokenAuth"]["token"]

    package = PackageFactory()

    query = """
        mutation UpdatePackage($id: ID!, $comments: String) {
            updatePackage(id: $id, comments: $comments) {
                package {
                    id
                    comments
                }
            }
        }
    """
    variables = {"id": package.id, "comments": "New comments"}

    response = graphql_query(query, variables=variables, headers={"HTTP_AUTHORIZATION": f"JWT {token}"}, client=client)
    content = json.loads(response.content)

    assert "errors" in content
    assert content["errors"][0]["message"] == "You do not have permission to perform this action."
