"""
Adaptation Layer Checker for gTAA Validator.

Checks Page Object files for architectural violations:
- Assertions (should only be in tests)
- Forbidden imports (test frameworks don't belong in Page Objects)
- Business logic (if/else/for/while — should be in a service layer)
- Duplicate locators (same selector in multiple Page Objects)

According to gTAA:
- Page Objects should only interact with the UI
- Page Objects should NOT contain test assertions
- Page Objects should NOT contain complex business logic
- Locators should be centralized and not duplicated
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class AdaptationChecker(BaseChecker):
    """
    Checks Page Object files for gTAA violations.

    Detects:
    - ASSERTION_IN_POM: assert statements inside class methods
    - FORBIDDEN_IMPORT: imports of pytest or unittest
    - BUSINESS_LOGIC_IN_POM: if/for/while inside class methods
    - DUPLICATE_LOCATOR: same locator string in multiple Page Objects
    """

    # Forbidden modules in Page Objects
    FORBIDDEN_MODULES = {"pytest", "unittest"}

    # Regex patterns to extract locator selector values
    LOCATOR_PATTERNS = [
        re.compile(r'By\.\w+,\s*["\']([^"\']+)["\']'),
        re.compile(r'\(By\.\w+,\s*["\']([^"\']+)["\']\)'),
    ]

    def __init__(self):
        super().__init__()
        # Tracks locator → list of files, reset per analysis run
        self._locator_registry: Dict[str, List[Path]] = defaultdict(list)

    def can_check(self, file_path: Path) -> bool:
        """
        True for Page Object files.

        Heuristics:
        - File is inside pages/, page_objects/, or pom/ directory
        - OR filename ends with _page.py or _pom.py
        - AND file is NOT inside a test directory
        """
        if file_path.suffix != ".py":
            return False

        parts_lower = [p.lower() for p in file_path.parts]
        filename = file_path.name.lower()

        in_page_dir = any(
            part in {"pages", "page_objects", "pom"} for part in parts_lower
        )
        is_page_file = filename.endswith("_page.py") or filename.endswith("_pom.py")
        in_test_dir = any(part in {"tests", "test"} for part in parts_lower)

        return (in_page_dir or is_page_file) and not in_test_dir

    def check(self, file_path: Path, tree: Optional[ast.Module] = None) -> List[Violation]:
        """
        Check a Page Object file for violations.

        Runs four sub-checks:
        1. Forbidden imports (pytest, unittest)
        2. Assertions inside class methods
        3. Business logic (if/for/while) inside class methods
        4. Duplicate locators across Page Objects

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

            violations.extend(self._check_forbidden_imports(file_path, tree))
            violations.extend(self._check_assertions(file_path, tree))
            violations.extend(self._check_business_logic(file_path, tree))
            violations.extend(self._check_duplicate_locators(file_path, source_code))

        except SyntaxError:
            pass
        except Exception:
            pass

        return violations

    # ------------------------------------------------------------------
    # Sub-checks
    # ------------------------------------------------------------------

    def _check_forbidden_imports(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detect imports of test frameworks in Page Object files."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.FORBIDDEN_MODULES:
                        violations.append(
                            Violation(
                                violation_type=ViolationType.FORBIDDEN_IMPORT,
                                severity=Severity.HIGH,
                                file_path=file_path,
                                line_number=node.lineno,
                                message=(
                                    f"Page Object imports test framework '{alias.name}'. "
                                    f"Test frameworks should only be imported in test files, "
                                    f"not in the Adaptation layer."
                                ),
                                code_snippet=f"import {alias.name}",
                            )
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module and any(
                    node.module == mod or node.module.startswith(f"{mod}.")
                    for mod in self.FORBIDDEN_MODULES
                ):
                    violations.append(
                        Violation(
                            violation_type=ViolationType.FORBIDDEN_IMPORT,
                            severity=Severity.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            message=(
                                f"Page Object imports from test framework '{node.module}'. "
                                f"Test frameworks should only be imported in test files."
                            ),
                            code_snippet=f"from {node.module} import ...",
                        )
                    )

        return violations

    def _check_assertions(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detect assert statements inside class methods."""
        visitor = _AssertionVisitor(file_path)
        visitor.visit(tree)
        return visitor.violations

    def _check_business_logic(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detect if/for/while inside class methods."""
        visitor = _BusinessLogicVisitor(file_path)
        visitor.visit(tree)
        return visitor.violations

    def _check_duplicate_locators(
        self, file_path: Path, source_code: str
    ) -> List[Violation]:
        """Detect locator strings that appear in multiple Page Object files."""
        violations: List[Violation] = []

        for pattern in self.LOCATOR_PATTERNS:
            for match in pattern.finditer(source_code):
                locator = match.group(1)
                existing = self._locator_registry[locator]

                if existing and file_path not in existing:
                    line_number = source_code[: match.start()].count("\n") + 1
                    other_names = ", ".join(f.name for f in existing)
                    violations.append(
                        Violation(
                            violation_type=ViolationType.DUPLICATE_LOCATOR,
                            severity=Severity.MEDIUM,
                            file_path=file_path,
                            line_number=line_number,
                            message=(
                                f"Locator '{locator}' is duplicated across Page Objects. "
                                f"Also found in: {other_names}. "
                                f"Consider centralizing locators in a base page or repository."
                            ),
                            code_snippet=locator,
                        )
                    )

                if file_path not in existing:
                    existing.append(file_path)

        return violations


# ======================================================================
# AST Visitors
# ======================================================================


class _AssertionVisitor(ast.NodeVisitor):
    """Detects assert statements inside class methods."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: List[Violation] = []
        self._in_class = False
        self._in_method = False

    def visit_ClassDef(self, node: ast.ClassDef):
        prev = self._in_class
        self._in_class = True
        self.generic_visit(node)
        self._in_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._in_class:
            prev = self._in_method
            self._in_method = True
            self.generic_visit(node)
            self._in_method = prev
        else:
            self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert):
        if self._in_class and self._in_method:
            try:
                snippet = ast.unparse(node)
            except AttributeError:
                snippet = "assert ..."
            self.violations.append(
                Violation(
                    violation_type=ViolationType.ASSERTION_IN_POM,
                    severity=Severity.HIGH,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    message=(
                        "Page Object method contains an assertion. "
                        "Assertions belong in the Definition layer (tests), not in Page Objects. "
                        "Return the value and let the test verify it."
                    ),
                    code_snippet=snippet,
                )
            )
        self.generic_visit(node)


class _BusinessLogicVisitor(ast.NodeVisitor):
    """Detects if/for/while inside class methods."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: List[Violation] = []
        self._in_class = False
        self._in_method = False

    def visit_ClassDef(self, node: ast.ClassDef):
        prev = self._in_class
        self._in_class = True
        self.generic_visit(node)
        self._in_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._in_class:
            prev = self._in_method
            self._in_method = True
            self.generic_visit(node)
            self._in_method = prev
        else:
            self.generic_visit(node)

    def _add_violation(self, node: ast.AST, construct: str):
        self.violations.append(
            Violation(
                violation_type=ViolationType.BUSINESS_LOGIC_IN_POM,
                severity=Severity.MEDIUM,
                file_path=self.file_path,
                line_number=node.lineno,
                message=(
                    f"Page Object method contains {construct}. "
                    f"Complex logic should be in a separate service layer, "
                    f"not in Page Objects."
                ),
                code_snippet=f"{construct} statement",
            )
        )

    def visit_If(self, node: ast.If):
        if self._in_class and self._in_method:
            self._add_violation(node, "if/else")
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        if self._in_class and self._in_method:
            self._add_violation(node, "for loop")
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        if self._in_class and self._in_method:
            self._add_violation(node, "while loop")
        self.generic_visit(node)
