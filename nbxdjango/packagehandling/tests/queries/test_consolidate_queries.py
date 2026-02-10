import pytest
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase
from packagehandling.factories import ClientFactory, ConsolidateFactory, UserFactory
from packagehandling.models import Consolidate

User = get_user_model()


@pytest.mark.django_db
class TestAllConsolidatesQuery(JSONWebTokenTestCase):
    """Test allConsolidates query with pagination, filtering, and ordering."""

    ALL_CONSOLIDATES_QUERY = """
        query AllConsolidates($page: Int, $pageSize: Int, $orderBy: String, $status: String) {
            allConsolidates(page: $page, pageSize: $pageSize, orderBy: $orderBy, status: $status) {
                results {
                    id
                    description
                    status
                    deliveryDate
                    createdAt
                    client {
                        id
                        email
                    }
                }
                totalCount
                page
                pageSize
                hasNext
                hasPrevious
            }
        }
    """

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = UserFactory(email="admin@example.com", is_superuser=True, password="admin123")

        # Create two clients with their users
        self.client1 = ClientFactory(email="client1@example.com")
        self.client2 = ClientFactory(email="client2@example.com")

        # Create consolidates for client1
        self.consolidates_client1 = [
            ConsolidateFactory(
                client=self.client1,
                status=Consolidate.Status.PENDING,
                description="Consolidate 1 for client1",
            ),
            ConsolidateFactory(
                client=self.client1,
                status=Consolidate.Status.PROCESSING,
                description="Consolidate 2 for client1",
            ),
            ConsolidateFactory(
                client=self.client1,
                status=Consolidate.Status.IN_TRANSIT,
                description="Consolidate 3 for client1",
            ),
        ]

        # Create consolidates for client2
        self.consolidates_client2 = [
            ConsolidateFactory(
                client=self.client2,
                status=Consolidate.Status.DELIVERED,
                description="Consolidate 1 for client2",
            ),
            ConsolidateFactory(
                client=self.client2,
                status=Consolidate.Status.PENDING,
                description="Consolidate 2 for client2",
            ),
        ]

    # Permission tests
    def test_admin_can_access_all_consolidates(self):
        """Admin users should see all consolidates from all clients."""
        self.client.authenticate(self.admin_user)
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is None
        assert response.data["allConsolidates"]["totalCount"] == 5
        assert len(response.data["allConsolidates"]["results"]) == 5

    def test_client_can_only_access_own_consolidates(self):
        """Client users should only see their own consolidates."""
        self.client.authenticate(self.client1.user)
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is None
        assert response.data["allConsolidates"]["totalCount"] == 3
        assert len(response.data["allConsolidates"]["results"]) == 3

        # Verify all returned consolidates belong to client1
        for consolidate in response.data["allConsolidates"]["results"]:
            assert consolidate["client"]["id"] == str(self.client1.id)

    def test_unauthenticated_user_gets_permission_denied(self):
        """Unauthenticated users should get PermissionDenied error."""
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is not None
        assert "permission" in response.errors[0].message.lower()

    # Pagination tests
    def test_default_pagination(self):
        """Test default pagination (page=1, pageSize=100)."""
        self.client.authenticate(self.admin_user)
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["page"] == 1
        assert data["pageSize"] == 10
        assert data["totalCount"] == 5
        assert data["hasNext"] is False
        assert data["hasPrevious"] is False

    def test_custom_pagination_values(self):
        """Test custom pagination with page=2, pageSize=20."""
        self.client.authenticate(self.admin_user)
        
        # Create more data to test pagination (currently have 5, need more for page 2 with pageSize=20)
        for _ in range(35):
            ConsolidateFactory(client=self.client1)
        # Now we have 40 total
        
        variables = {"page": 2, "pageSize": 20}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["page"] == 2
        assert data["pageSize"] == 20
        assert data["totalCount"] == 40
        assert len(data["results"]) == 20
        assert data["hasNext"] is False  # Page 2 is the last page
        assert data["hasPrevious"] is True

    def test_invalid_page_size_raises_error(self):
        """Test that invalid pageSize values raise ValueError."""
        self.client.authenticate(self.admin_user)
        variables = {"pageSize": 105}  # Invalid: not in [10, 20, 50, 100]
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is not None
        assert "Invalid page_size" in response.errors[0].message

    def test_total_count_calculation(self):
        """Test that totalCount is calculated correctly."""
        self.client.authenticate(self.client2.user)
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is None
        assert response.data["allConsolidates"]["totalCount"] == 2

    def test_has_next_and_has_previous_flags(self):
        """Test hasNext and hasPrevious flags for multi-page results."""
        self.client.authenticate(self.admin_user)

        # Create more consolidates for multi-page testing (currently we have 5, need more)
        for _ in range(15):
            ConsolidateFactory(client=self.client1)

        # Now we have 20 total consolidates

        # Page 1
        variables = {"page": 1, "pageSize": 10}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)
        data = response.data["allConsolidates"]
        assert data["hasNext"] is True
        assert data["hasPrevious"] is False

        # Page 2 (middle page)
        variables = {"page": 2, "pageSize": 10}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)
        data = response.data["allConsolidates"]
        assert data["hasNext"] is False  # Page 2 is last page with 20 items
        assert data["hasPrevious"] is True

    # Ordering tests
    def test_ordering_by_created_at_desc(self):
        """Test ordering by created_at descending (default)."""
        self.client.authenticate(self.admin_user)
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Verify descending order (newest first)
        for i in range(len(results) - 1):
            assert results[i]["createdAt"] >= results[i + 1]["createdAt"]

    def test_ordering_by_created_at_asc(self):
        """Test ordering by created_at ascending."""
        self.client.authenticate(self.admin_user)
        variables = {"orderBy": "created_at"}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Verify ascending order (oldest first)
        for i in range(len(results) - 1):
            assert results[i]["createdAt"] <= results[i + 1]["createdAt"]

    def test_ordering_by_delivery_date_desc(self):
        """Test ordering by delivery_date descending."""
        self.client.authenticate(self.admin_user)
        variables = {"orderBy": "-delivery_date"}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Verify descending order
        for i in range(len(results) - 1):
            if results[i]["deliveryDate"] and results[i + 1]["deliveryDate"]:
                assert results[i]["deliveryDate"] >= results[i + 1]["deliveryDate"]

    def test_ordering_by_delivery_date_asc(self):
        """Test ordering by delivery_date ascending."""
        self.client.authenticate(self.admin_user)
        variables = {"orderBy": "delivery_date"}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Verify ascending order
        for i in range(len(results) - 1):
            if results[i]["deliveryDate"] and results[i + 1]["deliveryDate"]:
                assert results[i]["deliveryDate"] <= results[i + 1]["deliveryDate"]

    def test_ordering_by_status_asc(self):
        """Test ordering by status ascending."""
        self.client.authenticate(self.admin_user)
        variables = {"orderBy": "status"}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Verify ascending order
        for i in range(len(results) - 1):
            assert results[i]["status"] <= results[i + 1]["status"]

    def test_ordering_by_status_desc(self):
        """Test ordering by status descending."""
        self.client.authenticate(self.admin_user)
        variables = {"orderBy": "-status"}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Verify descending order
        for i in range(len(results) - 1):
            assert results[i]["status"] >= results[i + 1]["status"]

    def test_default_ordering_applied(self):
        """Test that default ordering (-created_at) is applied when no orderBy provided."""
        self.client.authenticate(self.admin_user)
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY)

        assert response.errors is None
        results = response.data["allConsolidates"]["results"]

        # Should be ordered by created_at descending (newest first)
        for i in range(len(results) - 1):
            assert results[i]["createdAt"] >= results[i + 1]["createdAt"]

    def test_invalid_order_by_field_raises_error(self):
        """Test that invalid orderBy field raises ValueError."""
        self.client.authenticate(self.admin_user)
        variables = {"orderBy": "invalid_field"}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is not None
        assert "Invalid order_by value" in response.errors[0].message

    # Status filtering tests
    def test_filter_by_pending_status(self):
        """Test filtering by PENDING status."""
        self.client.authenticate(self.admin_user)
        variables = {"status": Consolidate.Status.PENDING}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 2  # 1 from client1, 1 from client2
        for consolidate in data["results"]:
            assert consolidate["status"] == "PENDING"

    def test_filter_by_processing_status(self):
        """Test filtering by PROCESSING status."""
        self.client.authenticate(self.admin_user)
        variables = {"status": Consolidate.Status.PROCESSING}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 1  # Only 1 from client1
        assert data["results"][0]["status"] == "PROCESSING"

    def test_filter_by_in_transit_status(self):
        """Test filtering by IN_TRANSIT status."""
        self.client.authenticate(self.admin_user)
        variables = {"status": Consolidate.Status.IN_TRANSIT}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 1
        assert data["results"][0]["status"] == "IN_TRANSIT"

    def test_filter_by_delivered_status(self):
        """Test filtering by DELIVERED status."""
        self.client.authenticate(self.admin_user)
        variables = {"status": Consolidate.Status.DELIVERED}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 1
        assert data["results"][0]["status"] == "DELIVERED"

    def test_filter_with_no_results(self):
        """Test filtering by status that has no matches."""
        self.client.authenticate(self.admin_user)
        variables = {"status": Consolidate.Status.CANCELLED}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 0
        assert len(data["results"]) == 0

    def test_filter_combined_with_pagination(self):
        """Test filtering combined with pagination."""
        self.client.authenticate(self.admin_user)
        variables = {"status": Consolidate.Status.PENDING, "page": 1, "pageSize": 10}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 2  # 2 pending consolidates total
        assert len(data["results"]) == 2  # Both fit on one page with pageSize=10
        assert data["hasNext"] is False
        assert data["hasPrevious"] is False
        assert data["results"][0]["status"] == "PENDING"

    def test_client_filter_respects_permissions(self):
        """Test that clients can only filter their own consolidates."""
        self.client.authenticate(self.client1.user)
        variables = {"status": Consolidate.Status.PENDING}
        response = self.client.execute(self.ALL_CONSOLIDATES_QUERY, variables=variables)

        assert response.errors is None
        data = response.data["allConsolidates"]
        assert data["totalCount"] == 1  # Only client1's pending consolidate
        assert data["results"][0]["client"]["id"] == str(self.client1.id)


@pytest.mark.django_db
class TestConsolidateByIdQuery(JSONWebTokenTestCase):
    """Test consolidateById query."""

    CONSOLIDATE_BY_ID_QUERY = """
        query ConsolidateById($id: ID!) {
            consolidateById(id: $id) {
                id
                description
                status
                client {
                    id
                    email
                }
            }
        }
    """

    def setUp(self):
        """Set up test data."""
        self.admin_user = UserFactory(email="admin@example.com", is_superuser=True, password="admin123")
        self.client1 = ClientFactory(email="client1@example.com")
        self.client2 = ClientFactory(email="client2@example.com")

        self.consolidate1 = ConsolidateFactory(client=self.client1)
        self.consolidate2 = ConsolidateFactory(client=self.client2)

    def test_admin_can_view_any_consolidate(self):
        """Admin can view any consolidate."""
        self.client.authenticate(self.admin_user)
        variables = {"id": str(self.consolidate1.id)}
        response = self.client.execute(self.CONSOLIDATE_BY_ID_QUERY, variables=variables)

        assert response.errors is None
        assert response.data["consolidateById"]["id"] == str(self.consolidate1.id)

    def test_client_can_view_own_consolidate(self):
        """Client can view their own consolidate."""
        self.client.authenticate(self.client1.user)
        variables = {"id": str(self.consolidate1.id)}
        response = self.client.execute(self.CONSOLIDATE_BY_ID_QUERY, variables=variables)

        assert response.errors is None
        assert response.data["consolidateById"]["id"] == str(self.consolidate1.id)

    def test_client_cannot_view_other_consolidate(self):
        """Client cannot view another client's consolidate."""
        self.client.authenticate(self.client1.user)
        variables = {"id": str(self.consolidate2.id)}
        response = self.client.execute(self.CONSOLIDATE_BY_ID_QUERY, variables=variables)

        assert response.errors is not None
        assert "permission" in response.errors[0].message.lower()
