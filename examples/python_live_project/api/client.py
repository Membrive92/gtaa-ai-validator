"""
API Client for backend services.
BAD PRACTICE: Mixes API client with test assertions and data generation.
"""
import json
import logging
import requests
from typing import Optional
from faker import Faker

from config.settings import Config

logger = logging.getLogger(__name__)
fake = Faker()


class APIClient:
    """API client for interacting with the ecommerce backend."""

    def __init__(self, base_url: str = None, api_key: str = None):
        config = Config()
        self.base_url = base_url or config.API_BASE_URL
        self.api_key = api_key or config.API_KEY  # BAD: Falls back to hardcoded key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        })
        # BAD PRACTICE: Storing responses as state in the client
        self.last_response = None
        self.last_status_code = None

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        logger.info(f"API {method.upper()} {url}")
        
        response = self.session.request(method, url, **kwargs)
        self.last_response = response
        self.last_status_code = response.status_code
        
        # BAD PRACTICE: Logging response body (may contain sensitive data)
        logger.info(f"Response [{response.status_code}]: {response.text[:500]}")
        
        return response

    # ========== User endpoints ==========
    
    def create_user(self, email: str = None, password: str = None, name: str = None) -> dict:
        """Create a new user."""
        # BAD PRACTICE: Generating test data inside the API client
        payload = {
            "email": email or fake.email(),
            "password": password or "Test1234!",
            "name": name or fake.name(),
            "phone": fake.phone_number(),
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip": fake.zipcode(),
                "country": "US"
            }
        }
        response = self._make_request("post", "/users", json=payload)
        
        # BAD PRACTICE: Assertions in API client
        assert response.status_code == 201, \
            f"Failed to create user: {response.status_code} - {response.text}"
        
        return response.json()

    def get_user(self, user_id: str) -> dict:
        response = self._make_request("get", f"/users/{user_id}")
        return response.json()

    def update_user(self, user_id: str, data: dict) -> dict:
        response = self._make_request("put", f"/users/{user_id}", json=data)
        return response.json()

    def delete_user(self, user_id: str) -> bool:
        response = self._make_request("delete", f"/users/{user_id}")
        return response.status_code == 204

    def login_user(self, email: str, password: str) -> dict:
        """Authenticate user and get token."""
        payload = {"email": email, "password": password}
        response = self._make_request("post", "/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            # BAD PRACTICE: Mutating session state from a "login" method
            self.session.headers["Authorization"] = f"Bearer {data['token']}"
            return data
        return {}

    # ========== Product endpoints ==========

    def get_products(self, page: int = 1, per_page: int = 20, category: str = None) -> dict:
        params = {"page": page, "per_page": per_page}
        if category:
            params["category"] = category
        response = self._make_request("get", "/products", params=params)
        return response.json()

    def get_product(self, product_id: str) -> dict:
        response = self._make_request("get", f"/products/{product_id}")
        return response.json()

    def create_product(self, data: dict) -> dict:
        response = self._make_request("post", "/products", json=data)
        # BAD PRACTICE: Assertion in API client
        assert response.status_code in [200, 201], \
            f"Product creation failed: {response.text}"
        return response.json()

    def search_products(self, query: str) -> dict:
        response = self._make_request("get", "/products/search", params={"q": query})
        return response.json()

    # ========== Order endpoints ==========

    def create_order(self, user_id: str, items: list, shipping_address: dict) -> dict:
        payload = {
            "user_id": user_id,
            "items": items,
            "shipping_address": shipping_address
        }
        response = self._make_request("post", "/orders", json=payload)
        return response.json()

    def get_order(self, order_id: str) -> dict:
        response = self._make_request("get", f"/orders/{order_id}")
        return response.json()

    def get_user_orders(self, user_id: str) -> list:
        response = self._make_request("get", f"/users/{user_id}/orders")
        return response.json().get("orders", [])

    def cancel_order(self, order_id: str) -> dict:
        response = self._make_request("post", f"/orders/{order_id}/cancel")
        return response.json()

    # ========== Cart endpoints ==========

    def get_cart(self, user_id: str) -> dict:
        response = self._make_request("get", f"/users/{user_id}/cart")
        return response.json()

    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> dict:
        payload = {"product_id": product_id, "quantity": quantity}
        response = self._make_request("post", f"/users/{user_id}/cart/items", json=payload)
        return response.json()

    def clear_cart(self, user_id: str) -> bool:
        response = self._make_request("delete", f"/users/{user_id}/cart")
        return response.status_code == 204

    # BAD PRACTICE: Utility/helper functions mixed with API client
    def generate_test_product(self) -> dict:
        """Test data generation does not belong in API client."""
        return {
            "name": fake.catch_phrase(),
            "description": fake.paragraph(nb_sentences=3),
            "price": round(fake.pyfloat(min_value=9.99, max_value=999.99), 2),
            "category": fake.random_element(["Electronics", "Clothing", "Books", "Home"]),
            "stock": fake.random_int(min=0, max=500),
            "sku": fake.bothify("???-####"),
            "images": [fake.image_url() for _ in range(3)]
        }

    # BAD PRACTICE: Reporting mixed with API client
    def save_response_to_file(self, filename: str = "api_response.json"):
        """Saving files should not be in the API client."""
        if self.last_response:
            with open(f"reports/{filename}", "w") as f:
                json.dump({
                    "status_code": self.last_status_code,
                    "body": self.last_response.json() if self.last_response.headers.get(
                        "content-type", "").startswith("application/json") else self.last_response.text,
                    "headers": dict(self.last_response.headers)
                }, f, indent=2)

    # BAD PRACTICE: Full CRUD test workflow in client
    def verify_product_lifecycle(self, product_data: dict) -> bool:
        """An entire test scenario inside the API client."""
        # Create
        created = self.create_product(product_data)
        product_id = created["id"]
        
        # Read
        fetched = self.get_product(product_id)
        assert fetched["name"] == product_data["name"], "Product name mismatch"
        
        # Update
        updated = self._make_request(
            "put", f"/products/{product_id}",
            json={"price": product_data["price"] + 10}
        ).json()
        assert updated["price"] == product_data["price"] + 10, "Price not updated"
        
        # Delete
        delete_resp = self._make_request("delete", f"/products/{product_id}")
        assert delete_resp.status_code == 204, "Delete failed"
        
        return True
