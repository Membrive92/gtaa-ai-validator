"""
API Tests for backend services.
BAD PRACTICES: API client assertions, no proper schema validation,
               mixes unit-level and integration-level concerns.
"""
import pytest
from jsonschema import validate, ValidationError

from api.client import APIClient
from api.schemas import USER_SCHEMA, PRODUCT_SCHEMA, ORDER_SCHEMA, PRODUCT_LIST_SCHEMA
from config.settings import Config
from utils.helpers import generate_user_data


class TestUserAPI:
    """Tests for User API endpoints."""

    @pytest.mark.api
    @pytest.mark.smoke
    def test_create_user(self, api_client: APIClient):
        """Test creating a new user."""
        user_data = generate_user_data()
        # BAD: api_client.create_user already has assertions inside
        response = api_client.create_user(
            email=user_data["email"],
            password=user_data["password"],
            name=f"{user_data['first_name']} {user_data['last_name']}"
        )
        
        assert "id" in response
        assert response["email"] == user_data["email"]
        
        # Validate schema
        validate(instance=response, schema=USER_SCHEMA)

    @pytest.mark.api
    def test_get_user(self, api_client: APIClient, test_user):
        """Test getting user by ID."""
        user = api_client.get_user(test_user["id"])
        assert user["id"] == test_user["id"]
        assert user["email"] == test_user["email"]
        validate(instance=user, schema=USER_SCHEMA)

    @pytest.mark.api
    def test_update_user(self, api_client: APIClient, test_user):
        """Test updating user data."""
        updated = api_client.update_user(test_user["id"], {"name": "Updated Name"})
        assert updated["name"] == "Updated Name"

    @pytest.mark.api
    def test_delete_user(self, api_client: APIClient):
        """Test deleting a user."""
        # BAD: Creates user inline instead of using fixture
        user = api_client.create_user()
        result = api_client.delete_user(user["id"])
        assert result is True

    @pytest.mark.api
    def test_login_api(self, api_client: APIClient, test_user):
        """Test login via API."""
        result = api_client.login_user(test_user["email"], test_user["password"])
        assert "token" in result
        assert result["token"]

    # BAD PRACTICE: Test that mutates shared API client state
    @pytest.mark.api
    def test_login_updates_session_token(self, api_client: APIClient, test_user):
        """Tests that login updates the session - BAD: mutates shared client."""
        old_auth = api_client.session.headers.get("Authorization", "")
        api_client.login_user(test_user["email"], test_user["password"])
        new_auth = api_client.session.headers.get("Authorization", "")
        # BAD: This assertion depends on API client implementation detail
        assert old_auth != new_auth


class TestProductAPI:
    """Tests for Product API endpoints."""

    @pytest.mark.api
    @pytest.mark.smoke
    def test_get_products(self, api_client: APIClient):
        """Test getting product list."""
        response = api_client.get_products()
        assert "products" in response
        assert len(response["products"]) > 0
        validate(instance=response, schema=PRODUCT_LIST_SCHEMA)

    @pytest.mark.api
    def test_get_single_product(self, api_client: APIClient, test_product):
        """Test getting a single product."""
        product = api_client.get_product(test_product["id"])
        assert product["id"] == test_product["id"]
        validate(instance=product, schema=PRODUCT_SCHEMA)

    @pytest.mark.api
    def test_create_product(self, api_client: APIClient):
        """Test creating a product."""
        # BAD: Using api_client's test data generation method
        product_data = api_client.generate_test_product()
        created = api_client.create_product(product_data)
        
        assert created["name"] == product_data["name"]
        assert created["price"] == product_data["price"]

    @pytest.mark.api
    def test_search_products(self, api_client: APIClient):
        """Test product search."""
        results = api_client.search_products("test")
        assert "products" in results

    @pytest.mark.api
    def test_get_products_pagination(self, api_client: APIClient):
        """Test product pagination."""
        page1 = api_client.get_products(page=1, per_page=5)
        page2 = api_client.get_products(page=2, per_page=5)
        
        # BAD: Assumes enough products exist for 2 pages
        assert page1["products"] != page2["products"]
        assert page1["page"] == 1
        assert page2["page"] == 2

    @pytest.mark.api
    def test_get_products_by_category(self, api_client: APIClient):
        """Test filtering products by category."""
        response = api_client.get_products(category="Electronics")
        for product in response.get("products", []):
            assert product["category"] == "Electronics"

    # BAD PRACTICE: Uses the "lifecycle" method that has assertions
    @pytest.mark.api
    @pytest.mark.regression
    def test_product_crud_lifecycle(self, api_client: APIClient):
        """Test full CRUD lifecycle."""
        product_data = api_client.generate_test_product()
        # BAD: This method has its own assertions
        result = api_client.verify_product_lifecycle(product_data)
        assert result is True


class TestOrderAPI:
    """Tests for Order API endpoints."""

    @pytest.mark.api
    def test_create_order(self, api_client: APIClient, test_user, test_product):
        """Test creating an order."""
        order = api_client.create_order(
            user_id=test_user["id"],
            items=[{"product_id": test_product["id"], "quantity": 2}],
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "country": "US"
            }
        )
        assert "id" in order
        assert order["status"] in ["pending", "confirmed"]
        validate(instance=order, schema=ORDER_SCHEMA)

    @pytest.mark.api
    def test_get_order(self, api_client: APIClient, test_user, test_product):
        """Test getting an order."""
        # BAD: Creating order inline instead of using fixture
        order = api_client.create_order(
            user_id=test_user["id"],
            items=[{"product_id": test_product["id"], "quantity": 1}],
            shipping_address={"street": "123 St", "city": "City", "state": "ST",
                              "zip": "00000", "country": "US"}
        )
        
        fetched = api_client.get_order(order["id"])
        assert fetched["id"] == order["id"]

    @pytest.mark.api
    def test_get_user_orders(self, api_client: APIClient, test_user):
        """Test getting all orders for a user."""
        orders = api_client.get_user_orders(test_user["id"])
        assert isinstance(orders, list)

    @pytest.mark.api
    def test_cancel_order(self, api_client: APIClient, test_user, test_product):
        """Test cancelling an order."""
        order = api_client.create_order(
            user_id=test_user["id"],
            items=[{"product_id": test_product["id"], "quantity": 1}],
            shipping_address={"street": "123 St", "city": "City", "state": "ST",
                              "zip": "00000", "country": "US"}
        )
        
        cancelled = api_client.cancel_order(order["id"])
        assert cancelled["status"] == "cancelled"

    # BAD PRACTICE: Test saves response to file
    @pytest.mark.api
    def test_order_response_logging(self, api_client: APIClient, test_user, test_product):
        """Test that creates an order and logs the response."""
        api_client.create_order(
            user_id=test_user["id"],
            items=[{"product_id": test_product["id"], "quantity": 1}],
            shipping_address={"street": "123 St", "city": "City", "state": "ST",
                              "zip": "00000", "country": "US"}
        )
        # BAD: API client saving files
        api_client.save_response_to_file("last_order_response.json")


class TestCartAPI:
    """Tests for Cart API endpoints."""

    @pytest.mark.api
    def test_add_to_cart_api(self, api_client: APIClient, test_user, test_product):
        """Test adding item to cart via API."""
        result = api_client.add_to_cart(
            user_id=test_user["id"],
            product_id=test_product["id"],
            quantity=2
        )
        assert "items" in result or "cart" in result

    @pytest.mark.api
    def test_get_cart_api(self, api_client: APIClient, test_user):
        """Test getting user's cart."""
        cart = api_client.get_cart(test_user["id"])
        assert isinstance(cart, dict)

    @pytest.mark.api
    def test_clear_cart_api(self, api_client: APIClient, test_user):
        """Test clearing user's cart."""
        result = api_client.clear_cart(test_user["id"])
        assert result is True
