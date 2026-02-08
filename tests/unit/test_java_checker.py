"""
Tests for unified checkers with Java files.

Phase 9+: Tests that DefinitionChecker, AdaptationChecker, and QualityChecker
correctly detect violations in Java code.

Covers:
- Browser call detection in @Test methods (ADAPTATION_IN_DEFINITION)
- Assertion detection in Page Objects (ASSERTION_IN_POM)
- Forbidden import detection (FORBIDDEN_IMPORT)
- Hardcoded test data detection (HARDCODED_TEST_DATA)
- Poor test naming detection (POOR_TEST_NAMING)
- JavaParser: class with extends, annotations, parameters, call parsing
- JavaParser utility methods: is_test_method, is_setup_method, etc.
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.definition_checker import DefinitionChecker
from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
from gtaa_validator.checkers.quality_checker import QualityChecker
from gtaa_validator.models import ViolationType
from gtaa_validator.parsers import get_parser_for_file
from gtaa_validator.parsers.java_parser import JavaParser
from gtaa_validator.parsers.treesitter_base import ParsedFunction, ParsedImport, ParsedCall


def parse_and_check(checker, file_path: Path):
    """Helper to parse a file and run the checker."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    parser = get_parser_for_file(file_path)
    parse_result = parser.parse(source) if parser else None
    return checker.check(file_path, parse_result)


class TestDefinitionCheckerJava:
    """Tests for ADAPTATION_IN_DEFINITION detection in Java files."""

    def setup_method(self):
        self.checker = DefinitionChecker()

    def test_can_check_java_file(self):
        """DefinitionChecker can check .java files."""
        assert self.checker.can_check(Path("LoginTest.java")) is True

    def test_detects_findElement_in_test(self, tmp_path):
        """Detects driver.findElement() in @Test method."""
        code = '''
import org.junit.jupiter.api.Test;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class LoginTest {
    private WebDriver driver;

    @Test
    public void testLogin() {
        driver.findElement(By.id("username")).sendKeys("test");
    }
}
'''
        test_file = tmp_path / "LoginTest.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) >= 1

    def test_detects_driver_get_in_test(self, tmp_path):
        """Detects driver.get() in @Test method."""
        code = '''
import org.junit.jupiter.api.Test;
import org.openqa.selenium.WebDriver;

public class LoginTest {
    private WebDriver driver;

    @Test
    public void testNavigation() {
        driver.get("https://example.com");
    }
}
'''
        test_file = tmp_path / "LoginTest.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) >= 1


class TestAdaptationCheckerJava:
    """Tests for ASSERTION_IN_POM and FORBIDDEN_IMPORT detection in Java files."""

    def setup_method(self):
        self.checker = AdaptationChecker()

    def test_can_check_java_file(self):
        """AdaptationChecker can check .java files."""
        assert self.checker.can_check(Path("LoginPage.java")) is True

    def test_detects_assertion_in_page(self, tmp_path):
        """Detects assertions in Page Object class."""
        code = '''
import org.openqa.selenium.WebDriver;
import org.junit.jupiter.api.Assertions;

public class LoginPage {
    private WebDriver driver;

    public void verifyLogin() {
        Assertions.assertTrue(driver.getCurrentUrl().contains("dashboard"));
    }
}
'''
        test_file = tmp_path / "LoginPage.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        assertion_violations = [v for v in violations
                               if v.violation_type == ViolationType.ASSERTION_IN_POM]
        assert len(assertion_violations) >= 1

    def test_detects_junit_import_in_page(self, tmp_path):
        """Detects JUnit import in Page Object."""
        code = '''
import org.openqa.selenium.WebDriver;
import org.junit.jupiter.api.Assertions;

public class LoginPage {
    private WebDriver driver;

    public void clickLogin() {
        // ...
    }
}
'''
        test_file = tmp_path / "LoginPage.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        forbidden_violations = [v for v in violations
                               if v.violation_type == ViolationType.FORBIDDEN_IMPORT]
        assert len(forbidden_violations) >= 1


class TestQualityCheckerJava:
    """Tests for HARDCODED_TEST_DATA and POOR_TEST_NAMING detection in Java files."""

    def setup_method(self):
        self.checker = QualityChecker()

    def test_can_check_java_file(self):
        """QualityChecker can check .java files."""
        assert self.checker.can_check(Path("LoginTest.java")) is True

    def test_detects_hardcoded_email(self, tmp_path):
        """Detects hardcoded email in test."""
        code = '''
import org.junit.jupiter.api.Test;

public class LoginTest {
    @Test
    public void testLogin() {
        String email = "test@example.com";
    }
}
'''
        test_file = tmp_path / "LoginTest.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        hardcoded_violations = [v for v in violations
                               if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hardcoded_violations) >= 1

    def test_detects_hardcoded_url(self, tmp_path):
        """Detects hardcoded URL in test."""
        code = '''
import org.junit.jupiter.api.Test;

public class LoginTest {
    @Test
    public void testLogin() {
        driver.get("https://example.com/login");
    }
}
'''
        test_file = tmp_path / "LoginTest.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        hardcoded_violations = [v for v in violations
                               if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hardcoded_violations) >= 1

    def test_detects_test1_name(self, tmp_path):
        """Detects generic test1 name."""
        code = '''
import org.junit.jupiter.api.Test;

public class LoginTest {
    @Test
    public void test1() {
        // ...
    }
}
'''
        test_file = tmp_path / "LoginTest.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) >= 1

    def test_good_name_no_violation(self, tmp_path):
        """Descriptive name does not trigger violation."""
        code = '''
import org.junit.jupiter.api.Test;

public class LoginTest {
    @Test
    public void testUserCanLoginWithValidCredentials() {
        // ...
    }
}
'''
        test_file = tmp_path / "LoginTest.java"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) == 0


# =====================================================================
# JavaParser direct tests (coverage for uncovered parser lines)
# =====================================================================


class TestJavaParserClassExtraction:
    """Tests for JavaParser class extraction, including inheritance."""

    def setup_method(self):
        self.parser = JavaParser()

    def test_class_with_extends(self, tmp_path):
        """Class with extends extracts base class."""
        code = '''
public class LoginPage extends BasePage {
    public void clickLogin() {}
}
'''
        f = tmp_path / "LoginPage.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        assert len(result.classes) == 1
        assert "BasePage" in result.classes[0].base_classes
        assert result.classes[0].is_page_object is True

    def test_class_without_extends(self, tmp_path):
        """Class without extends has empty base_classes."""
        code = '''
public class LoginTest {
    public void testLogin() {}
}
'''
        f = tmp_path / "LoginTest.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        assert len(result.classes) == 1
        assert result.classes[0].base_classes == []

    def test_class_methods_extracted(self, tmp_path):
        """Class methods are extracted with names."""
        code = '''
public class LoginPage {
    public void clickLogin() {}
    public void enterEmail(String email) {}
}
'''
        f = tmp_path / "LoginPage.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        methods = result.classes[0].methods
        assert len(methods) == 2
        names = [m.name for m in methods]
        assert "clickLogin" in names
        assert "enterEmail" in names


class TestJavaParserAnnotations:
    """Tests for Java annotation/decorator extraction."""

    def setup_method(self):
        self.parser = JavaParser()

    def test_test_annotation_extracted(self, tmp_path):
        """@Test annotation is captured as decorator."""
        code = '''
import org.junit.jupiter.api.Test;

public class LoginTest {
    @Test
    public void testLogin() {
        System.out.println("test");
    }
}
'''
        f = tmp_path / "LoginTest.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        methods = result.classes[0].methods
        assert len(methods) == 1
        assert "Test" in methods[0].decorators

    def test_method_parameters_extracted(self, tmp_path):
        """Method parameters are correctly extracted."""
        code = '''
public class LoginPage {
    public void login(String user, String pass) {
        System.out.println(user);
    }
}
'''
        f = tmp_path / "LoginPage.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        methods = result.classes[0].methods
        assert len(methods) == 1
        assert "user" in methods[0].parameters


class TestJavaParserCallExtraction:
    """Tests for Java method call extraction."""

    def setup_method(self):
        self.parser = JavaParser()

    def test_simple_method_call(self, tmp_path):
        """Simple object.method() call is extracted."""
        code = '''
public class LoginTest {
    public void testLogin() {
        driver.findElement(null);
    }
}
'''
        f = tmp_path / "LoginTest.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        fe_calls = [c for c in result.calls if "findElement" in c.method_name]
        assert len(fe_calls) >= 1

    def test_chained_method_call(self, tmp_path):
        """Chained driver.findElement().sendKeys() extracts at least one call."""
        code = '''
public class LoginTest {
    public void testLogin() {
        driver.findElement(null).sendKeys("test");
    }
}
'''
        f = tmp_path / "LoginTest.java"
        f.write_text(code, encoding="utf-8")
        result = self.parser.parse_file(f)
        method_names = [c.method_name for c in result.calls]
        # Tree-sitter Java parses chained calls; at least findElement is extracted
        assert "findElement" in method_names


class TestJavaParserUtilityMethods:
    """Tests for JavaParser utility methods."""

    def setup_method(self):
        self.parser = JavaParser()

    def test_is_test_method_with_test(self):
        """Method with @Test is identified as test."""
        func = ParsedFunction(name="testLogin", line_start=1, line_end=5, decorators=["Test"])
        assert self.parser.is_test_method(func) is True

    def test_is_test_method_without_annotation(self):
        """Method without test annotation is not a test."""
        func = ParsedFunction(name="testLogin", line_start=1, line_end=5, decorators=[])
        assert self.parser.is_test_method(func) is False

    def test_is_setup_method(self):
        """Method with @Before is setup."""
        func = ParsedFunction(name="setUp", line_start=1, line_end=5, decorators=["Before"])
        assert self.parser.is_setup_method(func) is True

    def test_is_setup_method_before_each(self):
        """Method with @BeforeEach is setup."""
        func = ParsedFunction(name="setUp", line_start=1, line_end=5, decorators=["BeforeEach"])
        assert self.parser.is_setup_method(func) is True

    def test_is_teardown_method(self):
        """Method with @After is teardown."""
        func = ParsedFunction(name="tearDown", line_start=1, line_end=5, decorators=["After"])
        assert self.parser.is_teardown_method(func) is True

    def test_is_teardown_method_false(self):
        """Method without teardown annotation is not teardown."""
        func = ParsedFunction(name="cleanup", line_start=1, line_end=5, decorators=["Test"])
        assert self.parser.is_teardown_method(func) is False

    def test_has_selenium_imports_true(self):
        """Detects Selenium imports."""
        imports = [ParsedImport(module="org.openqa.selenium.WebDriver", line=1)]
        assert self.parser.has_selenium_imports(imports) is True

    def test_has_selenium_imports_false(self):
        """Non-Selenium imports return False."""
        imports = [ParsedImport(module="org.junit.jupiter.api.Test", line=1)]
        assert self.parser.has_selenium_imports(imports) is False

    def test_has_playwright_imports(self):
        """Detects Playwright imports (rare in Java but supported)."""
        imports = [ParsedImport(module="com.microsoft.playwright.Page", line=1)]
        assert self.parser.has_playwright_imports(imports) is True

    def test_has_test_framework_imports_junit(self):
        """Detects JUnit imports."""
        imports = [ParsedImport(module="org.junit.jupiter.api.Test", line=1)]
        assert self.parser.has_test_framework_imports(imports) is True

    def test_has_test_framework_imports_testng(self):
        """Detects TestNG imports."""
        imports = [ParsedImport(module="org.testng.annotations.Test", line=1)]
        assert self.parser.has_test_framework_imports(imports) is True

    def test_has_test_framework_imports_false(self):
        """Non-test-framework imports return False."""
        imports = [ParsedImport(module="java.util.List", line=1)]
        assert self.parser.has_test_framework_imports(imports) is False
