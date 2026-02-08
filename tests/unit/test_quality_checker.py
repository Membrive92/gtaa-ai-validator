"""
Tests for gtaa_validator.checkers.quality_checker

Covers:
- can_check(): test file detection
- Hardcoded data: emails, URLs, phone numbers, passwords
- Long test functions (>50 lines)
- Poor test naming (generic names)
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.quality_checker import QualityChecker
from gtaa_validator.models import ViolationType, Severity


@pytest.fixture
def checker():
    return QualityChecker()



# =========================================================================
# can_check
# =========================================================================

class TestCanCheck:

    def test_test_prefix(self, checker):
        assert checker.can_check(Path("test_login.py")) is True

    def test_test_suffix(self, checker):
        assert checker.can_check(Path("login_test.py")) is True

    def test_in_tests_dir(self, checker):
        assert checker.can_check(Path("tests/helpers.py")) is True

    def test_regular_file(self, checker):
        assert checker.can_check(Path("login_page.py")) is False

    def test_non_python(self, checker):
        assert checker.can_check(Path("test_data.json")) is False


# =========================================================================
# Hardcoded data — emails
# =========================================================================

class TestHardcodedEmail:

    def test_detects_email(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_login():
    email = "user@example.com"
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hc) >= 1
        assert hc[0].severity == Severity.HIGH

    def test_no_email_no_violation(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_math():
    assert 2 + 2 == 4
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.HARDCODED_TEST_DATA for v in violations)


# =========================================================================
# Hardcoded data — URLs
# =========================================================================

class TestHardcodedURL:

    def test_detects_url(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_api():
    url = "https://api.example.com/v1"
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hc) >= 1


# =========================================================================
# Hardcoded data — phones
# =========================================================================

class TestHardcodedPhone:

    def test_detects_phone(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_contact():
    phone = "555-123-4567"
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hc) >= 1


# =========================================================================
# Hardcoded data — passwords
# =========================================================================

class TestHardcodedPassword:

    def test_detects_password_keyword(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_login():
    pwd = "MyPassword123"
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hc) >= 1

    def test_short_strings_ignored(self, checker, write_py_file):
        """Strings shorter than 5 chars are not checked."""
        path = write_py_file("test_example.py", '''\
def test_short():
    x = "ab"
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.HARDCODED_TEST_DATA for v in violations)

    def test_data_outside_test_not_flagged(self, checker, write_py_file):
        """Hardcoded data outside test functions is not flagged."""
        path = write_py_file("test_example.py", '''\
BASE_URL = "https://example.com/api"

def test_something():
    assert True
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.HARDCODED_TEST_DATA for v in violations)


# =========================================================================
# Long test functions
# =========================================================================

class TestLongFunctions:

    def test_detects_long_function(self, checker, write_py_file):
        # Generate a function with 60 lines
        lines = ["def test_long():"]
        for i in range(60):
            lines.append(f"    step_{i} = {i}")
        path = write_py_file("test_example.py", "\n".join(lines))

        violations = checker.check(path)
        long = [v for v in violations if v.violation_type == ViolationType.LONG_TEST_FUNCTION]
        assert len(long) == 1
        assert long[0].severity == Severity.MEDIUM

    def test_short_function_ok(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_short():
    assert True
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.LONG_TEST_FUNCTION for v in violations)

    def test_non_test_long_function_ignored(self, checker, write_py_file):
        """Long helper functions are not flagged."""
        lines = ["def helper():"]
        for i in range(60):
            lines.append(f"    step_{i} = {i}")
        path = write_py_file("test_example.py", "\n".join(lines))
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.LONG_TEST_FUNCTION for v in violations)


# =========================================================================
# Poor test naming
# =========================================================================

class TestPoorNaming:

    @pytest.mark.parametrize("name", [
        "test_1", "test_2", "test_a", "test_case1", "test_case",
    ])
    def test_detects_generic_names(self, checker, write_py_file, name):
        path = write_py_file("test_example.py", f"""\
def {name}():
    pass
""")
        violations = checker.check(path)
        poor = [v for v in violations if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(poor) == 1
        assert poor[0].severity == Severity.LOW

    def test_descriptive_name_ok(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_user_can_login_with_valid_credentials():
    pass
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.POOR_TEST_NAMING for v in violations)


# =========================================================================
# Broad exception handling
# =========================================================================

class TestBroadExceptionHandling:

    def test_bare_except_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_something():
    try:
        do_stuff()
    except:
        pass
''')
        violations = checker.check(path)
        broad = [v for v in violations if v.violation_type == ViolationType.BROAD_EXCEPTION_HANDLING]
        assert len(broad) == 1
        assert broad[0].severity == Severity.MEDIUM
        assert "except:" in broad[0].code_snippet

    def test_except_exception_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_something():
    try:
        do_stuff()
    except Exception:
        pass
''')
        violations = checker.check(path)
        broad = [v for v in violations if v.violation_type == ViolationType.BROAD_EXCEPTION_HANDLING]
        assert len(broad) == 1
        assert "except Exception:" in broad[0].code_snippet

    def test_specific_except_ok(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_something():
    try:
        do_stuff()
    except ValueError:
        pass
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.BROAD_EXCEPTION_HANDLING for v in violations)

    def test_multiple_specific_except_ok(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_something():
    try:
        do_stuff()
    except (TypeError, KeyError):
        pass
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.BROAD_EXCEPTION_HANDLING for v in violations)


# =========================================================================
# Hardcoded configuration
# =========================================================================

class TestHardcodedConfiguration:

    def test_localhost_url_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_api():
    url = "http://localhost:8080/api"
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_CONFIGURATION]
        assert len(hc) >= 1
        assert hc[0].severity == Severity.HIGH

    def test_sleep_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
import time
def test_wait():
    time.sleep(5)
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_CONFIGURATION]
        assert len(hc) >= 1

    def test_absolute_path_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_file():
    path = "/home/user/data/test.csv"
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_CONFIGURATION]
        assert len(hc) >= 1

    def test_comment_ignored(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_ok():
    # http://localhost:8080 is the base URL
    assert True
''')
        violations = checker.check(path)
        hc = [v for v in violations if v.violation_type == ViolationType.HARDCODED_CONFIGURATION]
        assert len(hc) == 0

    def test_no_config_no_violation(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
def test_math():
    assert 2 + 2 == 4
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.HARDCODED_CONFIGURATION for v in violations)


# =========================================================================
# Shared mutable state
# =========================================================================

class TestSharedMutableState:

    def test_module_level_list_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
shared_data = []

def test_one():
    shared_data.append(1)

def test_two():
    assert len(shared_data) == 1
''')
        violations = checker.check(path)
        sm = [v for v in violations if v.violation_type == ViolationType.SHARED_MUTABLE_STATE]
        assert len(sm) >= 1
        assert sm[0].severity == Severity.HIGH

    def test_module_level_dict_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
cache = {}

def test_cached():
    cache["key"] = "value"
''')
        violations = checker.check(path)
        sm = [v for v in violations if v.violation_type == ViolationType.SHARED_MUTABLE_STATE]
        assert len(sm) >= 1

    def test_uppercase_constant_ok(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
DEFAULTS = []

def test_ok():
    assert True
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.SHARED_MUTABLE_STATE for v in violations)

    def test_private_var_ok(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
_internal = {}

def test_ok():
    assert True
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.SHARED_MUTABLE_STATE for v in violations)

    def test_global_keyword_in_test_detected(self, checker, write_py_file):
        path = write_py_file("test_example.py", '''\
counter = 0

def test_increment():
    global counter
    counter += 1
''')
        violations = checker.check(path)
        sm = [v for v in violations if v.violation_type == ViolationType.SHARED_MUTABLE_STATE]
        # Should detect both: module-level mutable AND global keyword
        assert len(sm) >= 1

    def test_string_assignment_ok(self, checker, write_py_file):
        """Non-mutable module-level assignments should not be flagged."""
        path = write_py_file("test_example.py", '''\
base_url = "https://example.com"

def test_ok():
    assert True
''')
        violations = checker.check(path)
        assert not any(v.violation_type == ViolationType.SHARED_MUTABLE_STATE for v in violations)


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:

    def test_syntax_error_handled(self, checker, write_py_file):
        path = write_py_file("test_broken.py", "def test_x(\n")
        assert checker.check(path) == []

    def test_empty_file(self, checker, write_py_file):
        path = write_py_file("test_empty.py", "")
        assert checker.check(path) == []
