"""
Tests for gtaa_validator.checkers.base

Covers:
- BaseChecker: can_check(), check_project(), __repr__(), __str__()
"""

import pytest
from pathlib import Path

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation


class ConcreteChecker(BaseChecker):
    """Minimal concrete subclass for testing the base class."""

    def check(self, file_path, tree=None, file_type="unknown"):
        return []


class TestBaseChecker:
    """Tests for the BaseChecker abstract class."""

    def test_can_check_returns_true_for_python(self):
        """Default can_check() accepts .py files."""
        checker = ConcreteChecker()
        assert checker.can_check(Path("test_login.py")) is True

    def test_can_check_returns_false_for_non_python(self):
        """Default can_check() rejects non-.py files."""
        checker = ConcreteChecker()
        assert checker.can_check(Path("test_login.java")) is False

    def test_check_project_returns_empty_list(self):
        """Default check_project() returns empty list."""
        checker = ConcreteChecker()
        result = checker.check_project(Path("/fake/project"))
        assert result == []

    def test_repr_format(self):
        """__repr__() returns <ClassName> format."""
        checker = ConcreteChecker()
        assert repr(checker) == "<ConcreteChecker>"

    def test_name_attribute(self):
        """name attribute is set to class name."""
        checker = ConcreteChecker()
        assert checker.name == "ConcreteChecker"
