"""
Tests de integración para reporters — pipeline completo análisis → exportación.

Verifica que el análisis de los proyectos de ejemplo genera reportes
JSON y HTML válidos con la estructura esperada.
"""

import json

from gtaa_validator import __version__
from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer
from gtaa_validator.reporters.json_reporter import JsonReporter
from gtaa_validator.reporters.html_reporter import HtmlReporter


class TestJsonReporterIntegration:
    """Pipeline completo: análisis → JSON."""

    def test_bad_project_json(self, bad_project_path, tmp_path):
        """Análisis de bad_project genera JSON con violaciones."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()

        output = tmp_path / "report.json"
        JsonReporter().generate(report, output)

        data = json.loads(output.read_text(encoding="utf-8"))

        assert data["summary"]["total_violations"] > 0
        assert data["summary"]["score"] < 100
        assert data["summary"]["files_analyzed"] > 0
        assert len(data["violations"]) == data["summary"]["total_violations"]
        assert data["metadata"]["validator_version"] == __version__

    def test_good_project_json(self, good_project_path, tmp_path):
        """Análisis de good_project genera JSON sin violaciones."""
        analyzer = StaticAnalyzer(good_project_path)
        report = analyzer.analyze()

        output = tmp_path / "report.json"
        JsonReporter().generate(report, output)

        data = json.loads(output.read_text(encoding="utf-8"))

        assert data["summary"]["total_violations"] == 0
        assert data["summary"]["score"] == 100.0
        assert data["violations"] == []


class TestHtmlReporterIntegration:
    """Pipeline completo: análisis → HTML."""

    def test_bad_project_html(self, bad_project_path, tmp_path):
        """Análisis de bad_project genera HTML con dashboard completo."""
        analyzer = StaticAnalyzer(bad_project_path)
        report = analyzer.analyze()

        output = tmp_path / "report.html"
        HtmlReporter().generate(report, output)

        content = output.read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in content
        assert "gTAA AI Validator" in content
        assert "CRÍTICA" in content
        assert "<svg" in content
        assert "DefinitionChecker" in content
        assert "<table " in content

    def test_good_project_html(self, good_project_path, tmp_path):
        """Análisis de good_project genera HTML con score perfecto."""
        analyzer = StaticAnalyzer(good_project_path)
        report = analyzer.analyze()

        output = tmp_path / "report.html"
        HtmlReporter().generate(report, output)

        content = output.read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in content
        assert "100" in content
        assert "EXCELENTE" in content
        assert "Sin violaciones detectadas" in content
