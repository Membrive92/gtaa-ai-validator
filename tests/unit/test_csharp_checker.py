"""
Tests for unified checkers with C# files.

Phase 9+: Tests that DefinitionChecker, AdaptationChecker, and QualityChecker
correctly detect violations in C# code.

Covers:
- Browser call detection in [Test] methods (ADAPTATION_IN_DEFINITION)
- Assertion detection in Page Objects (ASSERTION_IN_POM)
- Forbidden import detection (FORBIDDEN_IMPORT)
- Hardcoded test data detection (HARDCODED_TEST_DATA)
- Poor test naming detection (POOR_TEST_NAMING)
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.definition_checker import DefinitionChecker
from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
from gtaa_validator.checkers.quality_checker import QualityChecker
from gtaa_validator.models import ViolationType
from gtaa_validator.parsers import get_parser_for_file


def parse_and_check(checker, file_path: Path):
    """Helper to parse a file and run the checker."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    parser = get_parser_for_file(file_path)
    parse_result = parser.parse(source) if parser else None
    return checker.check(file_path, parse_result)


class TestDefinitionCheckerCSharp:
    """Tests for ADAPTATION_IN_DEFINITION detection in C# files."""

    def setup_method(self):
        self.checker = DefinitionChecker()

    def test_can_check_csharp_file(self):
        """DefinitionChecker can check .cs files."""
        assert self.checker.can_check(Path("LoginTests.cs")) is True

    def test_detects_FindElement_in_test(self, tmp_path):
        """Detects driver.FindElement() in [Test] method."""
        code = '''
using NUnit.Framework;
using OpenQA.Selenium;

public class LoginTests
{
    private IWebDriver _driver;

    [Test]
    public void TestLogin()
    {
        _driver.FindElement(By.Id("username")).SendKeys("test");
    }
}
'''
        test_file = tmp_path / "LoginTests.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) > 0

    def test_detects_Navigate_in_test(self, tmp_path):
        """Detects driver.Navigate() in [Test] method."""
        code = '''
using NUnit.Framework;
using OpenQA.Selenium;

public class LoginTests
{
    private IWebDriver _driver;

    [Test]
    public void TestNavigation()
    {
        _driver.Navigate().GoToUrl("https://example.com");
    }
}
'''
        test_file = tmp_path / "LoginTests.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) > 0


class TestAdaptationCheckerCSharp:
    """Tests for ASSERTION_IN_POM and FORBIDDEN_IMPORT detection in C# files."""

    def setup_method(self):
        self.checker = AdaptationChecker()

    def test_can_check_csharp_file(self):
        """AdaptationChecker can check .cs files."""
        assert self.checker.can_check(Path("LoginPage.cs")) is True

    def test_detects_Assert_in_page(self, tmp_path):
        """Detects Assert calls in Page Object class."""
        code = '''
using OpenQA.Selenium;
using NUnit.Framework;

public class LoginPage
{
    private IWebDriver _driver;

    public void VerifyLogin()
    {
        Assert.That(_driver.Url, Does.Contain("dashboard"));
    }
}
'''
        test_file = tmp_path / "LoginPage.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        assertion_violations = [v for v in violations
                               if v.violation_type == ViolationType.ASSERTION_IN_POM]
        assert len(assertion_violations) > 0

    def test_detects_NUnit_using_in_page(self, tmp_path):
        """Detects NUnit using in Page Object."""
        code = '''
using OpenQA.Selenium;
using NUnit.Framework;

public class LoginPage
{
    private IWebDriver _driver;

    public void ClickLogin()
    {
        // ...
    }
}
'''
        test_file = tmp_path / "LoginPage.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        forbidden_violations = [v for v in violations
                               if v.violation_type == ViolationType.FORBIDDEN_IMPORT]
        assert len(forbidden_violations) > 0


class TestQualityCheckerCSharp:
    """Tests for HARDCODED_TEST_DATA and POOR_TEST_NAMING detection in C# files."""

    def setup_method(self):
        self.checker = QualityChecker()

    def test_can_check_csharp_file(self):
        """QualityChecker can check .cs files."""
        assert self.checker.can_check(Path("LoginTests.cs")) is True

    def test_detects_hardcoded_email(self, tmp_path):
        """Detects hardcoded email in test."""
        code = '''
using NUnit.Framework;

public class LoginTests
{
    [Test]
    public void TestLogin()
    {
        var email = "test@example.com";
    }
}
'''
        test_file = tmp_path / "LoginTests.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        hardcoded_violations = [v for v in violations
                               if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hardcoded_violations) > 0

    def test_detects_hardcoded_url(self, tmp_path):
        """Detects hardcoded URL in test."""
        code = '''
using NUnit.Framework;

public class LoginTests
{
    [Test]
    public void TestNavigation()
    {
        _driver.Navigate().GoToUrl("https://example.com/login");
    }
}
'''
        test_file = tmp_path / "LoginTests.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        hardcoded_violations = [v for v in violations
                               if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hardcoded_violations) > 0

    def test_detects_Test1_name(self, tmp_path):
        """Detects generic Test1 name."""
        code = '''
using NUnit.Framework;

public class LoginTests
{
    [Test]
    public void Test1()
    {
        // ...
    }
}
'''
        test_file = tmp_path / "LoginTests.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) > 0

    def test_good_name_no_violation(self, tmp_path):
        """Descriptive name does not trigger violation."""
        code = '''
using NUnit.Framework;

public class LoginTests
{
    [Test]
    public void TestUserCanLoginWithValidCredentials()
    {
        // ...
    }
}
'''
        test_file = tmp_path / "LoginTests.cs"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) == 0
