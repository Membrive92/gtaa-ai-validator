"""
Tests for gtaa_validator.file_utils

Covers:
- read_file_safe(): size limit, OSError handling, normal read, stat failure
- safe_relative_path(): path within base, outside base, identical paths (SEC-03)
- Boundary: exact size limit (> vs >=)
- Unicode content handling
"""

from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from gtaa_validator.file_utils import read_file_safe, safe_relative_path, MAX_FILE_SIZE_BYTES


class TestReadFileSafe:
    """Tests for the read_file_safe() function."""

    def test_reads_normal_file(self, tmp_path):
        """Normal file is read correctly."""
        f = tmp_path / "hello.py"
        f.write_text("print('hello')", encoding="utf-8")
        assert read_file_safe(f) == "print('hello')"

    def test_rejects_file_exceeding_size_limit(self, tmp_path):
        """File larger than max_size returns empty string."""
        f = tmp_path / "big.py"
        f.write_text("x" * 100, encoding="utf-8")
        # Use a very small limit
        result = read_file_safe(f, max_size=10)
        assert result == ""

    def test_returns_empty_on_oserror_during_read(self):
        """OSError during open/read returns empty string."""
        fake_path = MagicMock(spec=Path)
        fake_path.stat.return_value = MagicMock(st_size=100)
        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = read_file_safe(fake_path)
        assert result == ""

    def test_stat_failure_still_attempts_read(self):
        """If stat() raises OSError, still tries to read the file."""
        fake_path = MagicMock(spec=Path)
        fake_path.stat.side_effect = OSError("no such file")
        m = mock_open(read_data="content from mock")
        with patch("builtins.open", m):
            result = read_file_safe(fake_path)
        assert result == "content from mock"

    def test_empty_file_returns_empty_string(self, tmp_path):
        """Empty file returns empty string."""
        f = tmp_path / "empty.py"
        f.write_text("", encoding="utf-8")
        assert read_file_safe(f) == ""

    def test_file_at_exact_size_limit(self, tmp_path):
        """File at exactly max_size is NOT rejected (> not >=)."""
        f = tmp_path / "exact.py"
        content = "x" * 50
        f.write_text(content, encoding="utf-8")
        # max_size equals file size exactly → should be read (> check)
        size = f.stat().st_size
        result = read_file_safe(f, max_size=size)
        assert result == content

    def test_nonexistent_file_returns_empty(self, tmp_path):
        """Path to nonexistent file returns empty string."""
        f = tmp_path / "nonexistent.py"
        result = read_file_safe(f)
        assert result == ""

    def test_unicode_file_content(self, tmp_path):
        """Non-ASCII content is read correctly."""
        f = tmp_path / "unicode.py"
        content = '# Verificación de módulo con acentos: ñ, ü, é\nprint("café")'
        f.write_text(content, encoding="utf-8")
        result = read_file_safe(f)
        assert "café" in result
        assert "ñ" in result


# =========================================================================
# safe_relative_path() — SEC-03
# =========================================================================

class TestSafeRelativePath:
    """Tests for safe_relative_path() — SEC-03 path sanitization."""

    def test_path_within_base(self):
        """File inside base directory returns relative path."""
        base = Path("/project")
        file = Path("/project/tests/test_login.py")
        result = safe_relative_path(file, base)
        assert result == Path("tests/test_login.py")

    def test_path_outside_base(self):
        """File outside base directory returns original path (ValueError catch)."""
        base = Path("/project")
        file = Path("/other/location/test.py")
        result = safe_relative_path(file, base)
        assert result == file  # Returns original, does not crash

    def test_identical_paths(self):
        """Same path as base returns '.' (relative to itself)."""
        base = Path("/project")
        result = safe_relative_path(base, base)
        assert result == Path(".")
