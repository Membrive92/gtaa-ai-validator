"""
Structure Checker for gTAA Validator.

Validates that the project has proper gTAA layer structure:
- Tests directory (tests/ or test/)
- Page Objects directory (pages/, page_objects/, or pom/)

This is a PROJECT-LEVEL checker — it runs once via check_project(),
not per-file via check().

According to gTAA architecture, projects must have separate directories
for the Definition layer (tests) and the Adaptation layer (Page Objects).
"""

import ast
from pathlib import Path
from typing import List, Optional

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class StructureChecker(BaseChecker):
    """
    Checks project structure for required gTAA directories.

    This checker validates that the project has at least:
    - A test directory (tests/ or test/)
    - A page objects directory (pages/, page_objects/, or pom/)

    If either is missing, it reports a MISSING_LAYER_STRUCTURE violation.
    """

    # Acceptable directory names for each layer
    TEST_DIR_NAMES = {"tests", "test"}
    PAGE_DIR_NAMES = {"pages", "page_objects", "pom"}

    def can_check(self, file_path: Path) -> bool:
        """StructureChecker never runs on individual files."""
        return False

    def check(self, file_path: Path, tree: Optional[ast.Module] = None) -> List[Violation]:
        """Not used — StructureChecker only implements check_project()."""
        return []

    def check_project(self, project_path: Path) -> List[Violation]:
        """
        Check if project has required gTAA directory structure.

        Looks for immediate subdirectories matching expected layer names.
        Creates a single violation listing all missing layers.

        Args:
            project_path: Root directory of the project

        Returns:
            List containing 0 or 1 violation
        """
        try:
            subdirs = {d.name.lower() for d in project_path.iterdir() if d.is_dir()}
        except OSError:
            return []

        has_test_dir = bool(subdirs & self.TEST_DIR_NAMES)
        has_page_dir = bool(subdirs & self.PAGE_DIR_NAMES)

        if has_test_dir and has_page_dir:
            return []

        missing = []
        if not has_test_dir:
            missing.append(
                f"tests directory (expected one of: {', '.join(sorted(self.TEST_DIR_NAMES))})"
            )
        if not has_page_dir:
            missing.append(
                f"page objects directory (expected one of: {', '.join(sorted(self.PAGE_DIR_NAMES))})"
            )

        violation = Violation(
            violation_type=ViolationType.MISSING_LAYER_STRUCTURE,
            severity=Severity.CRITICAL,
            file_path=project_path,
            line_number=None,
            message=(
                f"Project lacks required gTAA directory structure. "
                f"Missing: {'; '.join(missing)}. "
                f"According to gTAA, projects should have separate directories "
                f"for the Definition layer (tests) and the Adaptation layer (Page Objects)."
            ),
            recommendation=ViolationType.MISSING_LAYER_STRUCTURE.get_recommendation(),
        )
        return [violation]
