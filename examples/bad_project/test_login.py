"""
Test file with ADAPTATION_IN_DEFINITION violations.

This file demonstrates BAD practices - test code directly calling Selenium API.
According to gTAA, tests should call Page Objects, not driver directly.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_login_with_valid_credentials():
    """
    Test login with valid credentials.

    VIOLATION: This test directly uses Selenium API instead of Page Objects!
    """
    driver = webdriver.Chrome()

    # VIOLATION: Direct Selenium calls in test code
    driver.get("https://example.com/login")
    driver.find_element(By.ID, "username").send_keys("testuser")
    driver.find_element(By.ID, "password").send_keys("password123")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Wait for dashboard
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dashboard"))
    )

    # VIOLATION: More direct Selenium calls
    welcome_message = driver.find_element(By.CLASS_NAME, "welcome").text
    assert "Welcome" in welcome_message

    driver.quit()


def test_login_with_invalid_credentials():
    """Test login with invalid credentials - also has violations."""
    driver = webdriver.Chrome()

    # VIOLATION: Direct Selenium usage
    driver.get("https://example.com/login")
    driver.find_element(By.ID, "username").send_keys("wrong")
    driver.find_element(By.ID, "password").send_keys("wrong")
    driver.find_element(By.CSS_SELECTOR, "button.submit-btn").click()

    # VIOLATION: Direct element access
    error_msg = driver.find_element(By.CLASS_NAME, "error-message").text
    assert "Invalid credentials" in error_msg

    driver.quit()
