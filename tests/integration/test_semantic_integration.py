"""
Tests de integración para análisis semántico — pipeline completo estático + semántico.

Verifica que el análisis combinado de los proyectos de ejemplo genera
reportes con violaciones estáticas enriquecidas y violaciones semánticas.
"""

import json

import pytest

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer
from gtaa_validator.analyzers.semantic_analyzer import SemanticAnalyzer
from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.reporters.json_reporter import JsonReporter
from gtaa_validator.reporters.html_reporter import HtmlReporter


@pytest.fixture
def mock_client():
    return MockLLMClient()


class TestSemanticPipeline:
    """Pipeline completo: StaticAnalyzer → SemanticAnalyzer → Report."""

    def test_bad_project_static_plus_semantic(self, bad_project_path, mock_client):
        """bad_project genera violaciones estáticas + semánticas."""
        static = StaticAnalyzer(bad_project_path)
        report = static.analyze()
        static_count = len(report.violations)

        semantic = SemanticAnalyzer(bad_project_path, mock_client)
        report = semantic.analyze(report)

        # Debe tener al menos las mismas violaciones estáticas
        assert len(report.violations) >= static_count
        # Al menos alguna violación debe tener ai_suggestion
        enriched = [v for v in report.violations if v.ai_suggestion]
        assert len(enriched) > 0

    def test_good_project_semantic_mantiene_score_alto(self, good_project_path, mock_client):
        """good_project con semántico mantiene score alto."""
        static = StaticAnalyzer(good_project_path)
        report = static.analyze()

        semantic = SemanticAnalyzer(good_project_path, mock_client)
        report = semantic.analyze(report)

        assert report.score >= 80.0

    def test_bad_project_json_con_ai(self, bad_project_path, mock_client, tmp_path):
        """JSON incluye ai_suggestion en violaciones enriquecidas."""
        static = StaticAnalyzer(bad_project_path)
        report = static.analyze()

        semantic = SemanticAnalyzer(bad_project_path, mock_client)
        report = semantic.analyze(report)

        output = tmp_path / "report.json"
        JsonReporter().generate(report, output)
        data = json.loads(output.read_text(encoding="utf-8"))

        # Al menos una violación con ai_suggestion
        ai_violations = [v for v in data["violations"] if v.get("ai_suggestion")]
        assert len(ai_violations) > 0

    def test_bad_project_html_con_ai(self, bad_project_path, mock_client, tmp_path):
        """HTML incluye badges AI y sugerencias."""
        static = StaticAnalyzer(bad_project_path)
        report = static.analyze()

        semantic = SemanticAnalyzer(bad_project_path, mock_client)
        report = semantic.analyze(report)

        output = tmp_path / "report.html"
        HtmlReporter().generate(report, output)
        content = output.read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in content
        assert "ai-badge" in content or "ai-suggestion" in content

    def test_sin_ai_no_hay_sugerencias(self, bad_project_path, tmp_path):
        """Sin SemanticAnalyzer, no hay ai_suggestion."""
        static = StaticAnalyzer(bad_project_path)
        report = static.analyze()

        output = tmp_path / "report.json"
        JsonReporter().generate(report, output)
        data = json.loads(output.read_text(encoding="utf-8"))

        for v in data["violations"]:
            assert v.get("ai_suggestion") is None

    def test_semantic_types_en_report(self, bad_project_path, mock_client):
        """Las violaciones semánticas tienen tipos correctos del enum."""
        static = StaticAnalyzer(bad_project_path)
        report = static.analyze()

        semantic = SemanticAnalyzer(bad_project_path, mock_client)
        report = semantic.analyze(report)

        semantic_types = {
            "UNCLEAR_TEST_PURPOSE", "PAGE_OBJECT_DOES_TOO_MUCH",
            "IMPLICIT_TEST_DEPENDENCY", "MISSING_WAIT_STRATEGY",
        }
        found_semantic = [
            v for v in report.violations
            if v.violation_type.name in semantic_types
        ]
        # bad_project debería tener al menos alguna violación semántica
        assert len(found_semantic) > 0
