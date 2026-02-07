"""
Tests for Products functionality.
"""
import time
import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from config.settings import Config
from utils.helpers import take_screenshot


class TestProducts:
    """Product listing and search tests."""

    @pytest.mark.smoke
    def test_products_page_loads(self, products_page: ProductsPage, login_page: LoginPage):
        """Test products page loads with items."""
        # BAD PRACTICE: Login in every test instead of using a fixture
        login_page.login("testuser@example.com", "Test1234!")
        products_page.goto()
        
        count = products_page.get_product_count()
        assert count > 0, "No products displayed on the page"

    def test_search_existing_product(self, products_page: ProductsPage, logged_in_page):
        """Test searching for a product that exists."""
        products_page.goto()
        products_page.search_product("Wireless Mouse")
        
        titles = products_page.get_product_titles()
        # BAD: Fragile assertion that assumes specific product exists
        assert any("wireless" in t.lower() or "mouse" in t.lower() for t in titles), \
            f"'Wireless Mouse' not found in results: {titles}"

    def test_search_nonexistent_product(self, products_page: ProductsPage, logged_in_page):
        """Test searching for a product that doesn't exist."""
        products_page.goto()
        products_page.search_product("xyznonexistentproduct123")
        
        assert products_page.is_no_results_shown(), "Expected no results message"

    def test_filter_by_category(self, products_page: ProductsPage, logged_in_page):
        """Test category filtering."""
        products_page.goto()
        products_page.filter_by_category("Electronics")
        
        # BAD: No assertion that products actually belong to Electronics
        assert products_page.get_product_count() > 0

    def test_price_range_filter(self, products_page: ProductsPage, logged_in_page):
        """Test price range filtering."""
        products_page.goto()
        products_page.set_price_range(10.00, 50.00)
        
        prices = products_page.get_product_prices()
        # BAD: This could fail if price parsing is wrong
        for price in prices:
            assert 10.00 <= price <= 50.00, f"Price {price} outside range"

    @pytest.mark.parametrize("sort_option", [
        "Price: Low to High",
        "Price: High to Low",
        "Name: A to Z",
        "Newest First",
    ])
    def test_sort_products(self, products_page: ProductsPage, logged_in_page, sort_option):
        """Test product sorting."""
        products_page.goto()
        products_page.sort_by(sort_option)
        
        count = products_page.get_product_count()
        assert count > 0, f"No products after sorting by {sort_option}"
        
        if "Low to High" in sort_option:
            prices = products_page.get_product_prices()
            # BAD: Doesn't handle equal prices well
            assert prices == sorted(prices), f"Prices not sorted ascending: {prices}"

    def test_add_product_to_cart(self, products_page: ProductsPage, logged_in_page):
        """Test adding a product to cart from listing."""
        products_page.goto()
        # BAD: Uses the problematic add_first_product_to_cart_and_verify method
        product_name = products_page.add_first_product_to_cart_and_verify()
        assert product_name, "Product name should not be empty"

    def test_product_detail_navigation(self, products_page: ProductsPage, logged_in_page):
        """Test navigating to product detail page."""
        products_page.goto()
        detail_page = products_page.go_to_product_detail(0)
        
        name = detail_page.get_product_name()
        price = detail_page.get_product_price()
        
        assert name, "Product name should not be empty"
        assert price > 0, f"Product price should be positive, got {price}"

    def test_pagination(self, products_page: ProductsPage, logged_in_page):
        """Test product pagination."""
        products_page.goto()
        first_page_titles = products_page.get_product_titles()
        
        products_page.go_to_next_page()
        second_page_titles = products_page.get_product_titles()
        
        # BAD: Assumes there are at least 2 pages
        assert first_page_titles != second_page_titles, \
            "Page 2 should show different products"

    # BAD PRACTICE: Test with API + UI mixed together
    @pytest.mark.regression
    def test_new_product_appears_in_ui(self, products_page: ProductsPage,
                                        api_client, logged_in_page):
        """Create product via API and verify in UI."""
        # Create product via API
        product_data = api_client.generate_test_product()
        created = api_client.create_product(product_data)
        
        # BAD: No wait for data propagation, just sleep
        time.sleep(5)
        
        # Search in UI
        products_page.goto()
        products_page.search_product(created["name"])
        
        titles = products_page.get_product_titles()
        assert created["name"] in titles, \
            f"Created product '{created['name']}' not found in UI"

    # BAD PRACTICE: Test uses page object's file I/O method
    def test_export_products(self, products_page: ProductsPage, logged_in_page):
        """Test exporting products - uses bad page object method."""
        products_page.goto()
        filepath = products_page.export_products_to_json()
        
        import json
        with open(filepath) as f:
            data = json.load(f)
        assert len(data) > 0, "Exported file is empty"

    def test_clear_filters(self, products_page: ProductsPage, logged_in_page):
        """Test clearing filters restores all products."""
        products_page.goto()
        initial_count = products_page.get_product_count()
        
        products_page.filter_by_category("Books")
        filtered_count = products_page.get_product_count()
        
        products_page.clear_filters()
        restored_count = products_page.get_product_count()
        
        assert restored_count >= filtered_count
        # BAD: Assumes count will be exactly same (could change between loads)
        assert restored_count == initial_count
