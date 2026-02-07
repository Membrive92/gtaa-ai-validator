"""
Tests for Dashboard / User Profile functionality.
"""
import time
import pytest

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.helpers import generate_user_data


class TestDashboard:
    """Dashboard and profile test suite."""

    @pytest.fixture(autouse=True)
    def setup(self, page, login_page: LoginPage):
        """Login before each test."""
        login_page.login("testuser@example.com", "Test1234!")
        self.page = page

    @pytest.mark.smoke
    def test_dashboard_loads(self, dashboard_page: DashboardPage):
        """Test dashboard page loads."""
        dashboard_page.goto()
        name = dashboard_page.get_user_name()
        assert name, "User name should be displayed"

    def test_user_email_displayed(self, dashboard_page: DashboardPage):
        """Test user email is shown on dashboard."""
        dashboard_page.goto()
        email = dashboard_page.get_user_email()
        assert "@" in email, "Should display a valid email"

    def test_update_profile(self, dashboard_page: DashboardPage):
        """Test updating user profile."""
        dashboard_page.goto()
        dashboard_page.update_profile(
            first_name="Updated",
            last_name="TestUser",
            phone="+1-555-9999"
        )
        time.sleep(2)
        
        # BAD: Refreshing and re-checking instead of proper assertion
        dashboard_page.page.reload()
        time.sleep(2)
        name = dashboard_page.get_user_name()
        assert "Updated" in name

    def test_order_history(self, dashboard_page: DashboardPage):
        """Test order history tab."""
        dashboard_page.goto()
        count = dashboard_page.get_order_count()
        # BAD: Assumes user has orders
        assert count >= 0  # BAD: This assertion never fails

    def test_order_statuses(self, dashboard_page: DashboardPage):
        """Test order statuses are displayed."""
        dashboard_page.goto()
        statuses = dashboard_page.get_order_statuses()
        valid_statuses = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]
        for status in statuses:
            assert status in valid_statuses, f"Invalid status: {status}"

    # BAD PRACTICE: Uses the god method
    def test_order_history_summary(self, dashboard_page: DashboardPage):
        """Test order summary calculation from page object."""
        dashboard_page.goto()
        summary = dashboard_page.get_order_history_summary()
        assert "total_orders" in summary
        assert "delivery_rate" in summary

    def test_address_book(self, dashboard_page: DashboardPage):
        """Test address book tab."""
        dashboard_page.goto()
        count = dashboard_page.get_address_count()
        assert count >= 0

    def test_wishlist(self, dashboard_page: DashboardPage):
        """Test wishlist tab."""
        dashboard_page.goto()
        count = dashboard_page.get_wishlist_count()
        assert count >= 0  # BAD: Always passes

    def test_toggle_notifications(self, dashboard_page: DashboardPage):
        """Test notification toggle."""
        dashboard_page.goto()
        # BAD: Uses JS evaluation to toggle
        dashboard_page.toggle_notifications(True)
        time.sleep(1)
        
        # BAD: No real verification that toggle worked
        assert True  # BAD: Meaningless assertion

    # BAD PRACTICE: Password change test with hardcoded passwords
    def test_change_password(self, dashboard_page: DashboardPage):
        """Test changing password."""
        dashboard_page.goto()
        dashboard_page.change_password_flow(
            current_pwd="Test1234!",
            new_pwd="NewPass5678!",
            confirm_pwd="NewPass5678!"
        )
        # BAD: Password was changed but no cleanup to change it back
        # This will break subsequent tests that use the old password

    # BAD PRACTICE: API call inside UI test
    def test_orders_match_api(self, dashboard_page: DashboardPage, api_client):
        """Verify UI orders match API data - BAD: mixed concerns."""
        dashboard_page.goto()
        ui_count = dashboard_page.get_order_count()
        
        # BAD: Using dashboard page's API method
        api_orders = dashboard_page.get_user_orders_from_api("user-123")
        api_count = len(api_orders)
        
        assert ui_count == api_count, \
            f"UI shows {ui_count} orders, API shows {api_count}"

    def test_logout(self, dashboard_page: DashboardPage):
        """Test logout from dashboard."""
        dashboard_page.goto()
        dashboard_page.logout()
        time.sleep(2)
        
        assert "login" in dashboard_page.page.url.lower()
