"""
Tests for gtaa_validator.file_utils

Covers:
- read_file_safe(): size limit, OSError handling, normal read, stat failure
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from gtaa_validator.file_utils import read_file_safe


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

