"""Tests para SemanticAnalyzer — análisis semántico con LLM."""

from datetime import datetime
from pathlib import Path

import pytest

from gtaa_validator.models import Report, Violation, Severity, ViolationType
from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.analyzers.semantic_analyzer import SemanticAnalyzer


@pytest.fixture
def mock_client():
    return MockLLMClient()


@pytest.fixture
def project_with_tests(tmp_path):
    """Proyecto con un test sin docstring (genera UNCLEAR_TEST_PURPOSE)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_login.py").write_text(
        'def test_foo():\n    assert True\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def project_with_page_object(tmp_path):
    """Proyecto con Page Object con muchos métodos."""
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    (pages_dir / "__init__.py").write_text("", encoding="utf-8")
    methods = "\n".join(f"    def action_{i}(self): pass" for i in range(12))
    (pages_dir / "big_page.py").write_text(
        f"class BigPage:\n{methods}\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    return tmp_path


@pytest.fixture
def empty_report(tmp_path):
    """Report sin violaciones."""
    return Report(
        project_path=tmp_path,
        files_analyzed=0,
        timestamp=datetime(2026, 1, 31, 12, 0, 0),
        score=100.0,
    )


@pytest.fixture
def report_with_violations(tmp_path):
    """Report con violaciones estáticas existentes."""
    test_file = tmp_path / "tests" / "test_login.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text('def test_foo():\n    assert True\n', encoding="utf-8")

    report = Report(
        project_path=tmp_path,
        files_analyzed=1,
        timestamp=datetime(2026, 1, 31, 12, 0, 0),
        score=90.0,
    )
    report.violations = [
        Violation(
            violation_type=ViolationType.POOR_TEST_NAMING,
            severity=Severity.LOW,
            file_path=test_file,
            line_number=1,
            message="Nombre genérico de test",
        ),
    ]
    return report


class TestSemanticAnalyzer:
    """Tests principales del SemanticAnalyzer."""

    def test_detecta_violaciones_semanticas(self, mock_client, project_with_tests, empty_report):
        """Detecta UNCLEAR_TEST_PURPOSE en tests sin docstring."""
        empty_report.project_path = project_with_tests
        analyzer = SemanticAnalyzer(project_with_tests, mock_client)

        result = analyzer.analyze(empty_report)

        semantic_types = [v.violation_type for v in result.violations]
        assert ViolationType.UNCLEAR_TEST_PURPOSE in semantic_types

    def test_detecta_page_object_too_much(self, mock_client, project_with_page_object, empty_report):
        """Detecta PAGE_OBJECT_DOES_TOO_MUCH en Page Object grande."""
        empty_report.project_path = project_with_page_object
        analyzer = SemanticAnalyzer(project_with_page_object, mock_client)

        result = analyzer.analyze(empty_report)

        semantic_types = [v.violation_type for v in result.violations]
        assert ViolationType.PAGE_OBJECT_DOES_TOO_MUCH in semantic_types

    def test_enriquece_violaciones_existentes(self, mock_client, report_with_violations):
        """Añade ai_suggestion a violaciones existentes."""
        project_path = report_with_violations.project_path
        analyzer = SemanticAnalyzer(project_path, mock_client)

        result = analyzer.analyze(report_with_violations)

        for v in result.violations:
            if v.violation_type == ViolationType.POOR_TEST_NAMING:
                assert v.ai_suggestion is not None
                assert len(v.ai_suggestion) > 10

    def test_recalcula_score(self, mock_client, project_with_tests, empty_report):
        """El score se recalcula tras añadir violaciones semánticas."""
        empty_report.project_path = project_with_tests
        empty_report.score = 100.0
        analyzer = SemanticAnalyzer(project_with_tests, mock_client)

        result = analyzer.analyze(empty_report)

        # Debe haber bajado si se detectaron violaciones
        if result.violations:
            assert result.score < 100.0

    def test_report_vacio_no_rompe(self, mock_client, tmp_path, empty_report):
        """Un proyecto vacío no genera errores."""
        empty_report.project_path = tmp_path
        analyzer = SemanticAnalyzer(tmp_path, mock_client)

        result = analyzer.analyze(empty_report)

        assert result.violations == []
        assert result.score == 100.0

    def test_no_sobreescribe_ai_suggestion_existente(self, mock_client, report_with_violations):
        """No reemplaza ai_suggestion ya existente."""
        report_with_violations.violations[0].ai_suggestion = "Sugerencia previa"
        project_path = report_with_violations.project_path
        analyzer = SemanticAnalyzer(project_path, mock_client)

        result = analyzer.analyze(report_with_violations)

        assert result.violations[0].ai_suggestion == "Sugerencia previa"

    def test_retorna_mismo_report(self, mock_client, project_with_tests, empty_report):
        """Retorna el mismo objeto Report modificado (no una copia)."""
        empty_report.project_path = project_with_tests
        analyzer = SemanticAnalyzer(project_with_tests, mock_client)

        result = analyzer.analyze(empty_report)

        assert result is empty_report

    def test_verbose_no_afecta_resultado(self, mock_client, project_with_tests, empty_report):
        """El flag verbose no cambia el resultado del análisis."""
        empty_report.project_path = project_with_tests
        analyzer_quiet = SemanticAnalyzer(project_with_tests, mock_client, verbose=False)
        analyzer_verbose = SemanticAnalyzer(project_with_tests, mock_client, verbose=True)

        report1 = Report(
            project_path=project_with_tests,
            files_analyzed=0,
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            score=100.0,
        )
        report2 = Report(
            project_path=project_with_tests,
            files_analyzed=0,
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            score=100.0,
        )

        result1 = analyzer_quiet.analyze(report1)
        result2 = analyzer_verbose.analyze(report2)

        assert len(result1.violations) == len(result2.violations)
