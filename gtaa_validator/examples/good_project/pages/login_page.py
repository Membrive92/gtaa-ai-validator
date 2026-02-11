"""
Login Page Object - Adaptation Layer.

This is the CORRECT way to structure test automation according to gTAA.
Page Objects encapsulate all Selenium/Playwright interactions.
Tests should call these methods, not driver directly.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:
    """
    Page Object for the Login page.

    Encapsulates all interactions with the login page.
    This is the Adaptation layer in gTAA architecture.
    """

    def __init__(self, driver: webdriver.Chrome):
        """Initialize with driver instance."""
        self.driver = driver
        self.url = "https://example.com/login"

        # Locators (centralized)
        self.username_input = (By.ID, "username")
        self.password_input = (By.ID, "password")
        self.submit_button = (By.XPATH, "//button[@type='submit']")
        self.welcome_message = (By.CLASS_NAME, "welcome")
        self.error_message = (By.CLASS_NAME, "error-message")

    def navigate(self):
        """Navigate to login page."""
        self.driver.get(self.url)

    def enter_username(self, username: str):
        """Enter username."""
        self.driver.find_element(*self.username_input).send_keys(username)

    def enter_password(self, password: str):
        """Enter password."""
        self.driver.find_element(*self.password_input).send_keys(password)

    def click_submit(self):
        """Click submit button."""
        self.driver.find_element(*self.submit_button).click()

    def login(self, username: str, password: str):
        """
        Complete login flow - high-level method.

        This is good practice: provide both atomic methods (enter_username)
        and composite methods (login) for convenience.
        """
        self.enter_username(username)
        self.enter_password(password)
        self.click_submit()

    def get_welcome_message(self) -> str:
        """Get welcome message text after successful login."""
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboard"))
        )
        return self.driver.find_element(*self.welcome_message).text

    def get_error_message(self) -> str:
        """Get error message text after failed login."""
        return self.driver.find_element(*self.error_message).text
