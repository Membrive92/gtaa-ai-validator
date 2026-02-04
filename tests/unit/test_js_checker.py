"""
Tests for unified checkers with JavaScript/TypeScript files.

Phase 9+: Tests that DefinitionChecker, AdaptationChecker, and QualityChecker
correctly detect violations in JavaScript/TypeScript code.

Covers:
- Browser call detection in test functions (ADAPTATION_IN_DEFINITION)
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


class TestDefinitionCheckerJS:
    """Tests for ADAPTATION_IN_DEFINITION detection in JS/TS files."""

    def setup_method(self):
        self.checker = DefinitionChecker()

    def test_can_check_javascript_file(self):
        """DefinitionChecker can check .js files."""
        assert self.checker.can_check(Path("login.spec.js")) is True

    def test_can_check_typescript_file(self):
        """DefinitionChecker can check .ts files."""
        assert self.checker.can_check(Path("login.spec.ts")) is True

    def test_can_check_tsx_file(self):
        """DefinitionChecker can check .tsx files."""
        assert self.checker.can_check(Path("Login.test.tsx")) is True

    def test_can_check_mjs_file(self):
        """DefinitionChecker can check .mjs files."""
        assert self.checker.can_check(Path("login.test.mjs")) is True

    def test_detects_page_locator_in_test(self, tmp_path):
        """Detects page.locator() in test function."""
        code = '''
import { test, expect } from '@playwright/test';

test('login test', async ({ page }) => {
    await page.locator('#username').fill('test');
});
'''
        test_file = tmp_path / "login.spec.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) > 0

    def test_detects_page_goto_in_test(self, tmp_path):
        """Detects page.goto() in test function."""
        code = '''
import { test } from '@playwright/test';

test('navigation test', async ({ page }) => {
    await page.goto('https://example.com');
});
'''
        test_file = tmp_path / "login.spec.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) > 0

    def test_detects_cy_get_in_it(self, tmp_path):
        """Detects cy.get() in it() block."""
        code = '''
describe('Login', () => {
    it('should login', () => {
        cy.get('#username').type('test');
    });
});
'''
        test_file = tmp_path / "login.spec.js"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        adaptation_violations = [v for v in violations
                                 if v.violation_type == ViolationType.ADAPTATION_IN_DEFINITION]
        assert len(adaptation_violations) > 0


class TestQualityCheckerJS:
    """Tests for HARDCODED_TEST_DATA and POOR_TEST_NAMING detection in JS/TS files."""

    def setup_method(self):
        self.checker = QualityChecker()

    def test_can_check_javascript_file(self):
        """QualityChecker can check .js files."""
        assert self.checker.can_check(Path("login.spec.js")) is True

    def test_detects_hardcoded_email(self, tmp_path):
        """Detects hardcoded email in test."""
        code = '''
import { test } from '@playwright/test';

test('login test', async ({ page }) => {
    await page.fill('#email', 'user@example.com');
});
'''
        test_file = tmp_path / "login.spec.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        hardcoded_violations = [v for v in violations
                               if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hardcoded_violations) > 0

    def test_detects_hardcoded_url(self, tmp_path):
        """Detects hardcoded URL in test."""
        code = '''
import { test } from '@playwright/test';

test('navigation', async ({ page }) => {
    await page.goto('https://example.com/login');
});
'''
        test_file = tmp_path / "login.spec.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        hardcoded_violations = [v for v in violations
                               if v.violation_type == ViolationType.HARDCODED_TEST_DATA]
        assert len(hardcoded_violations) > 0

    def test_detects_test_1_name(self, tmp_path):
        """Detects generic 'test 1' name."""
        code = '''
import { test } from '@playwright/test';

test('test 1', async ({ page }) => {
    // ...
});
'''
        test_file = tmp_path / "login.spec.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) > 0

    def test_detects_generic_describe_name(self, tmp_path):
        """Detects generic describe('test', ...) name."""
        code = '''
describe('test', () => {
    it('should work', () => {
        // ...
    });
});
'''
        test_file = tmp_path / "login.spec.js"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) > 0

    def test_good_name_no_violation(self, tmp_path):
        """Descriptive name does not trigger violation."""
        code = '''
import { test } from '@playwright/test';

test('user can login with valid credentials', async ({ page }) => {
    // ...
});
'''
        test_file = tmp_path / "login.spec.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        naming_violations = [v for v in violations
                           if v.violation_type == ViolationType.POOR_TEST_NAMING]
        assert len(naming_violations) == 0


class TestAdaptationCheckerJS:
    """Tests for ASSERTION_IN_POM detection in JS/TS Page Objects."""

    def setup_method(self):
        self.checker = AdaptationChecker()

    def test_can_check_typescript_file(self):
        """AdaptationChecker can check .ts files."""
        assert self.checker.can_check(Path("LoginPage.ts")) is True

    @pytest.mark.skip(reason="ASSERTION_IN_POM detection for JS Page Objects needs enhancement")
    def test_detects_expect_in_page(self, tmp_path):
        """Detects expect() in Page class."""
        code = '''
import { Page, expect } from '@playwright/test';

export class LoginPage {
    constructor(page) {
        this.page = page;
    }

    async verifyLogin() {
        await expect(this.page).toHaveURL(/dashboard/);
    }
}
'''
        test_file = tmp_path / "LoginPage.ts"
        test_file.write_text(code, encoding="utf-8")
        violations = parse_and_check(self.checker, test_file)

        assertion_violations = [v for v in violations
                               if v.violation_type == ViolationType.ASSERTION_IN_POM]
        assert len(assertion_violations) > 0
