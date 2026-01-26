"""
Login tests - Definition Layer.

This demonstrates CORRECT gTAA architecture:
- Tests only call Page Object methods
- No direct Selenium/Playwright calls in test code
- Clean, readable, maintainable tests
"""

from selenium import webdriver
from pages.login_page import LoginPage


def test_login_with_valid_credentials():
    """
    Test login with valid credentials.

    NO VIOLATIONS: Test uses Page Object methods only.
    """
    driver = webdriver.Chrome()

    # Use Page Object for all interactions
    login_page = LoginPage(driver)
    login_page.navigate()
    login_page.login("testuser", "password123")

    # Get data via Page Object method
    welcome_msg = login_page.get_welcome_message()
    assert "Welcome" in welcome_msg

    driver.quit()


def test_login_with_invalid_credentials():
    """Test login with invalid credentials - also uses Page Object."""
    driver = webdriver.Chrome()

    # All interactions through Page Object
    login_page = LoginPage(driver)
    login_page.navigate()
    login_page.login("wrong", "wrong")

    # Verify error via Page Object
    error_msg = login_page.get_error_message()
    assert "Invalid credentials" in error_msg

    driver.quit()


def test_empty_credentials():
    """Test with empty credentials."""
    driver = webdriver.Chrome()

    login_page = LoginPage(driver)
    login_page.navigate()
    login_page.click_submit()  # Submit without entering credentials

    error_msg = login_page.get_error_message()
    assert "required" in error_msg.lower()

    driver.quit()
