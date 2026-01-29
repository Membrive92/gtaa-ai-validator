"""Tests para JsonReporter — generación de reportes JSON."""

import json
from pathlib import Path
from datetime import datetime

import pytest

from gtaa_validator.models import Report, Violation, Severity, ViolationType
from gtaa_validator.reporters.json_reporter import JsonReporter


@pytest.fixture
def reporter():
    """Instancia de JsonReporter."""
    return JsonReporter()


@pytest.fixture
def sample_report(tmp_path):
    """Report con violaciones de ejemplo."""
    report = Report(
        project_path=tmp_path / "mi-proyecto",
        files_analyzed=5,
        timestamp=datetime(2026, 1, 29, 12, 0, 0),
        score=65.0,
        execution_time_seconds=0.123,
    )
    report.violations = [
        Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=tmp_path / "mi-proyecto" / "tests" / "test_login.py",
            line_number=10,
            message="Llamada directa a Selenium en capa de test",
            code_snippet='driver.find_element(By.ID, "user")',
        ),
        Violation(
            violation_type=ViolationType.POOR_TEST_NAMING,
            severity=Severity.LOW,
            file_path=tmp_path / "mi-proyecto" / "tests" / "test_misc.py",
            line_number=5,
            message="Nombre de test genérico",
        ),
    ]
    return report


@pytest.fixture
def empty_report(tmp_path):
    """Report sin violaciones."""
    return Report(
        project_path=tmp_path / "proyecto-limpio",
        files_analyzed=3,
        timestamp=datetime(2026, 1, 29, 12, 0, 0),
        score=100.0,
        execution_time_seconds=0.05,
    )


class TestJsonReporter:
    """Tests para generación de reportes JSON."""

    def test_genera_fichero_json_valido(self, reporter, sample_report, tmp_path):
        """El fichero generado contiene JSON válido."""
        output = tmp_path / "report.json"
        reporter.generate(sample_report, output)

        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_estructura_metadata(self, reporter, sample_report, tmp_path):
        """El JSON contiene sección metadata con campos esperados."""
        output = tmp_path / "report.json"
        reporter.generate(sample_report, output)
        data = json.loads(output.read_text(encoding="utf-8"))

        assert "metadata" in data
        meta = data["metadata"]
        assert "project_path" in meta
        assert "timestamp" in meta
        assert "validator_version" in meta
        assert "execution_time_seconds" in meta
        assert meta["execution_time_seconds"] == 0.123

    def test_estructura_summary(self, reporter, sample_report, tmp_path):
        """El JSON contiene sección summary con score y conteos."""
        output = tmp_path / "report.json"
        reporter.generate(sample_report, output)
        data = json.loads(output.read_text(encoding="utf-8"))

        assert "summary" in data
        summary = data["summary"]
        assert summary["files_analyzed"] == 5
        assert summary["total_violations"] == 2
        assert summary["score"] == 65.0
        assert summary["violations_by_severity"]["CRITICAL"] == 1
        assert summary["violations_by_severity"]["LOW"] == 1

    def test_estructura_violations(self, reporter, sample_report, tmp_path):
        """El JSON contiene lista de violaciones con campos completos."""
        output = tmp_path / "report.json"
        reporter.generate(sample_report, output)
        data = json.loads(output.read_text(encoding="utf-8"))

        assert "violations" in data
        assert len(data["violations"]) == 2

        v = data["violations"][0]
        assert v["type"] == "ADAPTATION_IN_DEFINITION"
        assert v["severity"] == "CRITICAL"
        assert v["line"] == 10
        assert "message" in v
        assert "recommendation" in v

    def test_report_sin_violaciones(self, reporter, empty_report, tmp_path):
        """Un report limpio genera JSON válido con violations vacío."""
        output = tmp_path / "report.json"
        reporter.generate(empty_report, output)
        data = json.loads(output.read_text(encoding="utf-8"))

        assert data["summary"]["total_violations"] == 0
        assert data["summary"]["score"] == 100.0
        assert data["violations"] == []

    def test_encoding_utf8(self, reporter, sample_report, tmp_path):
        """El JSON preserva caracteres UTF-8 (español)."""
        output = tmp_path / "report.json"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        # ensure_ascii=False permite caracteres directos
        assert "Llamada directa" in content
        assert "genérico" in content

    def test_json_indentado(self, reporter, sample_report, tmp_path):
        """El JSON está formateado con indentación para legibilidad."""
        output = tmp_path / "report.json"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        # indent=2 produce líneas con espacios
        assert "\n  " in content
