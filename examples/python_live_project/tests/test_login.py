"""
Tests for Login functionality.
BAD PRACTICES: Mixed concerns, hardcoded data, poor isolation.
"""
import time
import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from config.settings import Config
from utils.helpers import generate_random_email, take_screenshot


class TestLogin:
    """Login test suite."""

    # BAD PRACTICE: Test data hardcoded in test class
    VALID_EMAIL = "testuser@example.com"
    VALID_PASSWORD = "Test1234!"
    ADMIN_EMAIL = "admin@testapp.io"
    ADMIN_PASSWORD = "Admin123!@#"

    @pytest.mark.smoke
    def test_successful_login(self, login_page: LoginPage):
        """Test valid user can login successfully."""
        login_page.login(self.VALID_EMAIL, self.VALID_PASSWORD)

        # BAD: Assertion relies on URL which may vary
        assert "dashboard" in login_page.page.url or "home" in login_page.page.url

    @pytest.mark.smoke
    def test_admin_login(self, login_page: LoginPage):
        """Test admin login."""
        login_page.login_as_admin()
        # BAD: Duplicate URL assertion pattern
        assert "dashboard" in login_page.page.url

    def test_invalid_email_login(self, login_page: LoginPage):
        """Test login with invalid email."""
        login_page.login("invalid@email.com", "wrongpassword")
        error = login_page.get_error_message()
        assert error != "", "Expected error message but got none"
        # BAD: Fragile text assertion
        assert "invalid" in error.lower() or "incorrect" in error.lower()

    def test_empty_email_login(self, login_page: LoginPage):
        """Test login with empty email."""
        login_page.goto()
        login_page.enter_password(self.VALID_PASSWORD)
        login_page.click_login()
        time.sleep(1)  # BAD: hardcoded sleep
        # BAD: No proper assertion, just checking visibility
        assert login_page.page.is_visible(".field-error") or \
               login_page.page.is_visible(".error-message")

    def test_empty_password_login(self, login_page: LoginPage):
        """Test login with empty password."""
        login_page.goto()
        login_page.enter_email(self.VALID_EMAIL)
        login_page.click_login()
        time.sleep(1)
        assert login_page.page.is_visible(".field-error") or \
               login_page.page.is_visible(".error-message")

    # BAD PRACTICE: Test depends on previous test state
    def test_login_remember_me(self, login_page: LoginPage):
        """Test remember me functionality."""
        login_page.login(self.VALID_EMAIL, self.VALID_PASSWORD, remember_me=True)
        assert "dashboard" in login_page.page.url

        # BAD: Checking cookies directly in test
        cookies = login_page.page.context.cookies()
        remember_cookie = [c for c in cookies if c["name"] == "remember_token"]
        assert len(remember_cookie) > 0, "Remember me cookie not set"

    # BAD PRACTICE: Test that does too many things (not focused)
    def test_login_and_navigate_to_products(self, login_page: LoginPage):
        """Test login then navigation - should be separate tests."""
        login_page.login(self.VALID_EMAIL, self.VALID_PASSWORD)
        assert "dashboard" in login_page.page.url

        # BAD: Test continues into a different feature area
        login_page.page.click("a[href='/products']")
        time.sleep(2)
        assert "products" in login_page.page.url
        
        # BAD: Checking product count from login test
        from pages.products_page import ProductsPage
        products = ProductsPage(login_page.page)
        count = products.get_product_count()
        assert count > 0, "No products found after login"

    # BAD PRACTICE: Using page object's bad method
    def test_login_and_go_to_products_shortcut(self, login_page: LoginPage):
        """Uses LoginPage method that crosses page boundaries."""
        products_page = login_page.login_and_go_to_products(
            self.VALID_EMAIL, self.VALID_PASSWORD
        )
        assert products_page.get_product_count() > 0

    @pytest.mark.parametrize("email,password,expected_error", [
        ("", "Test1234!", "email is required"),
        ("testuser@example.com", "", "password is required"),
        ("not-an-email", "Test1234!", "valid email"),
        ("test@test.com", "short", "password must be"),
    ])
    def test_login_validation(self, login_page: LoginPage, email, password, expected_error):
        """Parameterized login validation tests."""
        login_page.goto()
        if email:
            login_page.enter_email(email)
        if password:
            login_page.enter_password(password)
        login_page.click_login()
        time.sleep(1)

        error = login_page.get_error_message()
        # BAD: Loose text matching that may not catch real issues
        assert expected_error.lower() in error.lower() or error != ""

    # BAD PRACTICE: Flaky test with retries built in
    @pytest.mark.flaky
    def test_social_login_google(self, login_page: LoginPage):
        """Test Google social login - inherently flaky."""
        for attempt in range(3):
            try:
                login_page.social_login_google()
                time.sleep(5)  # BAD: Long arbitrary wait
                if "accounts.google.com" in login_page.page.url or \
                   "dashboard" in login_page.page.url:
                    break
            except Exception:
                if attempt == 2:
                    pytest.skip("Google login popup not available in test env")
                time.sleep(2)

    # BAD PRACTICE: Test with API call mixed in
    def test_login_creates_session_in_backend(self, login_page: LoginPage, api_client):
        """Mixes UI and API verification poorly."""
        login_page.login(self.VALID_EMAIL, self.VALID_PASSWORD)
        
        # BAD: Extracting token from browser and using in API
        cookies = login_page.page.context.cookies()
        session_cookie = next((c for c in cookies if c["name"] == "session_id"), None)
        
        if session_cookie:
            # BAD: API call in a UI test
            import requests
            resp = requests.get(
                f"{Config().API_BASE_URL}/auth/session/{session_cookie['value']}",
                headers={"Authorization": f"Bearer {Config().API_KEY}"}
            )
            assert resp.status_code == 200

    def test_logout(self, login_page: LoginPage):
        """Test logout functionality."""
        login_page.login(self.VALID_EMAIL, self.VALID_PASSWORD)
        
        # BAD: Using DashboardPage from login test
        dashboard = DashboardPage(login_page.page)
        dashboard.logout()
        time.sleep(2)
        
        assert "login" in login_page.page.url.lower()
