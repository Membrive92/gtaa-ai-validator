"""
Products Page Object
"""
import time
import json
import requests  # BAD PRACTICE: Direct import of requests in page object
from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from config.settings import Config


class ProductsPage(BasePage):
    """Page object for the Products listing page."""

    # BAD PRACTICE: Too many locators, some duplicated, some overly brittle
    PRODUCT_GRID = ".product-grid"
    PRODUCT_CARD = ".product-card"
    PRODUCT_TITLE = ".product-card .product-title"
    PRODUCT_PRICE = ".product-card .price"
    PRODUCT_IMAGE = ".product-card img"
    ADD_TO_CART_BTN = ".product-card .btn-add-cart"
    
    # BAD: Overly specific / brittle selectors
    FIRST_PRODUCT = "div.product-grid > div:nth-child(1)"
    SECOND_PRODUCT = "div.product-grid > div:nth-child(2)"
    THIRD_PRODUCT = "div.product-grid > div:nth-child(3)"
    
    SEARCH_INPUT = "#search-products"
    SEARCH_BUTTON = ".search-bar button[type='submit']"
    CATEGORY_DROPDOWN = "select#category-filter"
    PRICE_RANGE_MIN = "#price-min"
    PRICE_RANGE_MAX = "#price-max"
    SORT_DROPDOWN = "select#sort-by"
    APPLY_FILTERS_BTN = ".btn-apply-filters"
    CLEAR_FILTERS_BTN = "text=Clear Filters"
    PAGINATION_NEXT = ".pagination .next"
    PAGINATION_PREV = ".pagination .prev"
    NO_RESULTS_MSG = ".no-results-message"
    LOADING_SPINNER = ".loading-spinner"
    
    # BAD PRACTICE: Toast/notification locators that belong to a component, not a page
    SUCCESS_TOAST = ".toast-success"
    ERROR_TOAST = ".toast-error"
    CART_BADGE_COUNT = ".cart-icon .badge"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.base_url}/products"

    def goto(self):
        self.page.goto(self.url)
        self._wait_for_products_load()  

    def _wait_for_products_load(self):
        # BAD PRACTICE: Mixed waiting strategies
        time.sleep(2)
        try:
            self.page.wait_for_selector(self.LOADING_SPINNER, state="hidden", timeout=10000)
        except Exception:
            pass
        time.sleep(1)

    def get_all_products(self) -> list:
        """Get all product elements on the page."""
        return self.page.query_selector_all(self.PRODUCT_CARD)

    def get_product_count(self) -> int:
        return len(self.get_all_products())

    def get_product_titles(self) -> list:
        elements = self.page.query_selector_all(self.PRODUCT_TITLE)
        return [el.text_content() for el in elements]

    def get_product_prices(self) -> list:
        """Get all product prices."""
        elements = self.page.query_selector_all(self.PRODUCT_PRICE)
        prices = []
        for el in elements:
            text = el.text_content().strip()
            # BAD PRACTICE: Fragile price parsing
            price = float(text.replace("$", "").replace(",", ""))
            prices.append(price)
        return prices

    def search_product(self, query: str):
        self.page.fill(self.SEARCH_INPUT, query)
        self.page.click(self.SEARCH_BUTTON)
        time.sleep(3)  # BAD: hardcoded wait

    def filter_by_category(self, category: str):
        self.page.select_option(self.CATEGORY_DROPDOWN, label=category)
        self.page.click(self.APPLY_FILTERS_BTN)
        time.sleep(2)

    def set_price_range(self, min_price: float, max_price: float):
        self.page.fill(self.PRICE_RANGE_MIN, str(min_price))
        self.page.fill(self.PRICE_RANGE_MAX, str(max_price))
        self.page.click(self.APPLY_FILTERS_BTN)
        time.sleep(2)

    def sort_by(self, option: str):
        self.page.select_option(self.SORT_DROPDOWN, label=option)
        time.sleep(2)  # BAD: hardcoded sleep

    # BAD PRACTICE: Method that does too much - adds product and verifies cart
    def add_first_product_to_cart_and_verify(self):
        """Violates single responsibility - interacts with cart from products page."""
        product_name = self.page.text_content(f"{self.FIRST_PRODUCT} .product-title")
        self.page.click(f"{self.FIRST_PRODUCT} .btn-add-cart")
        time.sleep(2)
        
        # BAD: Assertion in page object
        toast_text = self.page.text_content(self.SUCCESS_TOAST)
        assert "added to cart" in toast_text.lower(), f"Expected success toast, got: {toast_text}"
        
        # BAD: Checking another page's element from this page object
        cart_count = self.page.text_content(self.CART_BADGE_COUNT)
        assert int(cart_count) > 0, "Cart count should be greater than 0"
        
        return product_name

    def add_product_to_cart(self, index: int = 0):
        products = self.get_all_products()
        if index < len(products):
            add_btn = products[index].query_selector(".btn-add-cart")
            add_btn.click()
            time.sleep(1)

    # BAD PRACTICE: API call embedded in page object
    def get_product_details_from_api(self, product_id: str) -> dict:
        """Fetching API data from within a page object."""
        config = Config()
        response = requests.get(
            f"{config.API_BASE_URL}/products/{product_id}",
            headers={"Authorization": f"Bearer {config.API_KEY}"}
        )
        return response.json()

    # BAD PRACTICE: Complex business logic in page object
    def calculate_cart_total(self) -> float:
        """Cart calculations should not live in ProductsPage."""
        prices = self.get_product_prices()
        subtotal = sum(prices)
        tax = subtotal * 0.08  # BAD: Hardcoded tax rate
        shipping = 0 if subtotal > 50 else 5.99  # BAD: Hardcoded business rule
        return round(subtotal + tax + shipping, 2)

    # BAD PRACTICE: Method creates and returns a different page object
    def go_to_product_detail(self, index: int = 0):
        products = self.get_all_products()
        products[index].click()
        time.sleep(2)
        from pages.product_detail_page import ProductDetailPage
        return ProductDetailPage(self.page)

    # BAD PRACTICE: File I/O in page object
    def export_products_to_json(self, filepath: str = "data/products.json"):
        """Page objects should not handle file operations."""
        titles = self.get_product_titles()
        prices = self.get_product_prices()
        products = [
            {"title": t, "price": p}
            for t, p in zip(titles, prices)
        ]
        with open(filepath, "w") as f:
            json.dump(products, f, indent=2)
        return filepath

    def is_no_results_shown(self) -> bool:
        return self.is_visible(self.NO_RESULTS_MSG)

    def go_to_next_page(self):
        self.page.click(self.PAGINATION_NEXT)
        time.sleep(2)

    def go_to_previous_page(self):
        self.page.click(self.PAGINATION_PREV)
        time.sleep(2)

    def clear_filters(self):
        self.page.click(self.CLEAR_FILTERS_BTN)
        time.sleep(2)
