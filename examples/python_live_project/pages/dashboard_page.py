"""
Dashboard / User Profile Page Object
BAD PRACTICE: This is a "God Page Object" - handles too many concerns
"""
import time
import os
import json
import requests
from playwright.sync_api import Page

from pages.base_page import BasePage
from config.settings import Config


class DashboardPage(BasePage):
    """User Dashboard - handles profile, orders, settings, etc. (BAD: God object)"""

    # Profile section
    USER_NAME_DISPLAY = ".user-profile .display-name"
    USER_EMAIL_DISPLAY = ".user-profile .email"
    USER_AVATAR = ".user-profile .avatar"
    EDIT_PROFILE_BTN = "button#edit-profile"
    PROFILE_FORM = "#profile-form"
    PROFILE_FIRST_NAME = "#profile-first-name"
    PROFILE_LAST_NAME = "#profile-last-name"
    PROFILE_PHONE = "#profile-phone"
    PROFILE_BIO = "#profile-bio"
    SAVE_PROFILE_BTN = "button#save-profile"

    # Order history
    ORDERS_TAB = "a[href='#orders']"
    ORDER_LIST = ".order-list"
    ORDER_ROWS = ".order-list .order-row"
    ORDER_STATUS = ".order-row .status"
    ORDER_DATE = ".order-row .date"
    ORDER_TOTAL_AMOUNT = ".order-row .total"

    # Address book
    ADDRESSES_TAB = "a[href='#addresses']"
    ADDRESS_LIST = ".address-list"
    ADDRESS_CARDS = ".address-card"
    ADD_ADDRESS_BTN = "button#add-address"
    DEFAULT_ADDRESS_BADGE = ".address-card .badge-default"

    # Settings
    SETTINGS_TAB = "a[href='#settings']"
    NOTIFICATION_TOGGLE = "#toggle-notifications"
    NEWSLETTER_TOGGLE = "#toggle-newsletter"
    DARK_MODE_TOGGLE = "#toggle-dark-mode"
    DELETE_ACCOUNT_BTN = "button#delete-account"
    CHANGE_PASSWORD_BTN = "button#change-password"

    # Wishlist
    WISHLIST_TAB = "a[href='#wishlist']"
    WISHLIST_ITEMS = ".wishlist-item"

    # Navigation
    LOGOUT_BTN = "button#logout"
    NAV_PRODUCTS = "a[href='/products']"
    NAV_CART = "a[href='/cart']"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.base_url}/dashboard"

    def goto(self):
        self.page.goto(self.url)
        time.sleep(3)

    def get_user_name(self) -> str:
        return self.page.text_content(self.USER_NAME_DISPLAY)

    def get_user_email(self) -> str:
        return self.page.text_content(self.USER_EMAIL_DISPLAY)

    # BAD PRACTICE: Profile, orders, addresses, settings, wishlist - all in one page object
    def update_profile(self, first_name: str = None, last_name: str = None,
                       phone: str = None, bio: str = None):
        self.page.click(self.EDIT_PROFILE_BTN)
        time.sleep(1)
        if first_name:
            self.page.fill(self.PROFILE_FIRST_NAME, first_name)
        if last_name:
            self.page.fill(self.PROFILE_LAST_NAME, last_name)
        if phone:
            self.page.fill(self.PROFILE_PHONE, phone)
        if bio:
            self.page.fill(self.PROFILE_BIO, bio)
        self.page.click(self.SAVE_PROFILE_BTN)
        time.sleep(2)

    def go_to_orders(self):
        self.page.click(self.ORDERS_TAB)
        time.sleep(1)

    def get_order_count(self) -> int:
        self.go_to_orders()
        return len(self.page.query_selector_all(self.ORDER_ROWS))

    def get_order_statuses(self) -> list:
        self.go_to_orders()
        elements = self.page.query_selector_all(self.ORDER_STATUS)
        return [el.text_content() for el in elements]

    def go_to_addresses(self):
        self.page.click(self.ADDRESSES_TAB)
        time.sleep(1)

    def get_address_count(self) -> int:
        self.go_to_addresses()
        return len(self.page.query_selector_all(self.ADDRESS_CARDS))

    def go_to_settings(self):
        self.page.click(self.SETTINGS_TAB)
        time.sleep(1)

    def toggle_notifications(self, enable: bool):
        self.go_to_settings()
        # BAD PRACTICE: Direct JS execution to set toggle state
        self.page.evaluate(f"""
            document.querySelector('{self.NOTIFICATION_TOGGLE}').checked = {str(enable).lower()};
            document.querySelector('{self.NOTIFICATION_TOGGLE}').dispatchEvent(new Event('change'));
        """)
        time.sleep(1)

    def go_to_wishlist(self):
        self.page.click(self.WISHLIST_TAB)
        time.sleep(1)

    def get_wishlist_count(self) -> int:
        self.go_to_wishlist()
        return len(self.page.query_selector_all(self.WISHLIST_ITEMS))

    def logout(self):
        self.page.click(self.LOGOUT_BTN)
        time.sleep(2)

    # BAD PRACTICE: API interactions embedded in page object
    def get_user_orders_from_api(self, user_id: str) -> list:
        config = Config()
        response = requests.get(
            f"{config.API_BASE_URL}/users/{user_id}/orders",
            headers={"Authorization": f"Bearer {config.API_KEY}"}
        )
        return response.json().get("orders", [])

    # BAD PRACTICE: File system operations in page object
    def download_order_invoice(self, order_id: str):
        self.go_to_orders()
        self.page.click(f".order-row[data-id='{order_id}'] .download-invoice")
        time.sleep(3)
        # BAD: checking filesystem from page object
        download_path = os.path.expanduser("~/Downloads")
        invoice_file = os.path.join(download_path, f"invoice_{order_id}.pdf")
        assert os.path.exists(invoice_file), f"Invoice not downloaded: {invoice_file}"
        return invoice_file

    # BAD PRACTICE: Complex multi-step flow in single method
    def change_password_flow(self, current_pwd: str, new_pwd: str, confirm_pwd: str):
        """Complete password change - crosses page boundaries."""
        self.go_to_settings()
        self.page.click(self.CHANGE_PASSWORD_BTN)
        time.sleep(1)

        # BAD: Interacting with modal/dialog selectors from main page
        self.page.fill("#current-password", current_pwd)
        self.page.fill("#new-password", new_pwd)
        self.page.fill("#confirm-password", confirm_pwd)
        self.page.click("#btn-save-password")
        time.sleep(2)

        # BAD: assertion
        assert self.page.is_visible(".toast-success"), "Password change did not succeed"

    # BAD PRACTICE: Data transformation in page object
    def get_order_history_summary(self) -> dict:
        """Business logic / data transformation in page object."""
        self.go_to_orders()
        statuses = self.get_order_statuses()
        return {
            "total_orders": len(statuses),
            "delivered": statuses.count("Delivered"),
            "pending": statuses.count("Pending"),
            "cancelled": statuses.count("Cancelled"),
            "delivery_rate": statuses.count("Delivered") / len(statuses) if statuses else 0
        }
