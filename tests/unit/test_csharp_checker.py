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
- CSharpParser: namespace extraction, base classes, attributes, parameters
- CSharpParser: call parsing, string extraction (verbatim, interpolated)
- CSharpParser utility methods: is_test_method, has_selenium_imports, etc.
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.definition_checker import DefinitionChecker
from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
from gtaa_validator.checkers.quality_checker import QualityChecker
from gtaa_validator.models import ViolationType
from gtaa_validator.parsers import get_parser_for_file
from gtaa_validator.parsers.csharp_parser import CSharpParser
from gtaa_validator.parsers.treesitter_base import ParsedFunction, ParsedImport, ParsedCall


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
        assert len(adaptation_violations) >= 1

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
        assert len(adaptation_violations) >= 1


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
        assert len(assertion_violations) >= 1

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
        assert len(forbidden_violations) >= 1


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
        assert len(hardcoded_violations) >= 1

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
        assert len(hardcoded_violations) >= 1

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
        assert len(naming_violations) >= 1

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


# =====================================================================
# CSharpParser direct tests (coverage for uncovered parser lines)
# =====================================================================


class TestCSharpParserImports:
    """Tests for CSharpParser namespace/import extraction."""

    def setup_method(self):
        self.parser = CSharpParser()

    def test_using_qualified_name(self, tmp_path):
        """Extracts qualified namespace from using directive."""
        code = 'using NUnit.Framework;\npublic class X {}\n'
        f = tmp_path / "X.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        modules = [imp.module for imp in result.imports]
        assert any("NUnit" in m for m in modules)

    def test_using_simple_identifier(self, tmp_path):
        """Extracts simple identifier from using directive."""
        code = 'using System;\npublic class X {}\n'
        f = tmp_path / "X.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        modules = [imp.module for imp in result.imports]
        assert any("System" in m for m in modules)


class TestCSharpParserClasses:
    """Tests for CSharpParser class extraction."""

    def setup_method(self):
        self.parser = CSharpParser()

    def test_class_with_base_class(self, tmp_path):
        """Class with inheritance extracts base class."""
        code = '''
using OpenQA.Selenium;

public class LoginPage : BasePage
{
    public void ClickLogin() { }
}
'''
        f = tmp_path / "LoginPage.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        assert len(result.classes) == 1
        assert "BasePage" in result.classes[0].base_classes
        assert result.classes[0].is_page_object is True

    def test_class_with_methods_and_parameters(self, tmp_path):
        """Class methods and parameters are extracted."""
        code = '''
public class LoginPage
{
    public void Login(string user, string pass)
    {
    }
}
'''
        f = tmp_path / "LoginPage.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        methods = result.classes[0].methods
        assert len(methods) == 1
        assert methods[0].name == "Login"
        assert "user" in methods[0].parameters


class TestCSharpParserAttributes:
    """Tests for C# attribute extraction ([Test], [SetUp], etc.)."""

    def setup_method(self):
        self.parser = CSharpParser()

    def test_test_attribute_extracted(self, tmp_path):
        """[Test] attribute is captured as decorator."""
        code = '''
using NUnit.Framework;

public class LoginTests
{
    [Test]
    public void TestLogin()
    {
    }
}
'''
        f = tmp_path / "LoginTests.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        methods = result.classes[0].methods
        assert len(methods) == 1
        assert "Test" in methods[0].decorators


class TestCSharpParserCalls:
    """Tests for C# method call extraction."""

    def setup_method(self):
        self.parser = CSharpParser()

    def test_member_access_call(self, tmp_path):
        """object.Method() call is extracted."""
        code = '''
public class LoginTests
{
    public void TestLogin()
    {
        _driver.FindElement(null);
    }
}
'''
        f = tmp_path / "LoginTests.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        fe_calls = [c for c in result.calls if "FindElement" in c.method_name]
        assert len(fe_calls) >= 1

    def test_chained_call(self, tmp_path):
        """Chained _driver.Navigate().GoToUrl() extracts calls."""
        code = '''
public class LoginTests
{
    public void TestNavigation()
    {
        _driver.Navigate().GoToUrl("https://example.com");
    }
}
'''
        f = tmp_path / "LoginTests.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        method_names = [c.method_name for c in result.calls]
        assert "GoToUrl" in method_names

    def test_direct_call_without_object(self, tmp_path):
        """Direct function call Console.WriteLine() is extracted."""
        code = '''
public class X
{
    public void Foo()
    {
        Console.WriteLine("hello");
    }
}
'''
        f = tmp_path / "X.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        assert len(result.calls) >= 1


class TestCSharpParserStrings:
    """Tests for C# string extraction (regular, verbatim, interpolated)."""

    def setup_method(self):
        self.parser = CSharpParser()

    def test_regular_string(self, tmp_path):
        """Regular string literal is extracted."""
        code = '''
public class X
{
    public void Foo()
    {
        var x = "hello world";
    }
}
'''
        f = tmp_path / "X.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        values = [s.value for s in result.strings]
        assert "hello world" in values

    def test_verbatim_string(self, tmp_path):
        """Verbatim string @"..." is handled (tree-sitter may use different node)."""
        code = '''
public class X
{
    public void Foo()
    {
        var path = @"C:\\temp\\file.txt";
        var msg = "normal string";
    }
}
'''
        f = tmp_path / "X.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        # At least the regular string should be extracted
        assert len(result.strings) >= 1
        values = [s.value for s in result.strings]
        assert "normal string" in values

    def test_interpolated_string(self, tmp_path):
        """Interpolated string $"..." is extracted."""
        code = '''
public class X
{
    public void Foo()
    {
        var name = "World";
        var msg = $"Hello {name}";
    }
}
'''
        f = tmp_path / "X.cs"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        assert len(result.strings) >= 1


class TestCSharpParserUtilityMethods:
    """Tests for CSharpParser utility methods."""

    def setup_method(self):
        self.parser = CSharpParser()

    def test_is_test_method_nunit(self):
        """Method with [Test] is identified as test."""
        func = ParsedFunction(name="TestLogin", line_start=1, line_end=5, decorators=["Test"])
        assert self.parser.is_test_method(func) is True

    def test_is_test_method_xunit(self):
        """Method with [Fact] is identified as test."""
        func = ParsedFunction(name="Login_Works", line_start=1, line_end=5, decorators=["Fact"])
        assert self.parser.is_test_method(func) is True

    def test_is_test_method_false(self):
        """Method without test attribute is not a test."""
        func = ParsedFunction(name="Helper", line_start=1, line_end=5, decorators=[])
        assert self.parser.is_test_method(func) is False

    def test_is_setup_method(self):
        """Method with [SetUp] is setup."""
        func = ParsedFunction(name="Setup", line_start=1, line_end=5, decorators=["SetUp"])
        assert self.parser.is_setup_method(func) is True

    def test_is_teardown_method(self):
        """Method with [TearDown] is teardown."""
        func = ParsedFunction(name="Cleanup", line_start=1, line_end=5, decorators=["TearDown"])
        assert self.parser.is_teardown_method(func) is True

    def test_is_teardown_method_false(self):
        """Method without teardown attribute is not teardown."""
        func = ParsedFunction(name="Cleanup", line_start=1, line_end=5, decorators=["Test"])
        assert self.parser.is_teardown_method(func) is False

    def test_has_selenium_imports(self):
        """Detects OpenQA.Selenium imports."""
        imports = [ParsedImport(module="OpenQA.Selenium", line=1)]
        assert self.parser.has_selenium_imports(imports) is True

    def test_has_selenium_imports_false(self):
        """Non-Selenium imports return False."""
        imports = [ParsedImport(module="NUnit.Framework", line=1)]
        assert self.parser.has_selenium_imports(imports) is False

    def test_has_playwright_imports(self):
        """Detects Microsoft.Playwright imports."""
        imports = [ParsedImport(module="Microsoft.Playwright", line=1)]
        assert self.parser.has_playwright_imports(imports) is True

    def test_has_test_framework_imports_nunit(self):
        """Detects NUnit imports."""
        imports = [ParsedImport(module="NUnit.Framework", line=1)]
        assert self.parser.has_test_framework_imports(imports) is True

    def test_has_test_framework_imports_xunit(self):
        """Detects xUnit imports."""
        imports = [ParsedImport(module="Xunit", line=1)]
        assert self.parser.has_test_framework_imports(imports) is True

    def test_has_test_framework_imports_false(self):
        """Non-test imports return False."""
        imports = [ParsedImport(module="System.IO", line=1)]
        assert self.parser.has_test_framework_imports(imports) is False

    def test_is_browser_api_call_driver(self):
        """driver.FindElement is a browser API call."""
        call = ParsedCall(object_name="driver", method_name="FindElement", line=1)
        assert self.parser.is_browser_api_call(call) is True

    def test_is_browser_api_call_page(self):
        """page.Locator is a browser API call."""
        call = ParsedCall(object_name="page", method_name="Locator", line=1)
        assert self.parser.is_browser_api_call(call) is True

    def test_is_browser_api_call_false(self):
        """Non-browser call returns False."""
        call = ParsedCall(object_name="logger", method_name="Info", line=1)
        assert self.parser.is_browser_api_call(call) is False
