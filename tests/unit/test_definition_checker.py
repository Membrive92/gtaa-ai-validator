"""
Tests for gtaa_validator.checkers.definition_checker

Covers:
- DefinitionChecker.can_check(): test file detection by naming patterns
- DefinitionChecker.check() + BrowserAPICallVisitor: violation detection via AST
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.definition_checker import DefinitionChecker
from gtaa_validator.models import ViolationType, Severity


@pytest.fixture
def checker():
    """Fresh DefinitionChecker instance."""
    return DefinitionChecker()


# =========================================================================
# can_check() — test file detection
# =========================================================================

class TestCanCheck:
    """Tests for DefinitionChecker.can_check()."""

    def test_prefix_pattern(self, checker):
        """test_login.py matches."""
        assert checker.can_check(Path("test_login.py")) is True

    def test_suffix_pattern(self, checker):
        """login_test.py matches."""
        assert checker.can_check(Path("login_test.py")) is True

    def test_in_tests_directory(self, checker):
        """File inside a 'tests' directory matches."""
        assert checker.can_check(Path("project/tests/helpers.py")) is True

    def test_in_test_directory(self, checker):
        """File inside a 'test' directory matches."""
        assert checker.can_check(Path("project/test/utils.py")) is True

    def test_regular_py_file(self, checker):
        """A normal Python file does NOT match."""
        assert checker.can_check(Path("login_page.py")) is False

    def test_non_python_file(self, checker):
        """Non-.py files never match."""
        assert checker.can_check(Path("test_login.txt")) is False
        assert checker.can_check(Path("test_data.json")) is False

    def test_page_object_file(self, checker):
        """Page object files do NOT match."""
        assert checker.can_check(Path("pages/login_page.py")) is False

    def test_conftest(self, checker):
        """conftest.py in tests dir matches (due to 'test' in path)."""
        assert checker.can_check(Path("tests/conftest.py")) is True


# =========================================================================
# check() — Selenium detection
# =========================================================================

class TestCheckSelenium:
    """Tests for Selenium violation detection."""

    def test_detects_find_element(self, checker, write_py_file):
        """driver.find_element() inside test function is a violation."""
        path = write_py_file("test_example.py", """
def test_login():
    driver.find_element("id", "username")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION
        assert violations[0].severity == Severity.CRITICAL

    def test_detects_find_elements(self, checker, write_py_file):
        """driver.find_elements() is also detected."""
        path = write_py_file("test_example.py", """
def test_list_items():
    driver.find_elements("css", ".item")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION

    def test_detects_legacy_find_methods(self, checker, write_py_file):
        """Old-style find_element_by_* methods are detected."""
        path = write_py_file("test_example.py", """
def test_legacy():
    driver.find_element_by_id("username")
    driver.find_element_by_xpath("//input")
    driver.find_element_by_css_selector(".btn")
""")
        violations = checker.check(path)
        assert len(violations) == 3

    def test_multiple_violations_in_one_function(self, checker, write_py_file):
        """Multiple calls in one test function produce multiple violations."""
        path = write_py_file("test_example.py", """
def test_full_login():
    driver.find_element("id", "user")
    driver.find_element("id", "pass")
    driver.find_element("id", "submit")
""")
        violations = checker.check(path)
        assert len(violations) == 3


# =========================================================================
# check() — Playwright detection
# =========================================================================

class TestCheckPlaywright:
    """Tests for Playwright violation detection."""

    def test_detects_page_locator(self, checker, write_py_file):
        """page.locator() inside test function is a violation."""
        path = write_py_file("test_example.py", """
def test_search():
    page.locator("#search-input")
""")
        violations = checker.check(path)
        assert len(violations) == 1

    def test_detects_page_click(self, checker, write_py_file):
        """page.click() inside test function is a violation."""
        path = write_py_file("test_example.py", """
def test_click():
    page.click("#submit-btn")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION

    def test_detects_page_fill(self, checker, write_py_file):
        """page.fill() inside test function is a violation."""
        path = write_py_file("test_example.py", """
def test_fill():
    page.fill("#email", "user@test.com")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION

    def test_detects_wait_for_selector(self, checker, write_py_file):
        """page.wait_for_selector() is a violation."""
        path = write_py_file("test_example.py", """
def test_wait():
    page.wait_for_selector(".loaded")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION


# =========================================================================
# check() — things that should NOT be violations
# =========================================================================

class TestNoViolation:
    """Tests that confirm certain patterns do NOT trigger violations."""

    def test_page_object_calls_are_ok(self, checker, write_py_file):
        """Calling a page object method is NOT a violation."""
        path = write_py_file("test_example.py", """
def test_login():
    login_page.enter_username("user")
    login_page.enter_password("pass")
    login_page.click_submit()
""")
        violations = checker.check(path)
        assert len(violations) == 0

    def test_calls_outside_test_function(self, checker, write_py_file):
        """Browser calls outside test_* functions are NOT violations."""
        path = write_py_file("test_example.py", """
def setup():
    driver.find_element("id", "username")

def helper_login():
    page.locator("#login")
""")
        violations = checker.check(path)
        assert len(violations) == 0

    def test_non_browser_object(self, checker, write_py_file):
        """Calls on non-browser objects are NOT violations."""
        path = write_py_file("test_example.py", """
def test_something():
    my_list.find_element("item")
    widget.click()
    form.fill("data")
""")
        violations = checker.check(path)
        assert len(violations) == 0

    def test_clean_file_no_violations(self, checker, write_py_file):
        """A file with no browser calls produces zero violations."""
        path = write_py_file("test_example.py", """
def test_math():
    assert 2 + 2 == 4

def test_string():
    assert "hello".upper() == "HELLO"
""")
        violations = checker.check(path)
        assert len(violations) == 0

    def test_empty_file(self, checker, write_py_file):
        """An empty file produces zero violations."""
        path = write_py_file("test_empty.py", "")
        violations = checker.check(path)
        assert len(violations) == 0


# =========================================================================
# check() — edge cases
# =========================================================================

class TestEdgeCases:
    """Edge cases and robustness tests."""

    def test_syntax_error_handled_gracefully(self, checker, write_py_file):
        """Files with syntax errors don't crash — return empty list."""
        path = write_py_file("test_broken.py", """
def test_broken(
    # missing closing paren
    driver.find_element("id", "x")
""")
        violations = checker.check(path)
        assert violations == []

    def test_self_driver_attribute(self, checker, write_py_file):
        """self.driver.find_element() IS detected as violation (Phase 9+)."""
        path = write_py_file("test_example.py", """
def test_with_self():
    self.driver.find_element("id", "username")
""")
        # Phase 9+: self.driver.find_element() resolves to driver.find_element()
        # 'driver' IS in BROWSER_OBJECTS, so this IS a violation
        # This is correct gTAA behavior: test code should use Page Objects
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION

    def test_correct_line_numbers(self, checker, write_py_file):
        """Line numbers in violations match the actual source lines."""
        path = write_py_file("test_example.py", """
# Line 2
# Line 3
def test_login():
    x = 1          # Line 5
    driver.find_element("id", "user")  # Line 6
    y = 2          # Line 7
    driver.find_element("id", "pass")  # Line 8
""")
        violations = checker.check(path)
        assert len(violations) == 2
        assert violations[0].line_number == 6
        assert violations[1].line_number == 8

    def test_mixed_selenium_and_playwright(self, checker, write_py_file):
        """Both Selenium and Playwright violations in one file."""
        path = write_py_file("test_example.py", """
def test_selenium():
    driver.find_element("id", "user")

def test_playwright():
    page.locator("#search")
""")
        violations = checker.check(path)
        assert len(violations) == 2

    def test_violation_has_code_snippet(self, checker, write_py_file):
        """Each violation includes a code snippet."""
        path = write_py_file("test_example.py", """
def test_login():
    driver.find_element("id", "username")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].code_snippet is not None
        assert "find_element" in violations[0].code_snippet

    def test_violation_has_correct_file_path(self, checker, write_py_file):
        """Violation file_path matches the analyzed file."""
        path = write_py_file("test_example.py", """
def test_login():
    driver.find_element("id", "username")
""")
        violations = checker.check(path)
        assert violations[0].file_path == path


# =========================================================================
# check() — file_type filtering (Phase 7)
# =========================================================================

class TestFileTypeFiltering:
    """API files should skip ADAPTATION_IN_DEFINITION."""

    def test_api_file_skips_violations(self, checker, write_py_file):
        """file_type='api' → no violations even with browser calls."""
        path = write_py_file("test_example.py", """
def test_login():
    driver.find_element("id", "username")
""")
        violations = checker.check(path, file_type="api")
        assert len(violations) == 0

    def test_ui_file_detects_violations(self, checker, write_py_file):
        """file_type='ui' → violations detected normally."""
        path = write_py_file("test_example.py", """
def test_login():
    driver.find_element("id", "username")
""")
        violations = checker.check(path, file_type="ui")
        assert len(violations) == 1


# =========================================================================
# check() — nested browser calls in class methods
# =========================================================================

class TestNestedBrowserCallInClass:
    """Browser call inside a class method that is a test function."""

    def test_nested_browser_call_in_class_method(self, checker, write_py_file):
        """Browser call in a test method inside a class is still detected."""
        path = write_py_file("test_example.py", """
class TestLogin:
    def test_login(self):
        driver.find_element("id", "username")
""")
        violations = checker.check(path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ADAPTATION_IN_DEFINITION

