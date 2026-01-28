"""
Quality Checker for gTAA Validator.

Checks test files for code quality issues:
- Hardcoded test data (emails, URLs, phone numbers, passwords)
- Long test functions (>50 lines)
- Poor test naming conventions (test_1, test_2, test_a)

These violations indicate poor maintainability and test design,
even if they don't directly break gTAA layer separation.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class QualityChecker(BaseChecker):
    """
    Checks test files for quality issues.

    Detects:
    - HARDCODED_TEST_DATA: emails, URLs, phones, passwords in test code
    - LONG_TEST_FUNCTION: test functions exceeding MAX_TEST_LINES
    - POOR_TEST_NAMING: generic names like test_1, test_a
    """

    # Regex patterns for hardcoded data
    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )
    URL_PATTERN = re.compile(r"https?://[^\s\"']+")
    PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")

    # Keywords that suggest a password string
    PASSWORD_KEYWORDS = {"password", "passwd", "pwd"}

    # Generic test name patterns
    GENERIC_NAME_RE = re.compile(
        r"^test_[0-9]+$|^test_[a-z]$|^test_case[0-9]*$"
    )

    MAX_TEST_LINES = 50

    def can_check(self, file_path: Path) -> bool:
        """
        True for test files (same heuristic as DefinitionChecker).
        """
        if file_path.suffix != ".py":
            return False

        filename = file_path.name
        return (
            filename.startswith("test_")
            or filename.endswith("_test.py")
            or any(part in ("test", "tests") for part in file_path.parts)
        )

    def check(self, file_path: Path, tree: Optional[ast.Module] = None) -> List[Violation]:
        """
        Check a test file for quality violations.

        Args:
            file_path: Path to the file to check
            tree: Pre-parsed AST tree (optional)
        """
        violations: List[Violation] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            if tree is None:
                tree = ast.parse(source_code, filename=str(file_path))

            violations.extend(self._check_hardcoded_data(file_path, tree))
            violations.extend(self._check_long_functions(file_path, tree))
            violations.extend(self._check_test_naming(file_path, tree))

        except SyntaxError:
            pass
        except Exception:
            pass

        return violations

    # ------------------------------------------------------------------
    # Sub-checks
    # ------------------------------------------------------------------

    def _check_hardcoded_data(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detect hardcoded test data (emails, URLs, phones, passwords)."""
        visitor = _HardcodedDataVisitor(file_path)
        visitor.visit(tree)
        return visitor.violations

    def _check_long_functions(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detect test functions longer than MAX_TEST_LINES."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
                continue

            # Collect all line numbers inside the function to measure span
            lines = set()
            for child in ast.walk(node):
                if hasattr(child, "lineno"):
                    lines.add(child.lineno)
                if hasattr(child, "end_lineno") and child.end_lineno:
                    lines.add(child.end_lineno)

            if not lines:
                continue

            length = max(lines) - min(lines) + 1
            if length > self.MAX_TEST_LINES:
                violations.append(
                    Violation(
                        violation_type=ViolationType.LONG_TEST_FUNCTION,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=(
                            f"Test function '{node.name}' is {length} lines long "
                            f"(limit: {self.MAX_TEST_LINES}). "
                            f"Long tests are hard to understand and maintain. "
                            f"Consider splitting into smaller, focused tests."
                        ),
                        code_snippet=f"def {node.name}(...):",
                    )
                )

        return violations

    def _check_test_naming(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detect generic / non-descriptive test function names."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
                continue

            if self.GENERIC_NAME_RE.match(node.name):
                violations.append(
                    Violation(
                        violation_type=ViolationType.POOR_TEST_NAMING,
                        severity=Severity.LOW,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=(
                            f"Test has generic name '{node.name}'. "
                            f"Use descriptive names like "
                            f"'test_user_can_login_with_valid_credentials' "
                            f"instead of '{node.name}'."
                        ),
                        code_snippet=f"def {node.name}(...):",
                    )
                )

        return violations


# ======================================================================
# AST Visitor
# ======================================================================


class _HardcodedDataVisitor(ast.NodeVisitor):
    """Detects hardcoded test data inside test functions."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: List[Violation] = []
        self._in_test = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name.startswith("test_"):
            prev = self._in_test
            self._in_test = True
            self.generic_visit(node)
            self._in_test = prev
        else:
            self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        """Check string constants (Python 3.8+)."""
        if self._in_test and isinstance(node.value, str):
            self._check_string(node.value, node.lineno)
        self.generic_visit(node)

    # Python 3.7 compat
    visit_Str = visit_Constant

    def _check_string(self, value: str, lineno: int):
        # Skip very short strings (likely locator IDs, single words)
        if len(value) < 5:
            return

        if QualityChecker.EMAIL_PATTERN.search(value):
            self._add(lineno, f"Hardcoded email found: '{value}'", value)

        if QualityChecker.URL_PATTERN.search(value):
            self._add(lineno, f"Hardcoded URL found: '{value}'", value)

        if QualityChecker.PHONE_PATTERN.search(value):
            self._add(lineno, f"Hardcoded phone number found: '{value}'", value)

        value_lower = value.lower()
        for kw in QualityChecker.PASSWORD_KEYWORDS:
            if kw in value_lower:
                self._add(
                    lineno,
                    "Hardcoded password-like string found in test.",
                    value,
                )
                break

    def _add(self, lineno: int, message: str, value: str):
        self.violations.append(
            Violation(
                violation_type=ViolationType.HARDCODED_TEST_DATA,
                severity=Severity.HIGH,
                file_path=self.file_path,
                line_number=lineno,
                message=f"{message} Test data should be externalized to fixtures or data files.",
                code_snippet=f'"{value}"',
            )
        )
