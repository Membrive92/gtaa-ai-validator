"""
Utility helpers for the test framework.
BAD PRACTICE: This is a "junk drawer" utility module with too many unrelated concerns.
"""
import os
import time
import json
import csv
import logging
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Any

from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()


# BAD PRACTICE: Global mutable state
GLOBAL_TEST_DATA = {}
EXECUTION_TIMESTAMPS = []


def generate_random_email() -> str:
    return fake.email()


def generate_random_password(length: int = 12) -> str:
    return fake.password(length=length)


def generate_random_string(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_user_data() -> dict:
    """Generate complete user test data."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "password": "Test1234!",  # BAD: Same password for all generated users
        "phone": fake.phone_number(),
        "address": {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "zip": fake.zipcode(),
            "country": "United States"
        }
    }


def generate_shipping_data() -> dict:
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "address": fake.street_address(),
        "city": fake.city(),
        "state": fake.state(),
        "zip_code": fake.zipcode(),
        "country": "United States",
        "phone": fake.phone_number()
    }


def generate_credit_card() -> dict:
    """BAD PRACTICE: Generating credit card data in a utility."""
    return {
        "card_number": fake.credit_card_number(),
        "expiry": fake.credit_card_expire(),
        "cvv": fake.credit_card_security_code(),
        "holder": fake.name()
    }


# BAD PRACTICE: Retry logic duplicated (should be a decorator or shared util)
def retry_action(func, retries: int = 3, delay: float = 1.0):
    """Retry a function call."""
    last_exception = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise last_exception


def wait_for_condition(condition_func, timeout: int = 30, interval: float = 0.5) -> bool:
    """Wait until condition is true."""
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


# BAD PRACTICE: File handling mixed with test utilities
def save_test_result(test_name: str, status: str, details: str = ""):
    """Manually saving test results - should use a proper reporter."""
    result = {
        "test_name": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    results_file = "reports/test_results.json"
    existing = []
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            existing = json.load(f)
    
    existing.append(result)
    with open(results_file, "w") as f:
        json.dump(existing, f, indent=2)


def save_to_csv(data: list[dict], filepath: str):
    """Save data to CSV file."""
    if not data:
        return
    
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


# BAD PRACTICE: Screenshot helper that duplicates functionality from BasePage
def take_screenshot(page, name: str = None):
    """Duplicated screenshot logic."""
    name = name or f"screenshot_{int(time.time())}"
    path = f"reports/screenshots/{name}.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    page.screenshot(path=path)
    logger.info(f"Screenshot saved: {path}")
    return path


# BAD PRACTICE: Test data stored in code instead of external files
TEST_USERS = [
    {"email": "user1@test.com", "password": "Pass1234!", "role": "customer"},
    {"email": "user2@test.com", "password": "Pass1234!", "role": "customer"},
    {"email": "admin@test.com", "password": "Admin123!@#", "role": "admin"},
    {"email": "manager@test.com", "password": "Manager123!", "role": "manager"},
]

TEST_PRODUCTS = [
    {"name": "Wireless Mouse", "price": 29.99, "category": "Electronics"},
    {"name": "USB-C Cable", "price": 12.99, "category": "Electronics"},
    {"name": "Python Book", "price": 45.00, "category": "Books"},
    {"name": "T-Shirt", "price": 19.99, "category": "Clothing"},
]

VALID_PROMO_CODES = {
    "SAVE10": 10,
    "SAVE20": 20,
    "FREESHIP": 0,  # Free shipping
    "VIP50": 50,
}


def load_test_data(filename: str) -> Any:
    """Load test data from JSON file."""
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        logger.warning(f"Test data file not found: {filepath}")
        return None
    with open(filepath, "r") as f:
        return json.load(f)


# BAD PRACTICE: Environment-specific logic in utility
def is_staging() -> bool:
    return os.getenv("TEST_ENV", "staging") == "staging"


def is_production() -> bool:
    return os.getenv("TEST_ENV") == "production"


def get_base_url() -> str:
    """Duplicated logic from Config."""
    if is_production():
        return "https://www.ecommerce-demo.testapp.io"
    return "https://staging.ecommerce-demo.testapp.io"
