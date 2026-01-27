"""
Shared fixtures for gTAA Validator tests.

Provides reusable test data: sample violations, reports, and file paths.
"""

import pytest
from pathlib import Path

from gtaa_validator.models import Violation, Report, Severity, ViolationType


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def project_root():
    """Return the absolute path to the gtaa-ai-validator project root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def bad_project_path(project_root):
    """Path to examples/bad_project."""
    return project_root / "examples" / "bad_project"


@pytest.fixture
def good_project_path(project_root):
    """Path to examples/good_project."""
    return project_root / "examples" / "good_project"


# ---------------------------------------------------------------------------
# Sample violations
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_critical_violation():
    """A single CRITICAL violation."""
    return Violation(
        violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
        severity=Severity.CRITICAL,
        file_path=Path("tests/test_login.py"),
        line_number=24,
        message="Test calls driver.find_element() directly",
        code_snippet="driver.find_element(By.ID, 'username')",
    )


@pytest.fixture
def sample_high_violation():
    """A single HIGH violation."""
    return Violation(
        violation_type=ViolationType.HARDCODED_TEST_DATA,
        severity=Severity.HIGH,
        file_path=Path("tests/test_login.py"),
        line_number=10,
        message="Hardcoded email in test",
        code_snippet='email = "user@test.com"',
    )


@pytest.fixture
def sample_medium_violation():
    """A single MEDIUM violation."""
    return Violation(
        violation_type=ViolationType.LONG_TEST_FUNCTION,
        severity=Severity.MEDIUM,
        file_path=Path("tests/test_checkout.py"),
        line_number=1,
        message="Test function is 80 lines long",
    )


@pytest.fixture
def sample_low_violation():
    """A single LOW violation."""
    return Violation(
        violation_type=ViolationType.POOR_TEST_NAMING,
        severity=Severity.LOW,
        file_path=Path("tests/test_misc.py"),
        line_number=5,
        message="Generic test name: test_1",
    )


@pytest.fixture
def mixed_violations(
    sample_critical_violation,
    sample_high_violation,
    sample_medium_violation,
    sample_low_violation,
):
    """List with one violation of each severity level."""
    return [
        sample_critical_violation,
        sample_high_violation,
        sample_medium_violation,
        sample_low_violation,
    ]


# ---------------------------------------------------------------------------
# Sample reports
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_report():
    """Report with no violations (score should be 100)."""
    return Report(
        project_path=Path("/fake/project"),
        violations=[],
        files_analyzed=5,
    )


@pytest.fixture
def mixed_report(mixed_violations):
    """Report with one violation of each severity."""
    report = Report(
        project_path=Path("/fake/project"),
        violations=mixed_violations,
        files_analyzed=10,
    )
    report.calculate_score()
    return report


# ---------------------------------------------------------------------------
# Temporary test files (for DefinitionChecker tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def write_py_file(tmp_path):
    """
    Factory fixture that writes a Python file and returns its path.

    Usage:
        path = write_py_file("test_example.py", "def test_foo(): pass")
    """
    def _write(filename: str, content: str) -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _write
