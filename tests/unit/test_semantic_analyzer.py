"""Tests para SemanticAnalyzer — análisis semántico con LLM."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gtaa_validator.models import Report, Violation, Severity, ViolationType
from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.api_client import APILLMClient, RateLimitError
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


class TestSemanticAnalyzerProviderTracking:
    """Tests para tracking de proveedor LLM y fallback."""

    def test_provider_info_with_mock(self, mock_client, tmp_path, empty_report):
        """MockLLMClient se identifica correctamente."""
        empty_report.project_path = tmp_path
        analyzer = SemanticAnalyzer(tmp_path, mock_client)

        result = analyzer.analyze(empty_report)

        assert result.llm_provider_info is not None
        assert result.llm_provider_info["initial_provider"] == "mock"
        assert result.llm_provider_info["current_provider"] == "mock"
        assert result.llm_provider_info["fallback_occurred"] is False

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_provider_info_with_gemini(self, mock_genai, tmp_path, empty_report):
        """APILLMClient se identifica como gemini."""
        empty_report.project_path = tmp_path
        gemini_client = APILLMClient(api_key="test-key")
        analyzer = SemanticAnalyzer(tmp_path, gemini_client)

        # Mock para que no haga llamadas reales
        gemini_client.analyze_file = Mock(return_value=[])
        gemini_client.enrich_violation = Mock(return_value="")

        result = analyzer.analyze(empty_report)

        assert result.llm_provider_info["initial_provider"] == "gemini"
        assert result.llm_provider_info["current_provider"] == "gemini"
        assert result.llm_provider_info["fallback_occurred"] is False

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_fallback_on_rate_limit_in_analyze_file(self, mock_genai, project_with_tests, empty_report):
        """Fallback a Mock cuando analyze_file da RateLimitError."""
        empty_report.project_path = project_with_tests
        gemini_client = APILLMClient(api_key="test-key")

        # Simular rate limit en primera llamada
        gemini_client.analyze_file = Mock(side_effect=RateLimitError("429 rate limit"))

        analyzer = SemanticAnalyzer(project_with_tests, gemini_client)
        result = analyzer.analyze(empty_report)

        assert result.llm_provider_info["initial_provider"] == "gemini"
        assert result.llm_provider_info["current_provider"] == "mock"
        assert result.llm_provider_info["fallback_occurred"] is True

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_fallback_on_rate_limit_in_enrich_violation(
        self, mock_genai, report_with_violations
    ):
        """Fallback a Mock cuando enrich_violation da RateLimitError."""
        project_path = report_with_violations.project_path
        gemini_client = APILLMClient(api_key="test-key")

        # analyze_file funciona, pero enrich_violation falla
        gemini_client.analyze_file = Mock(return_value=[])
        gemini_client.enrich_violation = Mock(side_effect=RateLimitError("quota exceeded"))

        analyzer = SemanticAnalyzer(project_path, gemini_client)
        result = analyzer.analyze(report_with_violations)

        assert result.llm_provider_info["fallback_occurred"] is True
        assert result.llm_provider_info["current_provider"] == "mock"

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_fallback_only_occurs_once(self, mock_genai, project_with_tests, empty_report):
        """El fallback solo ocurre una vez aunque haya múltiples errores."""
        empty_report.project_path = project_with_tests
        gemini_client = APILLMClient(api_key="test-key")

        # Simular rate limit
        call_count = {"count": 0}

        def raise_rate_limit(*args, **kwargs):
            call_count["count"] += 1
            raise RateLimitError("429")

        gemini_client.analyze_file = Mock(side_effect=raise_rate_limit)

        analyzer = SemanticAnalyzer(project_with_tests, gemini_client)
        result = analyzer.analyze(empty_report)

        # Verificar que el fallback ocurrió
        assert result.llm_provider_info["fallback_occurred"] is True
        # El cliente ahora debe ser MockLLMClient
        assert isinstance(analyzer.llm_client, MockLLMClient)

    def test_get_provider_info_before_analyze(self, mock_client, tmp_path):
        """get_provider_info funciona antes de llamar a analyze."""
        analyzer = SemanticAnalyzer(tmp_path, mock_client)

        info = analyzer.get_provider_info()

        assert info["initial_provider"] == "mock"
        assert info["current_provider"] == "mock"
        assert info["fallback_occurred"] is False

    def test_llm_provider_info_in_report_to_dict(self, mock_client, tmp_path, empty_report):
        """llm_provider_info aparece en report.to_dict()."""
        empty_report.project_path = tmp_path
        analyzer = SemanticAnalyzer(tmp_path, mock_client)

        result = analyzer.analyze(empty_report)
        report_dict = result.to_dict()

        assert "llm_provider" in report_dict["metadata"]
        assert report_dict["metadata"]["llm_provider"]["current_provider"] == "mock"

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_max_llm_calls_triggers_fallback(self, mock_genai, report_with_violations):
        """max_llm_calls limita las llamadas antes de fallback."""
        project_path = report_with_violations.project_path
        gemini_client = APILLMClient(api_key="test-key")

        # Mock para que las llamadas funcionen
        gemini_client.analyze_file = Mock(return_value=[])
        gemini_client.enrich_violation = Mock(return_value="sugerencia")

        # Limitar a 1 llamada (analyze_file), luego fallback antes de enrich
        analyzer = SemanticAnalyzer(project_path, gemini_client, max_llm_calls=1)
        result = analyzer.analyze(report_with_violations)

        # Deberia haber hecho fallback despues de 1 llamada
        assert result.llm_provider_info["fallback_occurred"] is True
        assert result.llm_provider_info["llm_calls"] == 1
        assert result.llm_provider_info["max_llm_calls"] == 1

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_no_limit_means_no_fallback(self, mock_genai, tmp_path, empty_report):
        """Sin max_llm_calls no hay fallback por límite."""
        empty_report.project_path = tmp_path
        gemini_client = APILLMClient(api_key="test-key")

        gemini_client.analyze_file = Mock(return_value=[])
        gemini_client.enrich_violation = Mock(return_value="")

        # Sin límite
        analyzer = SemanticAnalyzer(tmp_path, gemini_client, max_llm_calls=None)
        result = analyzer.analyze(empty_report)

        assert result.llm_provider_info["fallback_occurred"] is False
        assert "llm_calls" not in result.llm_provider_info


class TestSemanticAnalyzerExcludedDirs:
    """Tests for directory exclusion in SemanticAnalyzer."""

    def test_excluded_dirs_filtering(self, mock_client, tmp_path, empty_report):
        """Files inside excluded dirs (venv, __pycache__) are skipped."""
        empty_report.project_path = tmp_path

        # Create files in excluded directories
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "test_venv.py").write_text("def test_x(): pass\n", encoding="utf-8")

        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test_cache.py").write_text("def test_y(): pass\n", encoding="utf-8")

        # Create a real test file
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_real.py").write_text("def test_z(): assert True\n", encoding="utf-8")

        analyzer = SemanticAnalyzer(tmp_path, mock_client)
        files = analyzer._discover_python_files()
        filenames = [f.name for f in files]

        assert "test_real.py" in filenames
        assert "test_venv.py" not in filenames
        assert "test_cache.py" not in filenames
