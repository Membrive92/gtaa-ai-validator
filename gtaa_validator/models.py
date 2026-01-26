"""
Data models for gTAA Validator.

This module defines the core data structures used throughout the validation process:
- Violation: Represents a single architectural violation found in the code
- Report: Aggregates all violations and metadata for a project analysis
- Severity: Enumeration of violation severity levels
- ViolationType: Enumeration of gTAA violation types

These models are used by analyzers, checkers, and reporters.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class Severity(Enum):
    """
    Severity levels for gTAA architectural violations.

    CRITICAL: Violates core gTAA principles (e.g., direct Selenium calls in tests)
    HIGH: Significant architectural issue (e.g., hardcoded test data)
    MEDIUM: Moderate quality issue (e.g., business logic in page objects)
    LOW: Minor code quality issue (e.g., poor naming conventions)
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def get_score_penalty(self) -> int:
        """
        Return the score penalty for this severity level.
        Used to calculate the overall compliance score (0-100).
        """
        penalties = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        return penalties[self]

    def __lt__(self, other):
        """Enable sorting by severity (CRITICAL > HIGH > MEDIUM > LOW)."""
        if not isinstance(other, Severity):
            return NotImplemented
        severity_order = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        return severity_order[self] < severity_order[other]


class ViolationType(Enum):
    """
    Types of gTAA architectural violations.

    Each violation type corresponds to a specific gTAA principle:
    - Layer separation (Definition, Adaptation, Execution)
    - Data externalization
    - Code quality and maintainability

    PHASE 2: Only ADAPTATION_IN_DEFINITION is implemented
    PHASE 3: All violation types will be detected
    """

    # CRITICAL violations - Core gTAA principles
    ADAPTATION_IN_DEFINITION = "ADAPTATION_IN_DEFINITION"  # Selenium/Playwright in test files
    MISSING_LAYER_STRUCTURE = "MISSING_LAYER_STRUCTURE"    # Missing tests/, pages/ directories

    # HIGH severity violations
    HARDCODED_TEST_DATA = "HARDCODED_TEST_DATA"            # Emails, URLs hardcoded in tests
    ASSERTION_IN_POM = "ASSERTION_IN_POM"                  # Assertions in Page Object Methods
    FORBIDDEN_IMPORT = "FORBIDDEN_IMPORT"                  # Wrong layer imports

    # MEDIUM severity violations
    BUSINESS_LOGIC_IN_POM = "BUSINESS_LOGIC_IN_POM"        # Business logic in Page Objects
    DUPLICATE_LOCATOR = "DUPLICATE_LOCATOR"                # Same locator in multiple places
    LONG_TEST_FUNCTION = "LONG_TEST_FUNCTION"              # Tests >50 lines

    # LOW severity violations
    POOR_TEST_NAMING = "POOR_TEST_NAMING"                  # Generic test names (test_1, test_2)

    def get_severity(self) -> Severity:
        """Return the severity level for this violation type."""
        severity_map = {
            # Critical
            ViolationType.ADAPTATION_IN_DEFINITION: Severity.CRITICAL,
            ViolationType.MISSING_LAYER_STRUCTURE: Severity.CRITICAL,

            # High
            ViolationType.HARDCODED_TEST_DATA: Severity.HIGH,
            ViolationType.ASSERTION_IN_POM: Severity.HIGH,
            ViolationType.FORBIDDEN_IMPORT: Severity.HIGH,

            # Medium
            ViolationType.BUSINESS_LOGIC_IN_POM: Severity.MEDIUM,
            ViolationType.DUPLICATE_LOCATOR: Severity.MEDIUM,
            ViolationType.LONG_TEST_FUNCTION: Severity.MEDIUM,

            # Low
            ViolationType.POOR_TEST_NAMING: Severity.LOW,
        }
        return severity_map[self]

    def get_description(self) -> str:
        """Return a human-readable description of this violation type."""
        descriptions = {
            ViolationType.ADAPTATION_IN_DEFINITION:
                "Test code directly calls Selenium/Playwright instead of using Page Objects",
            ViolationType.MISSING_LAYER_STRUCTURE:
                "Project lacks proper gTAA layer structure (tests/, pages/ directories)",
            ViolationType.HARDCODED_TEST_DATA:
                "Test data is hardcoded instead of externalized in data files",
            ViolationType.ASSERTION_IN_POM:
                "Page Object contains assertions (should only be in test layer)",
            ViolationType.FORBIDDEN_IMPORT:
                "File imports from forbidden layer (violates layer separation)",
            ViolationType.BUSINESS_LOGIC_IN_POM:
                "Page Object contains business logic (should be in separate layer)",
            ViolationType.DUPLICATE_LOCATOR:
                "Same locator defined in multiple Page Objects",
            ViolationType.LONG_TEST_FUNCTION:
                "Test function is too long (>50 lines), reducing maintainability",
            ViolationType.POOR_TEST_NAMING:
                "Test function has generic name (test_1, test_2, etc.)",
        }
        return descriptions[self]

    def get_recommendation(self) -> str:
        """Return a recommendation on how to fix this violation."""
        recommendations = {
            ViolationType.ADAPTATION_IN_DEFINITION:
                "Create Page Objects that encapsulate Selenium/Playwright interactions. "
                "Test code should call page.login() instead of driver.find_element().",
            ViolationType.MISSING_LAYER_STRUCTURE:
                "Organize project with: tests/ (test definitions), pages/ (page objects), "
                "data/ (test data), utils/ (helpers).",
            ViolationType.HARDCODED_TEST_DATA:
                "Move test data to external files (JSON, YAML, CSV) or test fixtures. "
                "Keep tests DRY and data-driven.",
            ViolationType.ASSERTION_IN_POM:
                "Remove assertions from Page Objects. Page Objects should only interact "
                "with UI and return data. Let tests verify the data.",
            ViolationType.FORBIDDEN_IMPORT:
                "Follow gTAA layer separation: Tests import Pages, Pages import Utils, "
                "but never the reverse.",
            ViolationType.BUSINESS_LOGIC_IN_POM:
                "Extract business logic to separate service/helper classes. "
                "Page Objects should only handle UI interactions.",
            ViolationType.DUPLICATE_LOCATOR:
                "Create a base page class or locator repository. Define each locator once "
                "and reuse across Page Objects.",
            ViolationType.LONG_TEST_FUNCTION:
                "Break long tests into smaller, focused test functions. Each test should "
                "verify one specific behavior.",
            ViolationType.POOR_TEST_NAMING:
                "Use descriptive test names: test_user_can_login_with_valid_credentials() "
                "instead of test_1().",
        }
        return recommendations[self]


@dataclass
class Violation:
    """
    Represents a single gTAA architectural violation detected in the code.

    Attributes:
        violation_type: Type of violation (enum)
        severity: Severity level (enum)
        file_path: Path to the file containing the violation
        line_number: Line number where violation occurs (if applicable)
        message: Detailed message explaining the violation
        code_snippet: Optional code snippet showing the violation
        recommendation: How to fix this violation
    """
    violation_type: ViolationType
    severity: Severity
    file_path: Path
    line_number: Optional[int] = None
    message: str = ""
    code_snippet: Optional[str] = None
    recommendation: str = ""

    def __post_init__(self):
        """
        Auto-populate fields from violation type if not provided.
        This ensures consistency across all violations.
        """
        # If severity not explicitly set, get from violation type
        if not self.severity:
            self.severity = self.violation_type.get_severity()

        # If recommendation not provided, get default recommendation
        if not self.recommendation:
            self.recommendation = self.violation_type.get_recommendation()

        # If message not provided, use violation description
        if not self.message:
            self.message = self.violation_type.get_description()

    def to_dict(self) -> dict:
        """Convert violation to dictionary for JSON serialization."""
        return {
            "type": self.violation_type.name,
            "severity": self.severity.value,
            "file": str(self.file_path),
            "line": self.line_number,
            "message": self.message,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation
        }


@dataclass
class Report:
    """
    Aggregates all violations and metadata for a complete project analysis.

    Attributes:
        project_path: Root directory of the analyzed project
        violations: List of all detected violations
        files_analyzed: Number of files analyzed
        timestamp: When the analysis was performed
        validator_version: Version of gTAA Validator used
        score: Compliance score (0-100)
        execution_time_seconds: Time taken for analysis
    """
    project_path: Path
    violations: List[Violation] = field(default_factory=list)
    files_analyzed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    validator_version: str = "0.1.0"
    score: float = 100.0
    execution_time_seconds: float = 0.0

    def calculate_score(self) -> float:
        """
        Calculate compliance score (0-100) based on violations.

        Formula: Start at 100, subtract penalty for each violation.
        Minimum score is 0.
        """
        total_penalty = sum(v.severity.get_score_penalty() for v in self.violations)
        score = max(0.0, 100.0 - total_penalty)
        self.score = score
        return score

    def get_violations_by_severity(self, severity: Severity) -> List[Violation]:
        """Get all violations of a specific severity level."""
        return [v for v in self.violations if v.severity == severity]

    def get_violation_count_by_severity(self) -> dict:
        """Return count of violations grouped by severity."""
        return {
            "CRITICAL": len(self.get_violations_by_severity(Severity.CRITICAL)),
            "HIGH": len(self.get_violations_by_severity(Severity.HIGH)),
            "MEDIUM": len(self.get_violations_by_severity(Severity.MEDIUM)),
            "LOW": len(self.get_violations_by_severity(Severity.LOW)),
        }

    def to_dict(self) -> dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            "metadata": {
                "project_path": str(self.project_path),
                "timestamp": self.timestamp.isoformat(),
                "validator_version": self.validator_version,
                "execution_time_seconds": self.execution_time_seconds,
            },
            "summary": {
                "files_analyzed": self.files_analyzed,
                "total_violations": len(self.violations),
                "violations_by_severity": self.get_violation_count_by_severity(),
                "score": self.score,
            },
            "violations": [v.to_dict() for v in self.violations]
        }
