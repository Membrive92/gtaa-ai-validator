"""
Tests for gtaa_validator.models

Covers the core data model logic:
- Severity: penalties and ordering
- ViolationType: mappings to severity, description, recommendation
- Violation: auto-population of fields, serialization
- Report: score calculation, filtering, serialization
"""

import pytest
from pathlib import Path

from gtaa_validator.models import (
    Severity, ViolationType, Violation, Report, AnalysisMetrics
)


# =========================================================================
# Severity
# =========================================================================

class TestSeverity:
    """Tests for the Severity enum."""

    @pytest.mark.parametrize("severity, expected_penalty", [
        (Severity.CRITICAL, 10),
        (Severity.HIGH, 5),
        (Severity.MEDIUM, 2),
        (Severity.LOW, 1),
    ])
    def test_get_score_penalty(self, severity, expected_penalty):
        """Each severity level returns the correct penalty."""
        assert severity.get_score_penalty() == expected_penalty

    def test_ordering_critical_is_highest(self):
        """CRITICAL > HIGH > MEDIUM > LOW."""
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL

    def test_same_severity_not_less_than(self):
        """A severity is NOT less than itself."""
        for s in Severity:
            assert not (s < s)


# =========================================================================
# ViolationType
# =========================================================================

class TestViolationType:
    """Tests for the ViolationType enum."""

    def test_all_types_have_severity(self):
        """Every ViolationType maps to a valid Severity."""
        for vtype in ViolationType:
            severity = vtype.get_severity()
            assert isinstance(severity, Severity)

    @pytest.mark.parametrize("vtype, expected_severity", [
        (ViolationType.ADAPTATION_IN_DEFINITION, Severity.CRITICAL),
        (ViolationType.MISSING_LAYER_STRUCTURE, Severity.CRITICAL),
        (ViolationType.HARDCODED_TEST_DATA, Severity.HIGH),
        (ViolationType.ASSERTION_IN_POM, Severity.HIGH),
        (ViolationType.FORBIDDEN_IMPORT, Severity.HIGH),
        (ViolationType.BUSINESS_LOGIC_IN_POM, Severity.MEDIUM),
        (ViolationType.DUPLICATE_LOCATOR, Severity.MEDIUM),
        (ViolationType.LONG_TEST_FUNCTION, Severity.MEDIUM),
        (ViolationType.POOR_TEST_NAMING, Severity.LOW),
    ])
    def test_specific_severity_mapping(self, vtype, expected_severity):
        """Each type maps to its documented severity."""
        assert vtype.get_severity() == expected_severity

    def test_all_types_have_description(self):
        """Every ViolationType has a non-empty description."""
        for vtype in ViolationType:
            desc = vtype.get_description()
            assert isinstance(desc, str)
            assert len(desc) > 10

    def test_all_types_have_recommendation(self):
        """Every ViolationType has a non-empty recommendation."""
        for vtype in ViolationType:
            rec = vtype.get_recommendation()
            assert isinstance(rec, str)
            assert len(rec) > 10


# =========================================================================
# Violation
# =========================================================================

class TestViolation:
    """Tests for the Violation dataclass."""

    def test_auto_populates_severity(self):
        """If severity is falsy, __post_init__ fills it from ViolationType."""
        v = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=None,
            file_path=Path("test.py"),
        )
        assert v.severity == Severity.CRITICAL

    def test_auto_populates_message(self):
        """If message is empty, __post_init__ fills it from ViolationType."""
        v = Violation(
            violation_type=ViolationType.POOR_TEST_NAMING,
            severity=Severity.LOW,
            file_path=Path("test.py"),
        )
        assert len(v.message) > 0

    def test_auto_populates_recommendation(self):
        """If recommendation is empty, __post_init__ fills it from ViolationType."""
        v = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=Path("test.py"),
        )
        assert len(v.recommendation) > 0

    def test_explicit_values_preserved(self):
        """Explicitly provided values are NOT overwritten by __post_init__."""
        v = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.HIGH,  # Override default CRITICAL
            file_path=Path("test.py"),
            message="Custom message",
            recommendation="Custom recommendation",
        )
        assert v.severity == Severity.HIGH
        assert v.message == "Custom message"
        assert v.recommendation == "Custom recommendation"

    def test_to_dict_contains_all_fields(self):
        """to_dict() returns a dict with all expected keys."""
        v = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=Path("tests/test_login.py"),
            line_number=42,
            message="Some message",
            code_snippet="driver.find_element()",
            recommendation="Use Page Objects",
        )
        d = v.to_dict()

        assert d["type"] == "ADAPTATION_IN_DEFINITION"
        assert d["severity"] == "CRITICAL"
        assert d["file"] == str(Path("tests/test_login.py"))
        assert d["line"] == 42
        assert d["message"] == "Some message"
        assert d["code_snippet"] == "driver.find_element()"
        assert d["recommendation"] == "Use Page Objects"

    def test_to_dict_handles_none_line(self):
        """to_dict() handles line_number=None."""
        v = Violation(
            violation_type=ViolationType.MISSING_LAYER_STRUCTURE,
            severity=Severity.CRITICAL,
            file_path=Path("project"),
        )
        d = v.to_dict()
        assert d["line"] is None


# =========================================================================
# Report
# =========================================================================

class TestReport:
    """Tests for the Report dataclass."""

    # ----- Score calculation -----

    def test_score_no_violations(self, empty_report):
        """Score is 100.0 when there are no violations."""
        score = empty_report.calculate_score()
        assert score == 100.0
        assert empty_report.score == 100.0

    def test_score_single_critical(self, sample_critical_violation):
        """One CRITICAL violation → score = 90.0 (100 - 10)."""
        report = Report(
            project_path=Path("/fake"),
            violations=[sample_critical_violation],
        )
        assert report.calculate_score() == 90.0

    def test_score_mixed_violations(self, mixed_violations):
        """Mixed violations: 10 + 5 + 2 + 1 = 18 penalty → score = 82.0."""
        report = Report(
            project_path=Path("/fake"),
            violations=mixed_violations,
        )
        assert report.calculate_score() == 82.0

    def test_score_never_below_zero(self, sample_critical_violation):
        """Score floors at 0.0 even with massive penalties."""
        many_critical = [sample_critical_violation] * 20  # 20 * 10 = 200
        report = Report(
            project_path=Path("/fake"),
            violations=many_critical,
        )
        assert report.calculate_score() == 0.0

    # ----- Filtering -----

    def test_get_violations_by_severity(self, mixed_report):
        """Filtering returns only violations of the requested severity."""
        criticals = mixed_report.get_violations_by_severity(Severity.CRITICAL)
        assert len(criticals) == 1
        assert criticals[0].severity == Severity.CRITICAL

    def test_get_violations_by_severity_empty(self, empty_report):
        """Filtering on an empty report returns an empty list."""
        assert empty_report.get_violations_by_severity(Severity.CRITICAL) == []

    # ----- Count -----

    def test_get_violation_count_by_severity(self, mixed_report):
        """Count dict has correct values for each severity."""
        counts = mixed_report.get_violation_count_by_severity()
        assert counts == {
            "CRITICAL": 1,
            "HIGH": 1,
            "MEDIUM": 1,
            "LOW": 1,
        }

    def test_get_violation_count_empty(self, empty_report):
        """Count dict is all zeros for empty report."""
        counts = empty_report.get_violation_count_by_severity()
        assert counts == {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }

    # ----- Serialization -----

    def test_to_dict_structure(self, mixed_report):
        """to_dict() returns metadata, summary, and violations sections."""
        d = mixed_report.to_dict()

        assert "metadata" in d
        assert "summary" in d
        assert "violations" in d

        assert d["metadata"]["project_path"] == "project"
        assert d["summary"]["files_analyzed"] == 10
        assert d["summary"]["total_violations"] == 4
        assert len(d["violations"]) == 4

    def test_to_dict_score_included(self, mixed_report):
        """to_dict() includes the calculated score."""
        d = mixed_report.to_dict()
        assert d["summary"]["score"] == 82.0

    def test_to_dict_timestamp_is_iso(self, empty_report):
        """Timestamp in to_dict() is an ISO-format string."""
        d = empty_report.to_dict()
        ts = d["metadata"]["timestamp"]
        # ISO format includes 'T' separator
        assert "T" in ts or "-" in ts

    def test_to_dict_with_metrics(self, empty_report):
        """to_dict() includes metrics in metadata when present."""
        empty_report.metrics = AnalysisMetrics(
            static_analysis_seconds=1.5,
            total_seconds=2.0,
            files_per_second=10.0,
        )
        d = empty_report.to_dict()
        assert "metrics" in d["metadata"]
        assert d["metadata"]["metrics"]["timing"]["static_analysis_seconds"] == 1.5

    def test_to_dict_without_metrics(self, empty_report):
        """to_dict() does not include metrics when None."""
        assert empty_report.metrics is None
        d = empty_report.to_dict()
        assert "metrics" not in d["metadata"]


# =========================================================================
# AnalysisMetrics
# =========================================================================

class TestAnalysisMetrics:
    """Tests for the AnalysisMetrics dataclass."""

    def test_defaults_are_zero(self):
        """All fields default to zero."""
        m = AnalysisMetrics()
        assert m.static_analysis_seconds == 0.0
        assert m.semantic_analysis_seconds == 0.0
        assert m.llm_api_calls == 0
        assert m.llm_total_tokens == 0

    def test_to_dict_timing_section(self):
        """to_dict() always includes timing section."""
        m = AnalysisMetrics(
            static_analysis_seconds=1.234,
            semantic_analysis_seconds=2.567,
            report_generation_seconds=0.123,
            total_seconds=3.924,
            files_per_second=5.12,
        )
        d = m.to_dict()
        assert "timing" in d
        assert d["timing"]["static_analysis_seconds"] == 1.234
        assert d["timing"]["semantic_analysis_seconds"] == 2.567
        assert d["timing"]["report_generation_seconds"] == 0.123
        assert d["timing"]["total_seconds"] == 3.924
        assert d["timing"]["files_per_second"] == 5.12

    def test_to_dict_no_llm_section_when_zero_calls(self):
        """to_dict() omits llm section when llm_api_calls is 0."""
        m = AnalysisMetrics()
        d = m.to_dict()
        assert "llm" not in d

    def test_to_dict_llm_section_when_calls_present(self):
        """to_dict() includes llm section when llm_api_calls > 0."""
        m = AnalysisMetrics(
            llm_api_calls=3,
            llm_input_tokens=1500,
            llm_output_tokens=500,
            llm_total_tokens=2000,
            llm_estimated_cost_usd=0.003,
        )
        d = m.to_dict()
        assert "llm" in d
        assert d["llm"]["api_calls"] == 3
        assert d["llm"]["input_tokens"] == 1500
        assert d["llm"]["output_tokens"] == 500
        assert d["llm"]["total_tokens"] == 2000
        assert d["llm"]["estimated_cost_usd"] == 0.003

    def test_to_dict_rounds_values(self):
        """to_dict() rounds timing to 3 decimals and fps to 2."""
        m = AnalysisMetrics(
            static_analysis_seconds=1.23456789,
            files_per_second=12.3456,
        )
        d = m.to_dict()
        assert d["timing"]["static_analysis_seconds"] == 1.235
        assert d["timing"]["files_per_second"] == 12.35
