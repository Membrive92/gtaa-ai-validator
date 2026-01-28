"""
Tests for gtaa_validator.checkers.structure_checker

Covers:
- can_check() always returns False (project-level only)
- check_project() detects missing directories
- Handles alternate directory names (test/, page_objects/, pom/)
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.structure_checker import StructureChecker
from gtaa_validator.models import ViolationType, Severity


@pytest.fixture
def checker():
    return StructureChecker()


# =========================================================================
# can_check — always False
# =========================================================================

class TestCanCheck:
    """StructureChecker never operates on individual files."""

    def test_returns_false_for_test_file(self, checker):
        assert checker.can_check(Path("test_login.py")) is False

    def test_returns_false_for_page_file(self, checker):
        assert checker.can_check(Path("pages/login_page.py")) is False

    def test_returns_false_for_any_py(self, checker):
        assert checker.can_check(Path("anything.py")) is False


# =========================================================================
# check_project — directory structure validation
# =========================================================================

class TestCheckProject:
    """Tests for project structure validation."""

    def test_valid_tests_and_pages(self, checker, tmp_path):
        """Both tests/ and pages/ present → 0 violations."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "pages").mkdir()
        assert checker.check_project(tmp_path) == []

    def test_valid_test_and_page_objects(self, checker, tmp_path):
        """test/ and page_objects/ are also valid names."""
        (tmp_path / "test").mkdir()
        (tmp_path / "page_objects").mkdir()
        assert checker.check_project(tmp_path) == []

    def test_valid_with_pom(self, checker, tmp_path):
        """pom/ is an accepted page objects directory name."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "pom").mkdir()
        assert checker.check_project(tmp_path) == []

    def test_missing_test_dir(self, checker, tmp_path):
        """Only pages/ → 1 CRITICAL violation mentioning tests."""
        (tmp_path / "pages").mkdir()
        violations = checker.check_project(tmp_path)
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.MISSING_LAYER_STRUCTURE
        assert violations[0].severity == Severity.CRITICAL
        assert "test" in violations[0].message.lower()

    def test_missing_page_dir(self, checker, tmp_path):
        """Only tests/ → 1 CRITICAL violation mentioning pages."""
        (tmp_path / "tests").mkdir()
        violations = checker.check_project(tmp_path)
        assert len(violations) == 1
        assert "page" in violations[0].message.lower()

    def test_missing_both(self, checker, tmp_path):
        """Empty project → 1 violation mentioning both layers."""
        violations = checker.check_project(tmp_path)
        assert len(violations) == 1
        msg = violations[0].message.lower()
        assert "test" in msg
        assert "page" in msg

    def test_good_project_passes(self, checker, good_project_path):
        """examples/good_project has tests/ and pages/."""
        assert checker.check_project(good_project_path) == []

    def test_violation_has_no_line_number(self, checker, tmp_path):
        """Project-level violations have line_number=None."""
        violations = checker.check_project(tmp_path)
        assert violations[0].line_number is None
