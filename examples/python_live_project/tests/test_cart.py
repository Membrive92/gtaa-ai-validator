"""
Tests for Shopping Cart functionality.
"""
import time
import pytest

from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from utils.helpers import VALID_PROMO_CODES


class TestCart:
    """Shopping cart test suite."""

    # BAD PRACTICE: Setup that logs in before each test via UI
    @pytest.fixture(autouse=True)
    def setup(self, page, login_page: LoginPage):
        """Login before each test - BAD: Should use API/cookies for speed."""
        login_page.login("testuser@example.com", "Test1234!")
        self.page = page

    def _add_product_to_cart(self):
        """Helper to add a product - BAD: duplicates fixture logic."""
        products = ProductsPage(self.page)
        products.goto()
        products.add_product_to_cart(0)
        time.sleep(2)

    def test_add_item_to_cart(self, cart_page: CartPage):
        """Test adding an item to the cart."""
        self._add_product_to_cart()
        cart_page.goto()
        assert cart_page.get_cart_items_count() > 0

    def test_remove_item_from_cart(self, cart_page: CartPage):
        """Test removing an item from the cart."""
        self._add_product_to_cart()
        cart_page.goto()
        
        initial_count = cart_page.get_cart_items_count()
        cart_page.remove_item(0)
        
        new_count = cart_page.get_cart_items_count()
        assert new_count == initial_count - 1

    def test_update_quantity(self, cart_page: CartPage):
        """Test updating item quantity."""
        self._add_product_to_cart()
        cart_page.goto()
        
        cart_page.update_item_quantity(0, 5)
        time.sleep(2)
        
        # BAD: No good way to verify quantity was actually updated
        total = cart_page.get_cart_total()
        assert total > 0

    def test_apply_valid_promo(self, cart_page: CartPage):
        """Test applying a valid promo code."""
        self._add_product_to_cart()
        cart_page.goto()
        
        # BAD: Using the bad method from cart page that has assertions
        cart_page.apply_promo_and_verify_discount("SAVE20", 20.0)

    def test_apply_invalid_promo(self, cart_page: CartPage):
        """Test applying an invalid promo code."""
        self._add_product_to_cart()
        cart_page.goto()
        
        cart_page.apply_promo_code("INVALIDCODE")
        time.sleep(1)
        
        assert cart_page.page.is_visible(cart_page.PROMO_ERROR_MSG)

    def test_apply_expired_promo(self, cart_page: CartPage):
        """Test applying an expired promo code."""
        self._add_product_to_cart()
        cart_page.goto()
        
        # BAD: Using hardcoded promo from page object
        cart_page.apply_promo_code(cart_page.EXPIRED_PROMO)
        time.sleep(1)
        
        assert cart_page.page.is_visible(cart_page.PROMO_ERROR_MSG)

    def test_empty_cart_display(self, cart_page: CartPage):
        """Test empty cart message."""
        cart_page.goto()
        # BAD: Assumes cart is empty, but previous tests may have left items
        assert cart_page.is_cart_empty() or cart_page.get_cart_items_count() == 0

    def test_cart_persists_after_refresh(self, cart_page: CartPage):
        """Test cart items persist after page refresh."""
        self._add_product_to_cart()
        cart_page.goto()
        
        initial_count = cart_page.get_cart_items_count()
        
        # Refresh the page
        cart_page.page.reload()
        time.sleep(3)  # BAD: hardcoded wait after reload
        
        refreshed_count = cart_page.get_cart_items_count()
        assert refreshed_count == initial_count

    # BAD PRACTICE: Test that spans multiple features
    def test_cart_to_checkout_to_confirmation(self, cart_page: CartPage):
        """Integration test that should be in e2e tests."""
        self._add_product_to_cart()
        cart_page.goto()
        
        # BAD: Using the mega-method that does everything
        order_number = cart_page.complete_checkout_from_cart(promo_code="SAVE10")
        assert order_number
        assert len(order_number) > 3

    # BAD PRACTICE: Multiple unrelated assertions in one test
    def test_cart_summary_calculations(self, cart_page: CartPage):
        """Test cart summary displays correctly."""
        self._add_product_to_cart()
        cart_page.goto()
        
        total = cart_page.get_cart_total()
        items = cart_page.get_item_names()
        count = cart_page.get_cart_items_count()
        
        assert total > 0, "Cart total should be positive"
        assert len(items) > 0, "Should have item names"
        assert count > 0, "Should have items in cart"
        # BAD: These are three different things being tested
        assert count == len(items), "Item count mismatch"
