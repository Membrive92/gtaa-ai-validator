"""
Static Analyzer for gTAA Validator.

This module orchestrates static analysis of test automation projects.
It coordinates multiple checkers, aggregates results, and produces a Report.

The StaticAnalyzer implements the Facade Pattern: it provides a simple
interface (analyze() method) to a complex subsystem of checkers.

Key responsibilities:
- Discover Python files in the project
- Run appropriate checkers on each file
- Aggregate violations from all checkers
- Calculate compliance score
- Generate final Report

Usage:
    analyzer = StaticAnalyzer(project_path)
    report = analyzer.analyze()
    print(f"Score: {report.score}")
"""

import time
from pathlib import Path
from typing import List

from gtaa_validator.models import Report, Violation
from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.checkers.definition_checker import DefinitionChecker

# Phase 3: Additional checkers will be imported
# from gtaa_validator.checkers.structure_checker import StructureChecker
# from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
# from gtaa_validator.checkers.quality_checker import QualityChecker


class StaticAnalyzer:
    """
    Orchestrates static analysis of a test automation project.

    The analyzer:
    1. Discovers all Python files in the project
    2. Filters files based on checker capabilities
    3. Runs each checker on applicable files
    4. Aggregates all violations
    5. Calculates compliance score
    6. Returns a complete Report

    Attributes:
        project_path: Root directory of the project to analyze
        checkers: List of checker instances to run
        verbose: Whether to print detailed progress information
    """

    def __init__(self, project_path: Path, verbose: bool = False):
        """
        Initialize the StaticAnalyzer.

        Args:
            project_path: Path to the project root directory
            verbose: If True, print detailed analysis progress
        """
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        self.checkers: List[BaseChecker] = self._initialize_checkers()

    def _initialize_checkers(self) -> List[BaseChecker]:
        """
        Initialize all available checkers.

        Phase 2: Only DefinitionChecker
        Phase 3: Will add StructureChecker, AdaptationChecker, QualityChecker

        Returns:
            List of initialized checker instances
        """
        checkers = [
            DefinitionChecker(),
            # StructureChecker(),      # Phase 3
            # AdaptationChecker(),     # Phase 3
            # QualityChecker(),        # Phase 3
        ]

        if self.verbose:
            checker_names = [c.name for c in checkers]
            print(f"Initialized {len(checkers)} checkers: {', '.join(checker_names)}")

        return checkers

    def analyze(self) -> Report:
        """
        Perform complete static analysis of the project.

        This is the main entry point for static analysis.
        It orchestrates the entire checking process and returns a Report.

        Returns:
            Report object containing all violations and metadata

        Example:
            analyzer = StaticAnalyzer(Path("./my-project"))
            report = analyzer.analyze()
            print(f"Found {len(report.violations)} violations")
            print(f"Score: {report.score}/100")
        """
        start_time = time.time()

        if self.verbose:
            print(f"\nStarting static analysis of: {self.project_path}")
            print("="*60)

        # Initialize report
        report = Report(
            project_path=self.project_path,
            violations=[],
            files_analyzed=0
        )

        # Discover all Python files
        python_files = self._discover_python_files()

        if self.verbose:
            print(f"\nFound {len(python_files)} Python files")

        # Analyze each file with applicable checkers
        for file_path in python_files:
            if self.verbose:
                relative_path = self._get_relative_path(file_path)
                print(f"  Checking: {relative_path}")

            file_violations = self._check_file(file_path)
            report.violations.extend(file_violations)
            report.files_analyzed += 1

        # Calculate score based on violations
        report.calculate_score()

        # Record execution time
        report.execution_time_seconds = time.time() - start_time

        if self.verbose:
            print("\n" + "="*60)
            print("Analysis complete!")
            print(f"Files analyzed: {report.files_analyzed}")
            print(f"Violations found: {len(report.violations)}")
            print(f"Score: {report.score:.1f}/100")
            print(f"Time: {report.execution_time_seconds:.2f}s")

        return report

    def _discover_python_files(self) -> List[Path]:
        """
        Discover all Python files in the project.

        Uses recursive glob to find all .py files, excluding common
        directories that should not be analyzed (venv, .git, etc.)

        Returns:
            List of Path objects for all Python files
        """
        # Directories to exclude from analysis
        exclude_dirs = {
            "venv", "env", "ENV", ".venv",  # Virtual environments
            ".git", ".hg", ".svn",           # Version control
            "__pycache__",                    # Python cache
            "node_modules",                   # JavaScript dependencies
            ".pytest_cache", ".tox",         # Testing artifacts
            "build", "dist", "*.egg-info",   # Build artifacts
        }

        python_files = []

        for py_file in self.project_path.rglob("*.py"):
            # Check if file is in an excluded directory
            should_exclude = any(
                excluded in py_file.parts
                for excluded in exclude_dirs
            )

            if not should_exclude:
                python_files.append(py_file)

        # Sort for consistent ordering
        python_files.sort()

        return python_files

    def _check_file(self, file_path: Path) -> List[Violation]:
        """
        Run all applicable checkers on a single file.

        For each checker, first check if it can analyze this file type,
        then run the checker if applicable.

        Args:
            file_path: Path to the file to check

        Returns:
            List of all violations found by all checkers
        """
        violations = []

        for checker in self.checkers:
            # Check if this checker can analyze this file
            if checker.can_check(file_path):
                try:
                    # Run the checker
                    checker_violations = checker.check(file_path)
                    violations.extend(checker_violations)

                    if self.verbose and checker_violations:
                        print(f"    [{checker.name}] Found {len(checker_violations)} violation(s)")

                except Exception as e:
                    # Don't crash if a single checker fails
                    if self.verbose:
                        print(f"    [{checker.name}] Error: {str(e)}")

        return violations

    def _get_relative_path(self, file_path: Path) -> Path:
        """
        Get path relative to project root.

        Args:
            file_path: Absolute path to file

        Returns:
            Path relative to project root
        """
        try:
            return file_path.relative_to(self.project_path)
        except ValueError:
            return file_path

    def get_summary(self) -> dict:
        """
        Get a summary of the analyzer configuration.

        Returns:
            Dictionary with analyzer information
        """
        return {
            "project_path": str(self.project_path),
            "checker_count": len(self.checkers),
            "checkers": [c.name for c in self.checkers],
        }
