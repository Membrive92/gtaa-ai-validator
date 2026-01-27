"""
Tests for gtaa_validator.analyzers.static_analyzer

Covers:
- Checker initialization
- File discovery and exclusion
- End-to-end analysis using examples/bad_project and examples/good_project
- Report metadata correctness
"""

import pytest
from pathlib import Path

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer
from gtaa_validator.checkers.definition_checker import DefinitionChecker


# =========================================================================
# Initialization
# =========================================================================

class TestInitialization:
    """Tests for StaticAnalyzer construction."""

    def test_initializes_with_definition_checker(self, bad_project_path):
        """Phase 2 creates exactly one checker: DefinitionChecker."""
        analyzer = StaticAnalyzer(bad_project_path)
        assert len(analyzer.checkers) == 1
        assert isinstance(analyzer.checkers[0], DefinitionChecker)

    def test_resolves_path(self, bad_project_path):
        """project_path is resolved to absolute."""
        analyzer = StaticAnalyzer(bad_project_path)
        assert analyzer.project_path.is_absolute()

    def test_get_summary(self, bad_project_path):
        """get_summary() returns analyzer configuration."""
        analyzer = StaticAnalyzer(bad_project_path)
        summary = analyzer.get_summary()
        assert summary["checker_count"] == 1
        assert "DefinitionChecker" in summary["checkers"]


# =========================================================================
# File discovery
# =========================================================================

class TestFileDiscovery:
    """Tests for _discover_python_files()."""

    def test_finds_python_files(self, bad_project_path):
        """Discovers .py files in the project."""
        analyzer = StaticAnalyzer(bad_project_path)
        files = analyzer._discover_python_files()
        assert len(files) > 0
        assert all(f.suffix == ".py" for f in files)

    def test_excludes_venv(self, tmp_path):
        """Files inside venv/ are excluded."""
        # Create a fake project with a venv
        (tmp_path / "test_real.py").write_text("pass", encoding="utf-8")
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "test_venv.py").write_text("pass", encoding="utf-8")

        analyzer = StaticAnalyzer(tmp_path)
        files = analyzer._discover_python_files()
        filenames = [f.name for f in files]

        assert "test_real.py" in filenames
        assert "test_venv.py" not in filenames

    def test_excludes_pycache(self, tmp_path):
        """Files inside __pycache__/ are excluded."""
        (tmp_path / "test_real.py").write_text("pass", encoding="utf-8")
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test_cached.py").write_text("pass", encoding="utf-8")

        analyzer = StaticAnalyzer(tmp_path)
        files = analyzer._discover_python_files()
        filenames = [f.name for f in files]

        assert "test_real.py" in filenames
        assert "test_cached.py" not in filenames

    def test_empty_project(self, tmp_path):
        """A project with no .py files returns empty list."""
        (tmp_path / "readme.txt").write_text("hello", encoding="utf-8")

        analyzer = StaticAnalyzer(tmp_path)
        files = analyzer._discover_python_files()
        assert files == []


# =========================================================================
# End-to-end analysis — bad_project
# =========================================================================

class TestAnalyzeBadProject:
    """Integration tests using examples/bad_project."""

    def test_detects_15_violations(self, bad_project_path):
        """bad_project should produce exactly 15 violations."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        assert len(report.violations) == 15

    def test_all_violations_are_critical(self, bad_project_path):
        """All violations in bad_project are CRITICAL severity."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        from gtaa_validator.models import Severity
        for v in report.violations:
            assert v.severity == Severity.CRITICAL

    def test_score_is_zero(self, bad_project_path):
        """bad_project score should be 0.0 (15 × 10 = 150 penalty)."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        assert report.score == 0.0

    def test_files_analyzed_count(self, bad_project_path):
        """Report tracks how many files were analyzed."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        assert report.files_analyzed >= 2


# =========================================================================
# End-to-end analysis — good_project
# =========================================================================

class TestAnalyzeGoodProject:
    """Integration tests using examples/good_project."""

    def test_no_violations(self, good_project_path):
        """good_project should produce zero violations."""
        analyzer = StaticAnalyzer(good_project_path)
        report = analyzer.analyze()
        assert len(report.violations) == 0

    def test_score_is_100(self, good_project_path):
        """good_project score should be 100.0."""
        analyzer = StaticAnalyzer(good_project_path)
        report = analyzer.analyze()
        assert report.score == 100.0

    def test_files_analyzed_count(self, good_project_path):
        """Report tracks analyzed files in good_project."""
        analyzer = StaticAnalyzer(good_project_path)
        report = analyzer.analyze()
        assert report.files_analyzed >= 2


# =========================================================================
# Report metadata
# =========================================================================

class TestReportMetadata:
    """Tests for report metadata correctness."""

    def test_execution_time_is_positive(self, bad_project_path):
        """Execution time is recorded and >= 0."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        assert report.execution_time_seconds >= 0

    def test_project_path_in_report(self, bad_project_path):
        """Report contains the analyzed project path."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        assert report.project_path == bad_project_path.resolve()

    def test_report_serializable(self, bad_project_path):
        """Report.to_dict() produces a valid dictionary."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()
        d = report.to_dict()
        assert isinstance(d, dict)
        assert d["summary"]["total_violations"] == 15
        assert d["summary"]["score"] == 0.0
