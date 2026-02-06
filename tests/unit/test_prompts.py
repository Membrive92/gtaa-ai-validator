"""
Tests for gtaa_validator.llm.prompts utility functions.

Covers:
- extract_context_snippet: context extraction around a violation line
- extract_functions_from_code: large file truncation to function signatures
"""

from gtaa_validator.llm.prompts import extract_context_snippet, extract_functions_from_code


class TestExtractContextSnippet:
    """Tests for extract_context_snippet()."""

    SAMPLE_CODE = "\n".join(f"line {i}" for i in range(1, 51))  # 50 lines

    def test_normal_line(self):
        """Middle line returns surrounding context."""
        result = extract_context_snippet(self.SAMPLE_CODE, line_number=25, context_lines=3)
        assert "line 25" in result
        assert "line 22" in result
        assert "line 28" in result

    def test_line_zero_returns_first_30(self):
        """line_number=0 (falsy) returns first 30 lines."""
        result = extract_context_snippet(self.SAMPLE_CODE, line_number=0)
        lines = result.split("\n")
        assert len(lines) == 30

    def test_first_line_no_negative_index(self):
        """line_number=1 does not produce negative indices."""
        result = extract_context_snippet(self.SAMPLE_CODE, line_number=1, context_lines=5)
        assert "line 1" in result
        # Should not crash or produce empty result
        assert len(result) > 0

    def test_highlighted_line_has_prefix(self):
        """The target line has '>>> ' prefix, others have '    '."""
        result = extract_context_snippet(self.SAMPLE_CODE, line_number=10, context_lines=2)
        for line in result.split("\n"):
            if "10:" in line:
                assert line.startswith(">>> ")
            else:
                assert line.startswith("    ")

    def test_last_line(self):
        """Context near the end of file does not crash."""
        result = extract_context_snippet(self.SAMPLE_CODE, line_number=50, context_lines=5)
        assert "line 50" in result


class TestExtractFunctionsFromCode:
    """Tests for extract_functions_from_code()."""

    def test_small_file_returned_unchanged(self):
        """Files smaller than max_chars are returned as-is."""
        code = "def foo():\n    pass\n"
        result = extract_functions_from_code(code, max_chars=3000)
        assert result == code

    def test_large_file_truncated(self):
        """Large files are reduced to function/class signatures."""
        # Generate a file larger than 3000 chars
        lines = []
        for i in range(100):
            lines.append(f"def test_func_{i}():")
            lines.append(f"    x = {i}")
            lines.append(f"    return x * 2")
            lines.append("")
        code = "\n".join(lines)
        assert len(code) > 3000

        result = extract_functions_from_code(code, max_chars=3000)
        assert len(result) <= 3000 + len("\n... [truncado]")
        assert "def test_func_0" in result

    def test_max_chars_respected(self):
        """Result does not exceed max_chars (plus truncation marker)."""
        code = "x = 1\n" * 1000  # Large file, no functions
        result = extract_functions_from_code(code, max_chars=500)
        # Should truncate to max_chars + truncation marker
        assert len(result) <= 500 + len("\n... [truncado]")
