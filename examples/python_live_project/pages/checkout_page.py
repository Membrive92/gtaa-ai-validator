"""
Checkout Page Object
"""
import time
from playwright.sync_api import Page

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """Page object for Checkout page."""

    # Shipping form
    FIRST_NAME = "#first-name"
    LAST_NAME = "#last-name"
    EMAIL = "#email"
    PHONE = "#phone"
    ADDRESS_LINE1 = "#address"
    ADDRESS_LINE2 = "#address-2"
    CITY = "#city"
    STATE = "#state"
    ZIP_CODE = "#zip"
    COUNTRY = "#country"

    # Payment form
    CARD_NUMBER = "#card-number"
    CARD_EXPIRY = "#card-expiry"
    CARD_CVV = "#card-cvv"
    CARD_HOLDER = "#card-holder-name"

    # Actions
    PLACE_ORDER_BTN = "#btn-place-order"
    BACK_TO_CART_BTN = "a.back-to-cart"

    # Order summary
    ORDER_SUMMARY = ".order-summary"
    ORDER_TOTAL = ".order-summary .total"
    ORDER_ITEMS = ".order-summary .item"

    # Confirmation
    ORDER_CONFIRMATION = ".order-confirmation"
    ORDER_NUMBER = ".order-number"
    CONFIRMATION_EMAIL_MSG = ".confirmation-email-message"

    # Errors
    FIELD_ERROR = ".field-error"
    PAYMENT_ERROR = ".payment-error"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.base_url}/checkout"

    def goto(self):
        self.page.goto(self.url)
        time.sleep(2)

    def fill_shipping_info(
        self, first_name: str, last_name: str, email: str,
        address: str, city: str, state: str, zip_code: str,
        country: str = "United States", phone: str = ""
    ):
        self.page.fill(self.FIRST_NAME, first_name)
        self.page.fill(self.LAST_NAME, last_name)
        self.page.fill(self.EMAIL, email)
        if phone:
            self.page.fill(self.PHONE, phone)
        self.page.fill(self.ADDRESS_LINE1, address)
        self.page.fill(self.CITY, city)
        self.page.select_option(self.STATE, label=state)
        self.page.fill(self.ZIP_CODE, zip_code)
        self.page.select_option(self.COUNTRY, label=country)

    # BAD PRACTICE: Hardcoded payment info in page object
    def fill_payment_info(
        self,
        card_number: str = "4111111111111111",
        expiry: str = "12/26",
        cvv: str = "123",
        holder: str = "Test User"
    ):
        self.page.fill(self.CARD_NUMBER, card_number)
        self.page.fill(self.CARD_EXPIRY, expiry)
        self.page.fill(self.CARD_CVV, cvv)
        self.page.fill(self.CARD_HOLDER, holder)

    def place_order(self):
        self.page.click(self.PLACE_ORDER_BTN)
        time.sleep(5)  # BAD: long hardcoded wait

    def get_order_number(self) -> str:
        self.page.wait_for_selector(self.ORDER_NUMBER, timeout=15000)
        return self.page.text_content(self.ORDER_NUMBER).strip()

    def get_order_total(self) -> float:
        text = self.page.text_content(self.ORDER_TOTAL).strip()
        return float(text.replace("$", "").replace(",", ""))

    # BAD PRACTICE: Giant "do everything" method
    def complete_checkout(self, shipping_data: dict, payment_data: dict = None):
        """Complete entire checkout - too much responsibility."""
        self.fill_shipping_info(**shipping_data)
        time.sleep(1)

        if payment_data:
            self.fill_payment_info(**payment_data)
        else:
            self.fill_payment_info()  # BAD: Uses hardcoded defaults

        self.place_order()

        # BAD: Assertions in page object
        assert self.page.is_visible(self.ORDER_CONFIRMATION), \
            "Order confirmation not displayed"

        order_number = self.get_order_number()
        assert order_number, "Order number is empty"

        # BAD: API verification mixed with page object
        self._verify_order_in_backend(order_number)

        return order_number

    # BAD PRACTICE: API call from page object
    def _verify_order_in_backend(self, order_number: str):
        """Verifying order via API from within a page object."""
        import requests
        from config.settings import Config
        config = Config()
        resp = requests.get(
            f"{config.API_BASE_URL}/orders/{order_number}",
            headers={"Authorization": f"Bearer {config.API_KEY}"}
        )
        assert resp.status_code == 200, f"Order {order_number} not found in backend"

    def get_field_errors(self) -> list:
        elements = self.page.query_selector_all(self.FIELD_ERROR)
        return [el.text_content() for el in elements]

    def get_payment_error(self) -> str:
        if self.is_visible(self.PAYMENT_ERROR):
            return self.get_text(self.PAYMENT_ERROR)
        return ""

    def back_to_cart(self):
        self.page.click(self.BACK_TO_CART_BTN)
        time.sleep(2)
        from pages.cart_page import CartPage
        return CartPage(self.page)
