"""
Login Page Object
"""
import time
from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from config.settings import Config


class LoginPage(BasePage):
    """Page object for the Login page."""

    # BAD PRACTICE: Mixing locator strategies inconsistently
    EMAIL_INPUT = "#email"
    PASSWORD_INPUT = "input[name='password']"
    LOGIN_BUTTON = "button[type='submit']"
    REMEMBER_ME = "//label[contains(text(), 'Remember me')]"  # XPath mixed with CSS
    FORGOT_PASSWORD_LINK = "text=Forgot your password?"
    ERROR_MESSAGE = ".error-message"
    GOOGLE_LOGIN_BTN = "#btn-google-login"
    FACEBOOK_LOGIN_BTN = "div.social-login > button:nth-child(2)"  # BAD: brittle positional selector

    # BAD PRACTICE: Hardcoded test data in page object
    DEFAULT_EMAIL = "testuser@example.com"
    DEFAULT_PASSWORD = "Test1234!"
    ADMIN_EMAIL = "admin@testapp.io"
    ADMIN_PASSWORD = "Admin123!@#"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.base_url}/login"

    def goto(self):
        self.page.goto(self.url)
        time.sleep(2)  # BAD PRACTICE: Hardcoded wait
        self.accept_cookies()

    def enter_email(self, email: str):
        self.page.fill(self.EMAIL_INPUT, email)

    def enter_password(self, password: str):
        self.page.fill(self.PASSWORD_INPUT, password)

    def click_login(self):
        self.page.click(self.LOGIN_BUTTON)

    def click_remember_me(self):
        self.page.click(self.REMEMBER_ME)

    # BAD PRACTICE: Method does too many things (not single responsibility)
    def login(self, email: str = None, password: str = None, remember_me: bool = False):
        """Perform login - overrides base page login (BAD)."""
        email = email or self.DEFAULT_EMAIL
        password = password or self.DEFAULT_PASSWORD

        self.goto()
        self.enter_email(email)
        self.enter_password(password)

        if remember_me:
            self.click_remember_me()

        self.click_login()
        time.sleep(3)  # BAD: hardcoded wait

        # BAD PRACTICE: Assertions inside page object
        if self.is_visible(self.ERROR_MESSAGE):
            error_text = self.get_text(self.ERROR_MESSAGE)
            raise Exception(f"Login failed: {error_text}")

        # BAD PRACTICE: Verification logic in page object
        assert "dashboard" in self.page.url.lower() or "home" in self.page.url.lower(), \
            "Login did not redirect to expected page"

        return True

    def login_as_admin(self):
        """Login with admin credentials."""
        return self.login(self.ADMIN_EMAIL, self.ADMIN_PASSWORD)

    def get_error_message(self) -> str:
        if self.is_visible(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        return ""

    # BAD PRACTICE: Page object knows about multiple pages and navigates between them
    def login_and_go_to_products(self, email: str, password: str):
        """This method violates single responsibility - crosses page boundaries."""
        self.login(email, password)
        self.page.click("a[href='/products']")
        time.sleep(2)
        # BAD: Returns a different page object, creating tight coupling
        from pages.products_page import ProductsPage
        return ProductsPage(self.page)

    # BAD PRACTICE: Direct DOM manipulation / JS execution in page object
    def bypass_captcha(self):
        """Bypass captcha for testing - bad practice."""
        self.page.evaluate("""
            document.querySelector('#captcha-container').style.display = 'none';
            document.querySelector('#captcha-verified').value = 'true';
        """)

    # BAD PRACTICE: Test data generation in page object
    def generate_test_user(self):
        """Page objects should not generate test data."""
        from faker import Faker
        fake = Faker()
        return {
            "email": fake.email(),
            "password": fake.password(length=12),
            "name": fake.name()
        }

    def social_login_google(self):
        self.goto()
        self.page.click(self.GOOGLE_LOGIN_BTN)
        time.sleep(5)  # BAD: arbitrary long wait
