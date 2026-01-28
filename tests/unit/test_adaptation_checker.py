"""
Tests for gtaa_validator.checkers.adaptation_checker

Covers:
- can_check(): Page Object file detection
- Forbidden imports (pytest, unittest)
- Assertions in class methods
- Business logic (if/for/while) in class methods
- Duplicate locators across files
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
from gtaa_validator.models import ViolationType, Severity


@pytest.fixture
def checker():
    return AdaptationChecker()


@pytest.fixture
def write_page_file(tmp_path):
    """Write a Python file inside a pages/ subdirectory."""
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir(exist_ok=True)

    def _write(filename: str, content: str) -> Path:
        fp = pages_dir / filename
        fp.write_text(content, encoding="utf-8")
        return fp

    return _write


# =========================================================================
# can_check — Page Object detection
# =========================================================================

class TestCanCheck:

    def test_file_in_pages_dir(self, checker):
        assert checker.can_check(Path("project/pages/login_page.py")) is True

    def test_file_in_page_objects_dir(self, checker):
        assert checker.can_check(Path("project/page_objects/login.py")) is True

    def test_file_in_pom_dir(self, checker):
        assert checker.can_check(Path("project/pom/login.py")) is True

    def test_file_named_page(self, checker):
        assert checker.can_check(Path("login_page.py")) is True

    def test_file_named_pom(self, checker):
        assert checker.can_check(Path("login_pom.py")) is True

    def test_regular_py_file(self, checker):
        assert checker.can_check(Path("utils.py")) is False

    def test_test_file(self, checker):
        assert checker.can_check(Path("test_login.py")) is False

    def test_page_in_tests_dir(self, checker):
        """File in pages/ inside tests/ should be excluded."""
        assert checker.can_check(Path("tests/pages/helper.py")) is False

    def test_non_python(self, checker):
        assert checker.can_check(Path("pages/readme.txt")) is False


# =========================================================================
# Forbidden imports
# =========================================================================

class TestForbiddenImports:

    def test_detects_import_pytest(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
import pytest

class LoginPage:
    pass
""")
        violations = checker.check(path)
        assert any(v.violation_type == ViolationType.FORBIDDEN_IMPORT for v in violations)

    def test_detects_from_unittest(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
from unittest import TestCase

class LoginPage:
    pass
""")
        violations = checker.check(path)
        assert any(v.violation_type == ViolationType.FORBIDDEN_IMPORT for v in violations)

    def test_detects_from_unittest_mock(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
from unittest.mock import MagicMock

class LoginPage:
    pass
""")
        violations = checker.check(path)
        assert any(v.violation_type == ViolationType.FORBIDDEN_IMPORT for v in violations)

    def test_selenium_import_ok(self, checker, write_page_file):
        """Selenium imports are expected in Page Objects."""
        path = write_page_file("login_page.py", """\
from selenium.webdriver.common.by import By

class LoginPage:
    pass
""")
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.FORBIDDEN_IMPORT for v in violations)


# =========================================================================
# Assertions in POM
# =========================================================================

class TestAssertions:

    def test_detects_assert_in_method(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
class LoginPage:
    def verify_title(self):
        assert self.title == "Login"
""")
        violations = checker.check(path)
        asserts = [v for v in violations if v.violation_type == ViolationType.ASSERTION_IN_POM]
        assert len(asserts) == 1
        assert asserts[0].severity == Severity.HIGH

    def test_no_assert_outside_class(self, checker, write_page_file):
        """Assert outside a class method is not flagged."""
        path = write_page_file("login_page.py", """\
assert True  # module-level

class LoginPage:
    pass
""")
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.ASSERTION_IN_POM for v in violations)

    def test_multiple_asserts(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
class LoginPage:
    def check(self):
        assert self.a == 1
        assert self.b == 2
""")
        violations = checker.check(path)
        asserts = [v for v in violations if v.violation_type == ViolationType.ASSERTION_IN_POM]
        assert len(asserts) == 2


# =========================================================================
# Business logic in POM
# =========================================================================

class TestBusinessLogic:

    def test_detects_if_in_method(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
class LoginPage:
    def do_something(self):
        if True:
            pass
""")
        violations = checker.check(path)
        biz = [v for v in violations if v.violation_type == ViolationType.BUSINESS_LOGIC_IN_POM]
        assert len(biz) >= 1

    def test_detects_for_in_method(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
class LoginPage:
    def get_items(self):
        for i in range(10):
            pass
""")
        violations = checker.check(path)
        biz = [v for v in violations if v.violation_type == ViolationType.BUSINESS_LOGIC_IN_POM]
        assert len(biz) >= 1

    def test_detects_while_in_method(self, checker, write_page_file):
        path = write_page_file("login_page.py", """\
class LoginPage:
    def wait(self):
        while not self.ready:
            pass
""")
        violations = checker.check(path)
        biz = [v for v in violations if v.violation_type == ViolationType.BUSINESS_LOGIC_IN_POM]
        assert len(biz) >= 1

    def test_no_logic_outside_class(self, checker, write_page_file):
        """Logic outside a class is not flagged."""
        path = write_page_file("login_page.py", """\
if __name__ == "__main__":
    pass

class LoginPage:
    pass
""")
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.BUSINESS_LOGIC_IN_POM for v in violations)

    def test_clean_page_object(self, checker, write_page_file):
        """A clean Page Object has no violations."""
        path = write_page_file("login_page.py", """\
from selenium.webdriver.common.by import By

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.username = (By.ID, "username")

    def enter_username(self, value):
        self.driver.find_element(*self.username).send_keys(value)
""")
        violations = checker.check(path)
        assert len(violations) == 0


# =========================================================================
# Duplicate locators
# =========================================================================

class TestDuplicateLocators:

    def test_detects_duplicate_across_files(self, checker, write_page_file):
        """Same locator in two files triggers violation on the second."""
        write_page_file("page_a.py", """\
from selenium.webdriver.common.by import By
class PageA:
    loc = (By.ID, "shared-locator")
""")
        path_b = write_page_file("page_b.py", """\
from selenium.webdriver.common.by import By
class PageB:
    loc = (By.ID, "shared-locator")
""")
        # Check both files to populate registry
        checker.check(write_page_file("page_a.py", """\
from selenium.webdriver.common.by import By
class PageA:
    loc = (By.ID, "shared-locator")
"""))
        violations = checker.check(path_b)
        dups = [v for v in violations if v.violation_type == ViolationType.DUPLICATE_LOCATOR]
        assert len(dups) >= 1

    def test_no_duplicate_single_file(self, checker, write_page_file):
        """Same locator in one file is not a cross-file duplicate."""
        # Fresh checker for isolated test
        fresh = AdaptationChecker()
        path = write_page_file("page_a.py", """\
from selenium.webdriver.common.by import By
class PageA:
    loc1 = (By.ID, "unique-loc")
""")
        violations = fresh.check(path)
        dups = [v for v in violations if v.violation_type == ViolationType.DUPLICATE_LOCATOR]
        assert len(dups) == 0


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:

    def test_syntax_error_handled(self, checker, write_page_file):
        path = write_page_file("broken_page.py", "class Foo(\n")
        assert checker.check(path) == []

    def test_empty_file(self, checker, write_page_file):
        path = write_page_file("empty_page.py", "")
        assert checker.check(path) == []
