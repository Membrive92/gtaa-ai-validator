"""
End-to-End Checkout Tests.
BAD PRACTICES: Long test methods, poor isolation, mixed concerns.
"""
import time
import pytest

from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from api.client import APIClient
from config.settings import Config
from utils.helpers import generate_shipping_data, generate_credit_card, take_screenshot


class TestCheckoutE2E:
    """End-to-end checkout tests."""

    # BAD PRACTICE: Hardcoded test data in test class
    SHIPPING_DATA = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@test.com",
        "address": "123 Main Street",
        "city": "New York",
        "state": "New York",
        "zip_code": "10001",
        "country": "United States",
        "phone": "+1-555-0100"
    }

    # BAD PRACTICE: Super long test method that tests the entire flow
    @pytest.mark.e2e
    @pytest.mark.smoke
    def test_complete_checkout_flow(self, page, login_page: LoginPage):
        """Complete e2e test from login to order confirmation.
        BAD: This is way too long and tests multiple things.
        """
        # Step 1: Login
        login_page.login("testuser@example.com", "Test1234!")
        assert "dashboard" in page.url or "home" in page.url
        
        # Step 2: Browse products
        products = ProductsPage(page)  # BAD: Creating page objects inline
        products.goto()
        assert products.get_product_count() > 0
        
        # Step 3: Add product to cart
        products.add_product_to_cart(0)
        time.sleep(2)
        
        # Step 4: Add another product
        products.add_product_to_cart(1)
        time.sleep(2)
        
        # Step 5: Go to cart
        cart = CartPage(page)  # BAD: Creating page objects inline
        cart.goto()
        assert cart.get_cart_items_count() >= 2
        
        # Step 6: Apply promo code
        cart.apply_promo_code("SAVE20")
        time.sleep(2)
        
        # Step 7: Proceed to checkout
        checkout = cart.proceed_to_checkout()
        time.sleep(2)
        
        # Step 8: Fill shipping info
        checkout.fill_shipping_info(**self.SHIPPING_DATA)
        time.sleep(1)
        
        # Step 9: Fill payment info
        checkout.fill_payment_info(
            card_number="4111111111111111",
            expiry="12/26",
            cvv="123",
            holder="John Doe"
        )
        
        # Step 10: Place order
        checkout.place_order()
        time.sleep(5)  # BAD: Long hardcoded wait
        
        # Step 11: Verify confirmation
        order_number = checkout.get_order_number()
        assert order_number, "Order number should not be empty"
        assert len(order_number) > 0
        
        # Step 12: BAD - Verify via API from UI test
        config = Config()
        import requests
        resp = requests.get(
            f"{config.API_BASE_URL}/orders/{order_number}",
            headers={"Authorization": f"Bearer {config.API_KEY}"}
        )
        assert resp.status_code == 200

    @pytest.mark.e2e
    def test_checkout_with_generated_data(self, page, login_page: LoginPage):
        """Test checkout with randomly generated data."""
        login_page.login("testuser@example.com", "Test1234!")
        
        products = ProductsPage(page)
        products.goto()
        products.add_product_to_cart(0)
        
        cart = CartPage(page)
        cart.goto()
        
        # BAD PRACTICE: Using cart page's complete_checkout_from_cart method
        order_number = cart.complete_checkout_from_cart(promo_code="SAVE10")
        assert order_number, "Order should have been placed"

    @pytest.mark.e2e
    def test_checkout_empty_cart(self, page, login_page: LoginPage):
        """Test that checkout is not possible with empty cart."""
        login_page.login("testuser@example.com", "Test1234!")
        
        cart = CartPage(page)
        cart.goto()
        
        # BAD: Using try/except for expected behavior
        try:
            checkout = cart.proceed_to_checkout()
            # If we get here, checkout should show error
            assert page.is_visible(".cart-empty-error")
        except Exception:
            # BAD: Swallowing exception as "passing"
            assert cart.is_cart_empty(), "Cart should be empty"

    @pytest.mark.e2e
    def test_checkout_invalid_payment(self, page, login_page: LoginPage,
                                       checkout_page: CheckoutPage):
        """Test checkout with invalid payment info."""
        login_page.login("testuser@example.com", "Test1234!")
        
        # BAD: Navigating to checkout directly might not work without cart items
        products = ProductsPage(page)
        products.goto()
        products.add_product_to_cart(0)
        
        cart = CartPage(page)
        cart.goto()
        cart.proceed_to_checkout()
        time.sleep(2)
        
        # BAD: Creating new CheckoutPage instead of using the returned one
        checkout = CheckoutPage(page)
        checkout.fill_shipping_info(**self.SHIPPING_DATA)
        checkout.fill_payment_info(
            card_number="0000000000000000",  # Invalid card
            expiry="01/20",  # Expired
            cvv="00"  # Invalid CVV
        )
        checkout.place_order()
        time.sleep(3)
        
        error = checkout.get_payment_error()
        assert error, "Expected payment error message"

    @pytest.mark.e2e
    def test_checkout_missing_shipping_info(self, page, login_page: LoginPage):
        """Test checkout with missing required fields."""
        login_page.login("testuser@example.com", "Test1234!")
        
        products = ProductsPage(page)
        products.goto()
        products.add_product_to_cart(0)
        
        cart = CartPage(page)
        cart.goto()
        checkout = cart.proceed_to_checkout()
        
        # Skip shipping info, go directly to payment
        checkout.fill_payment_info()
        checkout.place_order()
        time.sleep(2)
        
        errors = checkout.get_field_errors()
        assert len(errors) > 0, "Should have validation errors for missing shipping info"

    # BAD PRACTICE: Test that modifies cart then doesn't clean up
    @pytest.mark.regression
    def test_update_cart_quantity_and_checkout(self, page, login_page: LoginPage):
        """Test updating quantity in cart then checking out."""
        login_page.login("testuser@example.com", "Test1234!")
        
        products = ProductsPage(page)
        products.goto()
        products.add_product_to_cart(0)
        
        cart = CartPage(page)
        cart.goto()
        
        original_total = cart.get_cart_total()
        cart.update_item_quantity(0, 3)
        time.sleep(2)
        
        new_total = cart.get_cart_total()
        # BAD: Imprecise assertion
        assert new_total > original_total, "Total should increase with more items"
        
        checkout = cart.proceed_to_checkout()
        checkout.fill_shipping_info(**self.SHIPPING_DATA)
        checkout.fill_payment_info()
        checkout.place_order()
        
        order_number = checkout.get_order_number()
        assert order_number

    # BAD PRACTICE: Test depends on specific product existing
    @pytest.mark.e2e
    def test_buy_now_from_product_detail(self, page, login_page: LoginPage):
        """Test Buy Now flow from product detail page."""
        login_page.login("testuser@example.com", "Test1234!")
        
        products = ProductsPage(page)
        products.goto()
        detail = products.go_to_product_detail(0)
        
        # BAD: Using the god method from product detail page
        order_number = detail.complete_quick_purchase(
            size="Medium",
            color_index=0,
            qty=1
        )
        assert order_number, "Should receive order confirmation number"
