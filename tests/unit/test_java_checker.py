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
        assert len(adaptation_violations) > 0

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
        assert len(adaptation_violations) > 0


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
        assert len(assertion_violations) > 0

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
        assert len(forbidden_violations) > 0


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
        assert len(hardcoded_violations) > 0

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
        assert len(hardcoded_violations) > 0

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
        assert len(naming_violations) > 0

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
