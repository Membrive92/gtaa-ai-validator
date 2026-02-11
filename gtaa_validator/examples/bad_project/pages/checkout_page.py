"""
Bad Page Object with multiple gTAA violations.

Violations present:
- FORBIDDEN_IMPORT: imports pytest (line 14)
- ASSERTION_IN_POM: assert inside method (line 28)
- BUSINESS_LOGIC_IN_POM: if/else inside method (line 35)
- BUSINESS_LOGIC_IN_POM: for loop inside method (line 47)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest  # VIOLATION: FORBIDDEN_IMPORT


class CheckoutPage:
    """Page Object that violates several gTAA rules."""

    def __init__(self, driver):
        self.driver = driver
        self.submit_btn = (By.CSS_SELECTOR, "#submit-btn")
        self.total_label = (By.ID, "total-price")

    def validate_total(self, expected):
        """Contains assertion — VIOLATION: ASSERTION_IN_POM."""
        actual = self.driver.find_element(*self.total_label).text
        assert actual == expected  # VIOLATION

    def apply_discount(self, code):
        """Contains if/else — VIOLATION: BUSINESS_LOGIC_IN_POM."""
        discount_field = self.driver.find_element(By.ID, "discount")
        if code.startswith("SAVE"):  # VIOLATION
            discount_field.send_keys(code)
            self.driver.find_element(*self.submit_btn).click()
        else:
            print("Invalid code")

    def get_filtered_products(self, category):
        """Contains for loop — VIOLATION: BUSINESS_LOGIC_IN_POM."""
        elements = self.driver.find_elements(By.CLASS_NAME, "product")
        result = []
        for el in elements:  # VIOLATION
            if el.get_attribute("data-cat") == category:  # VIOLATION (nested if)
                result.append(el.text)
        return result
