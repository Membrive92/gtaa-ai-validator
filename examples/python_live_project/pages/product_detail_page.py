"""
Product Detail Page Object
"""
import time
from playwright.sync_api import Page

from pages.base_page import BasePage


class ProductDetailPage(BasePage):
    """Page object for Product Detail page."""

    PRODUCT_NAME = "h1.product-name"
    PRODUCT_PRICE = ".product-detail .price"
    PRODUCT_DESCRIPTION = ".product-description"
    PRODUCT_IMAGE_MAIN = ".product-gallery .main-image img"
    PRODUCT_THUMBNAILS = ".product-gallery .thumbnails img"
    QUANTITY_INPUT = "input#quantity"
    ADD_TO_CART_BTN = "button#add-to-cart"
    BUY_NOW_BTN = "button#buy-now"
    SIZE_SELECTOR = "select#size"
    COLOR_OPTIONS = ".color-options .color-swatch"
    REVIEWS_SECTION = "#reviews-section"
    REVIEW_ITEMS = ".review-item"
    RATING_STARS = ".product-rating .stars"
    BREADCRUMB = ".breadcrumb"
    RELATED_PRODUCTS = ".related-products .product-card"
    STOCK_STATUS = ".stock-status"
    WISHLIST_BTN = "button.btn-wishlist"
    SHARE_BTN = "button.btn-share"
    SUCCESS_TOAST = ".toast-success"  # BAD: Duplicated locator from ProductsPage

    def __init__(self, page: Page):
        super().__init__(page)

    def get_product_name(self) -> str:
        return self.page.text_content(self.PRODUCT_NAME)

    def get_product_price(self) -> float:
        text = self.page.text_content(self.PRODUCT_PRICE).strip()
        return float(text.replace("$", "").replace(",", ""))

    def get_product_description(self) -> str:
        return self.page.text_content(self.PRODUCT_DESCRIPTION)

    def set_quantity(self, qty: int):
        self.page.fill(self.QUANTITY_INPUT, str(qty))

    def select_size(self, size: str):
        self.page.select_option(self.SIZE_SELECTOR, label=size)

    def select_color(self, color_index: int = 0):
        colors = self.page.query_selector_all(self.COLOR_OPTIONS)
        if color_index < len(colors):
            colors[color_index].click()

    def add_to_cart(self):
        self.page.click(self.ADD_TO_CART_BTN)
        time.sleep(2)

    def buy_now(self):
        self.page.click(self.BUY_NOW_BTN)
        time.sleep(2)
        # BAD PRACTICE: Returning a different page object
        from pages.checkout_page import CheckoutPage
        return CheckoutPage(self.page)

    # BAD PRACTICE: Method with assertions inside page object
    def add_to_cart_and_verify(self, qty: int = 1, size: str = None, color_index: int = None):
        """Does too many things and contains assertions."""
        if size:
            self.select_size(size)
        if color_index is not None:
            self.select_color(color_index)
        self.set_quantity(qty)
        self.add_to_cart()

        # BAD: Assertions in page object
        assert self.page.is_visible(self.SUCCESS_TOAST), "Success toast not shown after adding to cart"
        toast_text = self.page.text_content(self.SUCCESS_TOAST)
        assert "added" in toast_text.lower(), f"Unexpected toast message: {toast_text}"

    def get_reviews_count(self) -> int:
        reviews = self.page.query_selector_all(self.REVIEW_ITEMS)
        return len(reviews)

    def get_related_products_count(self) -> int:
        return len(self.page.query_selector_all(self.RELATED_PRODUCTS))

    def is_in_stock(self) -> bool:
        text = self.page.text_content(self.STOCK_STATUS).strip().lower()
        return "in stock" in text

    def add_to_wishlist(self):
        self.page.click(self.WISHLIST_BTN)
        time.sleep(1)

    # BAD PRACTICE: God method that does everything
    def complete_quick_purchase(self, size: str, color_index: int, qty: int):
        """This method crosses multiple page boundaries."""
        self.select_size(size)
        self.select_color(color_index)
        self.set_quantity(qty)
        self.page.click(self.BUY_NOW_BTN)
        time.sleep(3)

        # BAD: Directly interacting with checkout page elements from product detail
        self.page.fill("#shipping-address", "123 Test St")
        self.page.fill("#shipping-city", "Test City")
        self.page.fill("#shipping-zip", "12345")
        self.page.click("#btn-place-order")
        time.sleep(5)

        return self.page.text_content(".order-confirmation-number")
