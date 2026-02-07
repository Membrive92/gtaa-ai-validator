"""
Cart Page Object
"""
import time
from playwright.sync_api import Page

from pages.base_page import BasePage
from config.settings import Config


class CartPage(BasePage):
    """Page object for Shopping Cart page."""

    CART_ITEMS = ".cart-item"
    CART_ITEM_NAME = ".cart-item .item-name"
    CART_ITEM_PRICE = ".cart-item .item-price"
    CART_ITEM_QTY = ".cart-item input.qty"
    CART_ITEM_REMOVE = ".cart-item .btn-remove"
    CART_SUBTOTAL = ".cart-summary .subtotal"
    CART_TAX = ".cart-summary .tax"
    CART_SHIPPING = ".cart-summary .shipping"
    CART_TOTAL = ".cart-summary .total"
    PROMO_CODE_INPUT = "#promo-code"
    APPLY_PROMO_BTN = "button#apply-promo"
    PROMO_SUCCESS_MSG = ".promo-success"
    PROMO_ERROR_MSG = ".promo-error"
    CHECKOUT_BTN = "button#proceed-checkout"
    CONTINUE_SHOPPING_BTN = "a.continue-shopping"
    EMPTY_CART_MSG = ".empty-cart-message"
    CART_BADGE = ".cart-icon .badge"  # BAD: Duplicated from multiple pages

    # BAD PRACTICE: Hardcoded promo codes in page object
    VALID_PROMO = "SAVE20"
    EXPIRED_PROMO = "SUMMER2023"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.base_url}/cart"

    def goto(self):
        self.page.goto(self.url)
        time.sleep(2)

    def get_cart_items_count(self) -> int:
        return len(self.page.query_selector_all(self.CART_ITEMS))

    def get_item_names(self) -> list:
        elements = self.page.query_selector_all(self.CART_ITEM_NAME)
        return [el.text_content() for el in elements]

    def get_cart_total(self) -> float:
        text = self.page.text_content(self.CART_TOTAL).strip()
        return float(text.replace("$", "").replace(",", ""))

    def update_item_quantity(self, index: int, qty: int):
        items = self.page.query_selector_all(self.CART_ITEM_QTY)
        if index < len(items):
            items[index].fill(str(qty))
            # BAD: Using keyboard event to trigger update, fragile
            items[index].press("Tab")
            time.sleep(2)

    def remove_item(self, index: int):
        items = self.page.query_selector_all(self.CART_ITEM_REMOVE)
        if index < len(items):
            items[index].click()
            time.sleep(2)  # BAD: hardcoded wait

    def apply_promo_code(self, code: str):
        self.page.fill(self.PROMO_CODE_INPUT, code)
        self.page.click(self.APPLY_PROMO_BTN)
        time.sleep(2)

    # BAD PRACTICE: Business logic validation in page object
    def apply_promo_and_verify_discount(self, code: str, expected_discount_pct: float):
        """Contains business logic and assertions."""
        original_total = self.get_cart_total()
        self.apply_promo_code(code)

        # BAD: Assertion in page object
        assert self.page.is_visible(self.PROMO_SUCCESS_MSG), \
            f"Promo code {code} was not accepted"

        new_total = self.get_cart_total()
        expected_total = original_total * (1 - expected_discount_pct / 100)
        # BAD: Floating point comparison without tolerance
        assert new_total == expected_total, \
            f"Expected total {expected_total}, got {new_total}"

    def proceed_to_checkout(self):
        self.page.click(self.CHECKOUT_BTN)
        time.sleep(3)
        # BAD: Page object instantiation and return
        from pages.checkout_page import CheckoutPage
        return CheckoutPage(self.page)

    def is_cart_empty(self) -> bool:
        return self.is_visible(self.EMPTY_CART_MSG)

    # BAD PRACTICE: Test scenario orchestration inside page object
    def complete_checkout_from_cart(self, promo_code: str = None):
        """Entire checkout flow in a single page object method - terrible practice."""
        if promo_code:
            self.apply_promo_code(promo_code)
            time.sleep(1)

        self.page.click(self.CHECKOUT_BTN)
        time.sleep(3)

        # BAD: Directly filling checkout page fields from cart page
        self.page.fill("#first-name", "John")
        self.page.fill("#last-name", "Doe")
        self.page.fill("#email", "john@test.com")
        self.page.fill("#address", "123 Main St")
        self.page.fill("#city", "New York")
        self.page.fill("#zip", "10001")
        self.page.select_option("#state", label="New York")
        self.page.select_option("#country", label="United States")

        # BAD: Filling payment info from cart page object
        self.page.fill("#card-number", "4111111111111111")
        self.page.fill("#card-expiry", "12/25")
        self.page.fill("#card-cvv", "123")

        self.page.click("#btn-place-order")
        time.sleep(5)

        return self.page.text_content(".order-number")

    def continue_shopping(self):
        self.page.click(self.CONTINUE_SHOPPING_BTN)
        time.sleep(2)
