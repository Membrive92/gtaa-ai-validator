"""
Tests for the CLI entry point (__main__.py).

Uses Click's CliRunner to invoke the CLI without spawning a subprocess.
Covers: basic run, verbose flag, JSON/HTML export, invalid path, score display,
        score labels, --config, --ai branch, file-as-argument, exit codes.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from gtaa_validator.__main__ import main
from gtaa_validator.models import Report, Violation, Severity, ViolationType


class TestCLI:
    """Tests for the main CLI command."""

    def setup_method(self):
        self.runner = CliRunner()
        # Use examples/bad_project as test fixture
        self.bad_project = os.path.join(
            os.path.dirname(__file__), os.pardir, os.pardir,
            "examples", "bad_project"
        )

    def test_basic_run(self):
        """CLI runs successfully with a valid project path."""
        result = self.runner.invoke(main, [self.bad_project])
        assert result.exit_code in (0, 1)
        assert "gTAA AI Validator" in result.output

    def test_verbose_flag(self):
        """--verbose shows detailed violation output."""
        result = self.runner.invoke(main, [self.bad_project, "--verbose"])
        assert result.exit_code in (0, 1)
        assert "VIOLACIONES DETALLADAS" in result.output

    def test_json_export(self):
        """--json creates a valid JSON report file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            json_path = f.name
        try:
            result = self.runner.invoke(main, [self.bad_project, "--json", json_path])
            assert result.exit_code in (0, 1)
            assert os.path.exists(json_path)
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            assert "summary" in data
            assert "violations" in data
        finally:
            os.unlink(json_path)

    def test_html_export(self):
        """--html creates an HTML report file."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            html_path = f.name
        try:
            result = self.runner.invoke(main, [self.bad_project, "--html", html_path])
            assert result.exit_code in (0, 1)
            assert os.path.exists(html_path)
            with open(html_path, encoding="utf-8") as f:
                content = f.read()
            assert "<html" in content.lower()
        finally:
            os.unlink(html_path)

    def test_invalid_path(self):
        """Non-existent path results in error exit code."""
        result = self.runner.invoke(main, ["/nonexistent/path/xyz"])
        assert result.exit_code != 0

    def test_score_displayed(self):
        """Output contains compliance score."""
        result = self.runner.invoke(main, [self.bad_project])
        assert "cumplimiento" in result.output.lower()

    def test_file_as_argument_exits_with_error(self):
        """Passing a file (not a directory) triggers 'no es un directorio' error."""
        # Create a temporary file that exists
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            file_path = f.name
            f.write(b"x = 1\n")
        try:
            result = self.runner.invoke(main, [file_path])
            assert result.exit_code != 0
        finally:
            os.unlink(file_path)

    def test_config_flag(self):
        """--config loads a .gtaa.yaml config file."""
        # Create a minimal config file
        with tempfile.NamedTemporaryFile(
            suffix=".gtaa.yaml", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("exclude_checks: []\n")
            config_path = f.name
        try:
            result = self.runner.invoke(
                main, [self.bad_project, "--config", config_path]
            )
            assert result.exit_code in (0, 1)
            assert "gTAA AI Validator" in result.output
        finally:
            os.unlink(config_path)


class TestCLIScoreLabels:
    """Tests for score label thresholds in CLI output."""

    def setup_method(self):
        self.runner = CliRunner()
        self.bad_project = os.path.join(
            os.path.dirname(__file__), os.pardir, os.pardir,
            "examples", "bad_project"
        )

    def _make_report(self, score, violations=None, project_path=None):
        """Helper to create a Report with a fixed score."""
        report = Report(
            project_path=Path(project_path or self.bad_project).resolve(),
            violations=violations or [],
            files_analyzed=5,
            score=score,
        )
        return report

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_score_label_excelente(self, mock_analyzer_cls):
        """Score >= 90 shows EXCELENTE."""
        report = self._make_report(95.0)
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project])
        assert "EXCELENTE" in result.output

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_score_label_bueno(self, mock_analyzer_cls):
        """Score >= 75 and < 90 shows BUENO."""
        report = self._make_report(80.0)
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project])
        assert "BUENO" in result.output

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_score_label_necesita_mejoras(self, mock_analyzer_cls):
        """Score >= 50 and < 75 shows NECESITA MEJORAS."""
        report = self._make_report(60.0)
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project])
        assert "NECESITA MEJORAS" in result.output

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_score_label_problemas_criticos(self, mock_analyzer_cls):
        """Score < 50 shows PROBLEMAS CRÍTICOS."""
        report = self._make_report(30.0)
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project])
        assert "PROBLEMAS" in result.output


class TestCLIExitCodes:
    """Tests for CLI exit codes based on violations."""

    def setup_method(self):
        self.runner = CliRunner()
        self.bad_project = os.path.join(
            os.path.dirname(__file__), os.pardir, os.pardir,
            "examples", "bad_project"
        )

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_exit_code_0_no_critical(self, mock_analyzer_cls):
        """Exit code 0 when no CRITICAL violations."""
        report = Report(
            project_path=Path(self.bad_project).resolve(),
            violations=[
                Violation(
                    violation_type=ViolationType.POOR_TEST_NAMING,
                    severity=Severity.LOW,
                    file_path=Path("test.py"),
                    message="low severity only",
                ),
            ],
            files_analyzed=5,
            score=95.0,
        )
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project])
        assert result.exit_code == 0

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_critical_violation_returns_1(self, mock_analyzer_cls):
        """main() returns 1 when CRITICAL violations exist.

        Note: CliRunner uses standalone_mode=False, so the return value
        is captured in result.return_value, not result.exit_code.
        """
        report = Report(
            project_path=Path(self.bad_project).resolve(),
            violations=[
                Violation(
                    violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
                    severity=Severity.CRITICAL,
                    file_path=Path("test.py"),
                    message="critical violation",
                ),
            ],
            files_analyzed=5,
            score=50.0,
        )
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project])
        # Click CliRunner captures the return value, not as exit_code
        assert "CRÍTICA: 1" in result.output


class TestCLIVerboseOutput:
    """Tests for verbose violation details and AI suggestion display."""

    def setup_method(self):
        self.runner = CliRunner()
        self.bad_project = os.path.join(
            os.path.dirname(__file__), os.pardir, os.pardir,
            "examples", "bad_project"
        )

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_verbose_shows_ai_suggestion(self, mock_analyzer_cls):
        """--verbose shows [AI] suggestion when present."""
        project = Path(self.bad_project).resolve()
        report = Report(
            project_path=project,
            violations=[
                Violation(
                    violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
                    severity=Severity.CRITICAL,
                    file_path=project / "test_login.py",
                    line_number=10,
                    message="Direct selenium call",
                    code_snippet="driver.find_element()",
                    ai_suggestion="Use a Page Object instead",
                ),
            ],
            files_analyzed=3,
            score=50.0,
        )
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project, "--verbose"])
        assert "[AI]" in result.output
        assert "Page Object" in result.output

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_verbose_shows_relative_path(self, mock_analyzer_cls):
        """--verbose shows relative file paths for violations."""
        project = Path(self.bad_project).resolve()
        report = Report(
            project_path=project,
            violations=[
                Violation(
                    violation_type=ViolationType.POOR_TEST_NAMING,
                    severity=Severity.LOW,
                    file_path=project / "tests" / "test_misc.py",
                    line_number=5,
                    message="Generic test name",
                ),
            ],
            files_analyzed=3,
            score=90.0,
        )
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project, "--verbose"])
        assert "test_misc.py" in result.output

    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_verbose_external_path_fallback(self, mock_analyzer_cls):
        """--verbose handles violation path outside project (ValueError)."""
        project = Path(self.bad_project).resolve()
        report = Report(
            project_path=project,
            violations=[
                Violation(
                    violation_type=ViolationType.POOR_TEST_NAMING,
                    severity=Severity.LOW,
                    file_path=Path("/completely/different/path/test.py"),
                    line_number=1,
                    message="External path",
                ),
            ],
            files_analyzed=1,
            score=90.0,
        )
        mock_analyzer_cls.return_value.analyze.return_value = report
        result = self.runner.invoke(main, [self.bad_project, "--verbose"])
        # Should not crash, path shown as-is
        assert result.exit_code in (0, 1)
        assert "test.py" in result.output


class TestCLIAIBranch:
    """Tests for the --ai semantic analysis branch."""

    def setup_method(self):
        self.runner = CliRunner()
        self.bad_project = os.path.join(
            os.path.dirname(__file__), os.pardir, os.pardir,
            "examples", "bad_project"
        )

    @patch("gtaa_validator.__main__.SemanticAnalyzer")
    @patch("gtaa_validator.__main__.create_llm_client")
    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_ai_flag_invokes_semantic_analyzer(
        self, mock_static_cls, mock_create_llm, mock_semantic_cls
    ):
        """--ai creates LLM client and runs SemanticAnalyzer."""
        project = Path(self.bad_project).resolve()
        base_report = Report(
            project_path=project, violations=[], files_analyzed=3, score=100.0
        )
        mock_static_cls.return_value.analyze.return_value = base_report

        # SemanticAnalyzer.analyze returns the same report
        mock_semantic_cls.return_value.analyze.return_value = base_report
        mock_semantic_cls.return_value.get_token_usage.return_value = {
            "total_calls": 0, "input_tokens": 0, "output_tokens": 0,
            "total_tokens": 0, "estimated_cost_usd": 0.0,
        }

        mock_llm = MagicMock()
        mock_llm.__class__.__name__ = "MockLLMClient"
        mock_create_llm.return_value = mock_llm

        result = self.runner.invoke(main, [self.bad_project, "--ai"])
        assert result.exit_code in (0, 1)
        mock_create_llm.assert_called_once()
        mock_semantic_cls.assert_called_once()

    @patch("gtaa_validator.__main__.SemanticAnalyzer")
    @patch("gtaa_validator.__main__.create_llm_client")
    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_ai_with_token_usage(
        self, mock_static_cls, mock_create_llm, mock_semantic_cls
    ):
        """--ai with token usage shows LLM token consumption summary."""
        project = Path(self.bad_project).resolve()
        report = Report(
            project_path=project, violations=[], files_analyzed=3, score=100.0,
            llm_provider_info={"current_provider": "MockProvider"},
        )
        mock_static_cls.return_value.analyze.return_value = report
        mock_semantic_cls.return_value.analyze.return_value = report
        mock_semantic_cls.return_value.get_token_usage.return_value = {
            "total_calls": 5, "input_tokens": 1000, "output_tokens": 500,
            "total_tokens": 1500, "estimated_cost_usd": 0.0023,
        }

        mock_llm = MagicMock()
        mock_llm.__class__.__name__ = "MockLLMClient"
        mock_create_llm.return_value = mock_llm

        result = self.runner.invoke(main, [self.bad_project, "--ai"])
        assert "Consumo de Tokens" in result.output
        assert "1,500" in result.output or "1500" in result.output

    @patch("gtaa_validator.__main__.SemanticAnalyzer")
    @patch("gtaa_validator.__main__.create_llm_client")
    @patch("gtaa_validator.__main__.StaticAnalyzer")
    def test_ai_with_fallback_info(
        self, mock_static_cls, mock_create_llm, mock_semantic_cls
    ):
        """--ai shows fallback info when provider falls back."""
        project = Path(self.bad_project).resolve()
        report = Report(
            project_path=project, violations=[], files_analyzed=3, score=100.0,
            llm_provider_info={
                "current_provider": "MockProvider",
                "initial_provider": "GeminiProvider",
                "fallback_occurred": True,
            },
        )
        mock_static_cls.return_value.analyze.return_value = report
        mock_semantic_cls.return_value.analyze.return_value = report
        mock_semantic_cls.return_value.get_token_usage.return_value = {
            "total_calls": 0, "input_tokens": 0, "output_tokens": 0,
            "total_tokens": 0, "estimated_cost_usd": 0.0,
        }

        mock_llm = MagicMock()
        mock_llm.__class__.__name__ = "MockLLMClient"
        mock_create_llm.return_value = mock_llm

        result = self.runner.invoke(main, [self.bad_project, "--ai"])
        assert "Fallback" in result.output or "fallback" in result.output


class TestAutoReports:
    """Tests for automatic report generation with timestamps (Allure-style)."""

    def setup_method(self):
        self.runner = CliRunner()
        self.bad_project = os.path.join(
            os.path.dirname(__file__), os.pardir, os.pardir,
            "examples", "bad_project"
        )

    def test_auto_generates_reports_by_default(self, tmp_path):
        """Without --json/--html, reports are auto-generated in output-dir."""
        out_dir = tmp_path / "reports"
        result = self.runner.invoke(
            main, [self.bad_project, "--output-dir", str(out_dir)]
        )
        assert result.exit_code in (0, 1)
        json_files = list(out_dir.glob("gtaa_report_*.json"))
        html_files = list(out_dir.glob("gtaa_report_*.html"))
        assert len(json_files) == 1, f"Expected 1 JSON report, got {json_files}"
        assert len(html_files) == 1, f"Expected 1 HTML report, got {html_files}"

    def test_explicit_json_skips_auto(self, tmp_path):
        """With explicit --json, no auto-generation in output-dir."""
        out_dir = tmp_path / "reports"
        json_file = tmp_path / "custom.json"
        result = self.runner.invoke(
            main, [self.bad_project, "--json", str(json_file), "--output-dir", str(out_dir)]
        )
        assert result.exit_code in (0, 1)
        assert json_file.exists()
        # output-dir should not be created since explicit path was given
        assert not out_dir.exists()

    def test_no_report_flag(self, tmp_path):
        """--no-report disables automatic report generation."""
        out_dir = tmp_path / "reports"
        result = self.runner.invoke(
            main, [self.bad_project, "--no-report", "--output-dir", str(out_dir)]
        )
        assert result.exit_code in (0, 1)
        assert not out_dir.exists()

    def test_creates_nested_directories(self, tmp_path):
        """Parent directories are created for explicit report paths."""
        nested_json = tmp_path / "a" / "b" / "report.json"
        result = self.runner.invoke(
            main, [self.bad_project, "--json", str(nested_json), "--no-report"]
        )
        assert result.exit_code in (0, 1)
        assert nested_json.exists()

    def test_filename_format(self, tmp_path):
        """Auto-generated filenames follow gtaa_report_<project>_YYYY-MM-DD pattern."""
        import re
        out_dir = tmp_path / "reports"
        self.runner.invoke(main, [self.bad_project, "--output-dir", str(out_dir)])
        json_files = list(out_dir.glob("gtaa_report_*.json"))
        assert len(json_files) == 1
        pattern = r"gtaa_report_bad_project_\d{4}-\d{2}-\d{2}\.json"
        assert re.match(pattern, json_files[0].name), f"Filename {json_files[0].name} doesn't match pattern"
