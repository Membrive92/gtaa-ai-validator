"""
Base class for all gTAA violation checkers.

This module defines the abstract base class that all checkers must inherit from.
It implements the Strategy Pattern, allowing the analyzer to execute different
checking strategies without knowing the implementation details.

Key concepts:
- Abstract Base Class (ABC): Enforces that subclasses implement required methods
- Strategy Pattern: Encapsulates different algorithms (checkers) behind a common interface
- Template Method: Defines the skeleton of check() that subclasses implement
"""

import ast
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from gtaa_validator.models import Violation


class BaseChecker(ABC):
    """
    Abstract base class for all gTAA violation checkers.

    All checkers must inherit from this class and implement the check() method.
    The check() method receives a file path and returns a list of violations found.

    Subclasses:
    - DefinitionChecker: Checks test files for violations (Phase 2)
    - StructureChecker: Validates project structure (Phase 3)
    - AdaptationChecker: Validates Page Objects (Phase 3)
    - QualityChecker: General code quality checks (Phase 3)

    Usage:
        class MyChecker(BaseChecker):
            def check(self, file_path: Path) -> List[Violation]:
                # Implementation here
                return violations
    """

    def __init__(self):
        """Initialize the checker."""
        self.name = self.__class__.__name__

    @abstractmethod
    def check(self, file_path: Path, tree: Optional[ast.Module] = None) -> List[Violation]:
        """
        Check a file for gTAA violations.

        This is the main method that must be implemented by all subclasses.
        It analyzes a single file and returns a list of violations found.

        Args:
            file_path: Path to the file to check
            tree: Pre-parsed AST tree (optional). If provided, the checker
                  should use it instead of parsing the file again.

        Returns:
            List of Violation objects found in the file (empty list if no violations)

        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        pass

    def check_project(self, project_path: Path) -> List[Violation]:
        """
        Check project-level violations (e.g., missing directory structure).

        Override this method for checkers that analyze the entire project
        rather than individual files. Default returns empty list.

        Args:
            project_path: Root directory of the project

        Returns:
            List of Violation objects (empty by default)
        """
        return []

    def can_check(self, file_path: Path) -> bool:
        """
        Determine if this checker can analyze the given file.

        Override this method if the checker should only run on specific file types.
        Default implementation returns True for all Python files.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this checker can analyze the file, False otherwise

        Example:
            def can_check(self, file_path: Path) -> bool:
                # Only check files in tests/ directory
                return "tests" in file_path.parts
        """
        return file_path.suffix == ".py"

    def __repr__(self) -> str:
        """String representation of the checker."""
        return f"<{self.name}>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.name
