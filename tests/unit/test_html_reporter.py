"""Tests para HtmlReporter — generación de reportes HTML dashboard."""

from pathlib import Path
from datetime import datetime

import pytest

from gtaa_validator.models import Report, Violation, Severity, ViolationType
from gtaa_validator.reporters.html_reporter import HtmlReporter


@pytest.fixture
def reporter():
    """Instancia de HtmlReporter."""
    return HtmlReporter()


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
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=tmp_path / "mi-proyecto" / "tests" / "test_login.py",
            line_number=15,
            message="Datos de test hardcodeados",
            code_snippet='"admin@test.com"',
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


class TestHtmlReporter:
    """Tests para generación de reportes HTML."""

    def test_genera_fichero_html(self, reporter, sample_report, tmp_path):
        """El fichero generado existe y contiene DOCTYPE."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)

        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_contiene_nombre_proyecto(self, reporter, sample_report, tmp_path):
        """El HTML muestra el nombre del proyecto."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "mi-proyecto" in content

    def test_contiene_score(self, reporter, sample_report, tmp_path):
        """El HTML muestra la puntuación."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "65" in content
        assert "/ 100" in content

    def test_contiene_svg_gauge(self, reporter, sample_report, tmp_path):
        """El HTML incluye un SVG para el gauge de score."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "<svg" in content
        assert "circle" in content

    def test_contiene_conteo_severidades(self, reporter, sample_report, tmp_path):
        """El HTML muestra tarjetas con conteo por severidad."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "CRÍTICA" in content
        assert "ALTA" in content
        assert "MEDIA" in content
        assert "BAJA" in content

    def test_contiene_tabla_violaciones(self, reporter, sample_report, tmp_path):
        """El HTML incluye tabla con las violaciones detectadas."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "Adaptación en capa de definición" in content
        assert "Nombre de test genérico" in content
        # Violaciones agrupadas por checker
        assert "DefinitionChecker" in content
        assert "QualityChecker" in content

    def test_contiene_grafico_barras(self, reporter, sample_report, tmp_path):
        """El HTML incluye gráfico de barras SVG."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "Distribución por Severidad" in content
        assert "<rect" in content

    def test_report_sin_violaciones(self, reporter, empty_report, tmp_path):
        """Un report limpio muestra mensaje de sin violaciones."""
        output = tmp_path / "report.html"
        reporter.generate(empty_report, output)
        content = output.read_text(encoding="utf-8")

        assert "Sin violaciones detectadas" in content
        assert "<!DOCTYPE html>" in content
        assert "100" in content  # score 100

    def test_sin_violaciones_no_chart(self, reporter, empty_report, tmp_path):
        """Sin violaciones no se genera gráfico de barras."""
        output = tmp_path / "report.html"
        reporter.generate(empty_report, output)
        content = output.read_text(encoding="utf-8")

        assert "Distribución por Severidad" not in content

    def test_score_excelente_label(self, reporter, empty_report, tmp_path):
        """Score 100 muestra etiqueta EXCELENTE."""
        output = tmp_path / "report.html"
        reporter.generate(empty_report, output)
        content = output.read_text(encoding="utf-8")

        assert "EXCELENTE" in content

    def test_score_problemas_criticos_label(self, reporter, sample_report, tmp_path):
        """Score < 50 muestra PROBLEMAS CRÍTICOS."""
        sample_report.score = 30.0
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "PROBLEMAS" in content

    def test_contiene_footer(self, reporter, sample_report, tmp_path):
        """El HTML incluye footer con versión."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "Generado por gTAA AI Validator" in content

    def test_html_responsive(self, reporter, sample_report, tmp_path):
        """El HTML incluye viewport meta para responsividad."""
        output = tmp_path / "report.html"
        reporter.generate(sample_report, output)
        content = output.read_text(encoding="utf-8")

        assert "viewport" in content

    def test_escapa_html_en_contenido(self, reporter, tmp_path):
        """El HTML escapa caracteres especiales para evitar XSS."""
        report = Report(
            project_path=tmp_path / "test<script>alert(1)</script>",
            files_analyzed=1,
            timestamp=datetime(2026, 1, 29, 12, 0, 0),
            score=100.0,
        )
        report.violations = [
            Violation(
                violation_type=ViolationType.POOR_TEST_NAMING,
                severity=Severity.LOW,
                file_path=tmp_path / "test.py",
                line_number=1,
                message='<script>alert("xss")</script>',
            ),
        ]
        output = tmp_path / "report.html"
        reporter.generate(report, output)
        content = output.read_text(encoding="utf-8")

        assert "<script>" not in content
        assert "&lt;script&gt;" in content
