"""
Base Page Object - Foundation for all page objects.
"""
import time
import logging
from playwright.sync_api import Page, expect

from config.settings import Config

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page):
        self.page = page
        self.config = Config()  # BAD PRACTICE: Direct instantiation instead of injection
        self.base_url = self.config.BASE_URL
        self.timeout = self.config.TIMEOUT

    def navigate(self, path: str = ""):
        """Navigate to a specific path."""
        url = f"{self.base_url}/{path}"
        self.page.goto(url)
        # BAD PRACTICE: Hardcoded sleep instead of proper wait
        time.sleep(3)

    def get_title(self):
        return self.page.title()

    def get_current_url(self):
        return self.page.url

    def click(self, selector: str):
        """Generic click method."""
        self.page.click(selector)

    def fill(self, selector: str, text: str):
        """Generic fill method."""
        self.page.fill(selector, text)

    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self.page.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        try:
            return self.page.is_visible(selector)
        except Exception:
            return False

    def wait_for_element(self, selector: str, timeout: int = None):
        """Wait for element to be visible."""
        timeout = timeout or self.timeout
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)

    def take_screenshot(self, name: str = "screenshot"):
        """Take a screenshot."""
        self.page.screenshot(path=f"reports/screenshots/{name}.png")

    # BAD PRACTICE: Business logic in base page
    def login(self, username: str, password: str):
        """Login method that shouldn't be in BasePage."""
        self.navigate("login")
        self.fill("#email", username)
        self.fill("#password", password)
        self.click("button[type='submit']")
        time.sleep(2)

    # BAD PRACTICE: Database interaction in page object
    def get_user_from_db(self, user_id: str):
        """This should NOT be in a page object."""
        import sqlite3
        conn = sqlite3.connect(self.config.DB_HOST)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")  # SQL injection risk
        return cursor.fetchone()

    # BAD PRACTICE: API call inside a page object
    def get_product_via_api(self, product_id: str):
        """API calls should not be in page objects."""
        import requests
        response = requests.get(
            f"{self.config.API_BASE_URL}/products/{product_id}",
            headers={"Authorization": f"Bearer {self.config.API_KEY}"}
        )
        return response.json()

    def scroll_to_bottom(self):
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

    def accept_cookies(self):
        """Accept cookie banner if present."""
        try:
            self.page.click("#accept-cookies", timeout=3000)
        except Exception:
            pass  # BAD PRACTICE: Silent exception swallowing
