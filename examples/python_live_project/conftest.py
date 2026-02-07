"""
Pytest fixtures for the test automation framework.
"""
import os
import time
import pytest
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser

from config.settings import Config, get_config
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.dashboard_page import DashboardPage
from api.client import APIClient
from utils.reporter import ReportGenerator
from utils.helpers import generate_user_data, take_screenshot

logger = logging.getLogger(__name__)


# BAD PRACTICE: Global variables for state sharing between fixtures
_browser_instance = None
_api_client_instance = None


@pytest.fixture(scope="session")
def config():
    """Provide test configuration."""
    return get_config()


# BAD PRACTICE: Browser fixture with too much responsibility
@pytest.fixture(scope="session")
def browser(config):
    """Create browser instance for the entire session."""
    global _browser_instance
    
    with sync_playwright() as p:
        browser_type = getattr(p, config.BROWSER)
        _browser_instance = browser_type.launch(
            headless=config.HEADLESS,
            slow_mo=config.SLOW_MO,
            # BAD PRACTICE: Disabling security features for convenience
            args=[
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
            ]
        )
        yield _browser_instance
        _browser_instance.close()
        _browser_instance = None


@pytest.fixture(scope="function")
def page(browser, config) -> Page:
    """Create a new page for each test."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,  # BAD: Ignoring SSL errors
        # BAD PRACTICE: Hardcoded locale and timezone
        locale="en-US",
        timezone_id="America/New_York",
    )
    page = context.new_page()
    page.set_default_timeout(config.TIMEOUT)
    
    yield page
    
    # BAD PRACTICE: No proper cleanup, screenshot on failure not handled here
    context.close()


# BAD PRACTICE: Page object fixtures create tight coupling
@pytest.fixture
def login_page(page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def products_page(page) -> ProductsPage:
    return ProductsPage(page)


@pytest.fixture
def cart_page(page) -> CartPage:
    return CartPage(page)


@pytest.fixture
def checkout_page(page) -> CheckoutPage:
    return CheckoutPage(page)


@pytest.fixture
def dashboard_page(page) -> DashboardPage:
    return DashboardPage(page)


# BAD PRACTICE: "logged_in" fixture that does too much
@pytest.fixture
def logged_in_page(page, config) -> Page:
    """Return a page that's already logged in."""
    login = LoginPage(page)
    login.login(config.ADMIN_USERNAME, config.ADMIN_PASSWORD)
    time.sleep(2)
    return page


@pytest.fixture(scope="session")
def api_client(config) -> APIClient:
    """Provide API client instance."""
    global _api_client_instance
    _api_client_instance = APIClient(
        base_url=config.API_BASE_URL,
        api_key=config.API_KEY
    )
    return _api_client_instance


# BAD PRACTICE: Fixture that creates data but doesn't clean up
@pytest.fixture
def test_user(api_client) -> dict:
    """Create a test user via API."""
    user_data = generate_user_data()
    created_user = api_client.create_user(
        email=user_data["email"],
        password=user_data["password"],
        name=f"{user_data['first_name']} {user_data['last_name']}"
    )
    # BAD: No teardown/cleanup to delete the user after test
    return {**created_user, "password": user_data["password"]}


# BAD PRACTICE: Fixture with hardcoded test product
@pytest.fixture
def test_product(api_client) -> dict:
    """Create a test product."""
    product = api_client.create_product({
        "name": "Automated Test Product",
        "description": "This product was created by automated tests",
        "price": 99.99,
        "category": "Electronics",
        "stock": 100,
        "sku": "AUTO-TEST-001"
    })
    return product


@pytest.fixture(scope="session")
def report_generator():
    """Provide report generator - BAD: Custom reporter instead of using allure/pytest-html."""
    reporter = ReportGenerator()
    reporter.start_suite()
    yield reporter
    reporter.end_suite()
    reporter.generate_html_report()
    reporter.generate_json_report()


# BAD PRACTICE: Hook that catches all exceptions and takes screenshots
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on failure."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # BAD: Accessing global browser instance
        if _browser_instance and _browser_instance.contexts:
            try:
                page = _browser_instance.contexts[0].pages[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"reports/screenshots/failure_{item.name}_{timestamp}.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                page.screenshot(path=screenshot_path)
                logger.info(f"Failure screenshot: {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {e}")
