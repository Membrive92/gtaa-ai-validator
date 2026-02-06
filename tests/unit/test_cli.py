"""
Tests for the CLI entry point (__main__.py).

Uses Click's CliRunner to invoke the CLI without spawning a subprocess.
Covers: basic run, verbose flag, JSON/HTML export, invalid path, score display.
"""

import json
import os
import tempfile

from click.testing import CliRunner

from gtaa_validator.__main__ import main


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
