"""
Tests for gtaa_validator.checkers.bdd_checker

Covers:
- can_check() for .feature and step definition files
- GHERKIN_IMPLEMENTATION_DETAIL detection
- MISSING_THEN_STEP detection
- STEP_DEF_DIRECT_BROWSER_CALL detection
- STEP_DEF_TOO_COMPLEX detection
- DUPLICATE_STEP_PATTERN (check_project)
- _is_step_definition_path utility
- _is_step_function utility
"""

import ast
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from gtaa_validator.checkers.bdd_checker import BDDChecker
from gtaa_validator.models import ViolationType, Severity


@pytest.fixture
def checker():
    return BDDChecker()


# =========================================================================
# can_check
# =========================================================================

class TestCanCheck:

    def test_feature_file(self, checker):
        assert checker.can_check(Path("login.feature")) is True

    def test_step_file_in_steps_dir(self, checker):
        assert checker.can_check(Path("steps/login_steps.py")) is True

    def test_step_file_by_name(self, checker):
        assert checker.can_check(Path("login_steps.py")) is True

    def test_regular_python_file(self, checker):
        assert checker.can_check(Path("utils.py")) is False

    def test_non_python_non_feature(self, checker):
        assert checker.can_check(Path("readme.md")) is False

    def test_step_defs_dir(self, checker):
        assert checker.can_check(Path("step_defs/login.py")) is True

    def test_step_definitions_dir(self, checker):
        assert checker.can_check(Path("step_definitions/login.py")) is True


# =========================================================================
# _is_step_function
# =========================================================================

class TestIsStepFunction:

    def test_given_decorator(self, checker):
        code = '@given("I am on the login page")\ndef step_login(context): pass'
        tree = ast.parse(code)
        func = tree.body[0]
        assert checker._is_step_function(func) is True

    def test_when_decorator(self, checker):
        code = '@when("I click submit")\ndef step_click(context): pass'
        tree = ast.parse(code)
        func = tree.body[0]
        assert checker._is_step_function(func) is True

    def test_then_decorator(self, checker):
        code = '@then("I see the dashboard")\ndef step_verify(context): pass'
        tree = ast.parse(code)
        func = tree.body[0]
        assert checker._is_step_function(func) is True

    def test_no_step_decorator(self, checker):
        code = '@pytest.fixture\ndef my_fixture(): pass'
        tree = ast.parse(code)
        func = tree.body[0]
        assert checker._is_step_function(func) is False


# =========================================================================
# Feature file checks
# =========================================================================

class TestFeatureFileChecks:

    def _check_feature(self, checker, content):
        """Helper to check a .feature file from string content."""
        feature_path = Path("test.feature")
        with patch("builtins.open", mock_open(read_data=content)):
            return checker._check_feature_file(feature_path)

    def test_detect_xpath_in_feature(self, checker):
        content = """Feature: Login
  Scenario: XPath
    When I type "admin" into //input[@id='username']
    Then I see the dashboard
"""
        violations = self._check_feature(checker, content)
        impl = [v for v in violations if v.violation_type == ViolationType.GHERKIN_IMPLEMENTATION_DETAIL]
        assert len(impl) >= 1
        assert impl[0].severity == Severity.HIGH

    def test_detect_url_in_feature(self, checker):
        content = """Feature: Login
  Scenario: URL
    Given I navigate to http://localhost:8080/login
    Then I see the page
"""
        violations = self._check_feature(checker, content)
        impl = [v for v in violations if v.violation_type == ViolationType.GHERKIN_IMPLEMENTATION_DETAIL]
        assert len(impl) >= 1
        assert impl[0].severity == Severity.HIGH

    def test_detect_sql_in_feature(self, checker):
        content = """Feature: Admin
  Scenario: SQL
    When I run SELECT * FROM users WHERE role='admin'
    Then I see results
"""
        violations = self._check_feature(checker, content)
        impl = [v for v in violations if v.violation_type == ViolationType.GHERKIN_IMPLEMENTATION_DETAIL]
        assert len(impl) >= 1
        assert impl[0].severity == Severity.HIGH

    def test_clean_feature_no_violations(self, checker):
        content = """Feature: Login
  Scenario: Valid login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
"""
        violations = self._check_feature(checker, content)
        assert len(violations) == 0

    def test_detect_missing_then(self, checker):
        content = """Feature: Login
  Scenario: No verification
    Given I am on the login page
    When I enter credentials
    And I click submit
"""
        violations = self._check_feature(checker, content)
        missing = [v for v in violations if v.violation_type == ViolationType.MISSING_THEN_STEP]
        assert len(missing) == 1
        assert missing[0].severity == Severity.MEDIUM

    def test_scenario_with_then_no_missing_then(self, checker):
        content = """Feature: Login
  Scenario: With then
    Given I am on the login page
    When I click submit
    Then I see the dashboard
"""
        violations = self._check_feature(checker, content)
        types = [v.violation_type for v in violations]
        assert ViolationType.MISSING_THEN_STEP not in types


# =========================================================================
# Step definition checks
# =========================================================================

class TestStepDefinitionChecks:

    def _check_step_file(self, checker, content):
        """Helper to check a step definition file from string content."""
        step_path = Path("steps/test_steps.py")
        tree = ast.parse(content)
        with patch("builtins.open", mock_open(read_data=content)):
            return checker._check_step_definition(step_path, tree)

    def test_detect_browser_call_selenium(self, checker):
        content = '''from behave import given
@given("I am on the login page")
def step_login(context):
    context.driver.find_element("id", "username")
'''
        violations = self._check_step_file(checker, content)
        browser = [v for v in violations if v.violation_type == ViolationType.STEP_DEF_DIRECT_BROWSER_CALL]
        assert len(browser) >= 1
        assert browser[0].severity == Severity.CRITICAL

    def test_detect_browser_call_playwright(self, checker):
        content = '''from behave import when
@when("I click submit")
def step_click(context):
    context.page.locator("#submit").click()
'''
        violations = self._check_step_file(checker, content)
        browser = [v for v in violations if v.violation_type == ViolationType.STEP_DEF_DIRECT_BROWSER_CALL]
        assert len(browser) >= 1
        assert browser[0].severity == Severity.CRITICAL

    def test_clean_step_no_browser_call(self, checker):
        content = '''from behave import given
@given("I am on the login page")
def step_login(context):
    context.login_page.navigate()
'''
        violations = self._check_step_file(checker, content)
        types = [v.violation_type for v in violations]
        assert ViolationType.STEP_DEF_DIRECT_BROWSER_CALL not in types

    def test_detect_too_complex_step(self, checker):
        # Create a step function with > 15 lines
        lines = ['    x = 1'] * 20
        body = '\n'.join(lines)
        content = f'''from behave import then
@then("I verify the dashboard")
def step_verify(context):
{body}
'''
        violations = self._check_step_file(checker, content)
        complex_v = [v for v in violations if v.violation_type == ViolationType.STEP_DEF_TOO_COMPLEX]
        assert len(complex_v) >= 1
        assert complex_v[0].severity == Severity.MEDIUM

    def test_short_step_not_too_complex(self, checker):
        content = '''from behave import given
@given("I am logged in")
def step_login(context):
    context.login_page.login("admin", "pass")
'''
        violations = self._check_step_file(checker, content)
        types = [v.violation_type for v in violations]
        assert ViolationType.STEP_DEF_TOO_COMPLEX not in types


# =========================================================================
# check_project (duplicate step patterns)
# =========================================================================

class TestCheckProject:

    def test_detect_duplicate_step_pattern(self, checker, tmp_path):
        steps_dir = tmp_path / "steps"
        steps_dir.mkdir()

        file1 = steps_dir / "login_steps.py"
        file1.write_text('''from behave import given
@given("I am on the login page")
def step_login(context):
    pass
''')
        file2 = steps_dir / "search_steps.py"
        file2.write_text('''from behave import given
@given("I am on the login page")
def step_login_dup(context):
    pass
''')

        violations = checker.check_project(tmp_path)
        types = [v.violation_type for v in violations]
        assert ViolationType.DUPLICATE_STEP_PATTERN in types

    def test_no_duplicate_when_unique_patterns(self, checker, tmp_path):
        steps_dir = tmp_path / "steps"
        steps_dir.mkdir()

        file1 = steps_dir / "login_steps.py"
        file1.write_text('''from behave import given
@given("I am on the login page")
def step_login(context):
    pass
''')
        file2 = steps_dir / "search_steps.py"
        file2.write_text('''from behave import when
@when("I search for something")
def step_search(context):
    pass
''')

        violations = checker.check_project(tmp_path)
        types = [v.violation_type for v in violations]
        assert ViolationType.DUPLICATE_STEP_PATTERN not in types


# =========================================================================
# _is_step_definition_path
# =========================================================================

class TestIsStepDefinitionPath:

    def test_steps_directory(self, checker):
        assert checker._is_step_definition_path(Path("project/steps/login.py")) is True

    def test_step_prefix(self, checker):
        assert checker._is_step_definition_path(Path("step_login.py")) is True

    def test_steps_suffix(self, checker):
        assert checker._is_step_definition_path(Path("login_steps.py")) is True

    def test_regular_file(self, checker):
        assert checker._is_step_definition_path(Path("login_page.py")) is False


# =========================================================================
# Additional feature file edge cases
# =========================================================================

class TestFeatureFileEdgeCases:

    def _check_feature(self, checker, content):
        feature_path = Path("test.feature")
        with patch("builtins.open", mock_open(read_data=content)):
            return checker._check_feature_file(feature_path)

    def test_detect_css_id_selector_in_feature(self, checker):
        """CSS #id selector in feature step is an implementation detail."""
        content = """Feature: Login
  Scenario: CSS selector
    When I click on #submit-button
    Then I see the dashboard
"""
        violations = self._check_feature(checker, content)
        impl = [v for v in violations if v.violation_type == ViolationType.GHERKIN_IMPLEMENTATION_DETAIL]
        assert len(impl) >= 1

    def test_background_implementation_detail(self, checker):
        """Implementation details in Background steps are also detected."""
        content = """Feature: Login
  Background:
    Given I navigate to http://localhost:3000/login

  Scenario: Login
    When I enter valid credentials
    Then I see the dashboard
"""
        violations = self._check_feature(checker, content)
        impl = [v for v in violations if v.violation_type == ViolationType.GHERKIN_IMPLEMENTATION_DETAIL]
        assert len(impl) >= 1

    def test_empty_feature_file(self, checker):
        """Empty feature file produces no violations."""
        violations = self._check_feature(checker, "")
        assert violations == []
