"""
Tests for gtaa_validator.checkers.base

Covers:
- BaseChecker: can_check(), check_project(), __repr__(), name
- _is_test_file(): multi-language test file detection (Python, Java, JS/TS, C#)
- _is_test_function(): multi-language test function identification
- _get_config_for_extension(): extension-to-config dispatch
- ABC enforcement: cannot instantiate BaseChecker directly
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

from gtaa_validator.checkers.base import BaseChecker


@dataclass
class FakeFunction:
    """Minimal stand-in for ParsedFunction for unit tests."""
    name: str
    line_start: int = 1
    line_end: int = 10
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    is_async: bool = False


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

    def test_cannot_instantiate_base_directly(self):
        """BaseChecker is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseChecker()


# =========================================================================
# _is_test_file() — multi-language test file detection
# =========================================================================

class TestIsTestFile:
    """Tests for BaseChecker._is_test_file() multi-language detection."""

    def setup_method(self):
        self.checker = ConcreteChecker()

    # --- Python ---

    def test_python_prefix(self):
        """test_login.py → True (starts with test_)."""
        assert self.checker._is_test_file(Path("test_login.py")) is True

    def test_python_suffix(self):
        """login_test.py → True (ends with _test.py)."""
        assert self.checker._is_test_file(Path("login_test.py")) is True

    def test_python_in_tests_dir(self):
        """tests/helpers.py → True (tests directory)."""
        assert self.checker._is_test_file(Path("project/tests/helpers.py")) is True

    def test_python_regular_file(self):
        """utils/helper.py → False (no test pattern)."""
        assert self.checker._is_test_file(Path("utils/helper.py")) is False

    # --- Java ---

    def test_java_test_in_name(self):
        """LoginTest.java → True."""
        assert self.checker._is_test_file(Path("LoginTest.java")) is True

    def test_java_no_test(self):
        """Login.java → False."""
        assert self.checker._is_test_file(Path("Login.java")) is False

    def test_java_in_test_dir(self):
        """test/Login.java → True (test directory)."""
        assert self.checker._is_test_file(Path("src/test/Login.java")) is True

    # --- JavaScript/TypeScript ---

    def test_js_spec_file(self):
        """login.spec.ts → True."""
        assert self.checker._is_test_file(Path("login.spec.ts")) is True

    def test_js_test_file(self):
        """login.test.js → True."""
        assert self.checker._is_test_file(Path("login.test.js")) is True

    def test_js_tests_dir(self):
        """__tests__/helper.js → True."""
        assert self.checker._is_test_file(Path("__tests__/helper.js")) is True

    def test_js_regular_file(self):
        """app.js → False."""
        assert self.checker._is_test_file(Path("app.js")) is False

    def test_tsx_test_file(self):
        """Login.test.tsx → True."""
        assert self.checker._is_test_file(Path("Login.test.tsx")) is True

    def test_mjs_spec_file(self):
        """login.spec.mjs → True."""
        assert self.checker._is_test_file(Path("login.spec.mjs")) is True

    # --- C# ---

    def test_csharp_test_in_name(self):
        """LoginTest.cs → True."""
        assert self.checker._is_test_file(Path("LoginTest.cs")) is True

    def test_csharp_no_test(self):
        """Login.cs → False."""
        assert self.checker._is_test_file(Path("Login.cs")) is False

    # --- Unsupported ---

    def test_unsupported_extension(self):
        """script.rb → False (not supported)."""
        assert self.checker._is_test_file(Path("test_script.rb")) is False

    def test_markdown_not_test(self):
        """README.md → False."""
        assert self.checker._is_test_file(Path("README.md")) is False


# =========================================================================
# _is_test_function() — multi-language test function identification
# =========================================================================

class TestIsTestFunction:
    """Tests for BaseChecker._is_test_function() method."""

    def setup_method(self):
        self.checker = ConcreteChecker()

    def test_python_test_func(self):
        """test_foo → True for .py."""
        func = FakeFunction(name="test_foo")
        assert self.checker._is_test_function(func, ".py") is True

    def test_python_helper_func(self):
        """helper_func → False for .py."""
        func = FakeFunction(name="helper_func")
        assert self.checker._is_test_function(func, ".py") is False

    def test_java_test_annotation(self):
        """@Test → True for .java."""
        func = FakeFunction(name="shouldLogin", decorators=["Test"])
        assert self.checker._is_test_function(func, ".java") is True

    def test_java_parameterized_test(self):
        """@ParameterizedTest → True for .java."""
        func = FakeFunction(name="testWith", decorators=["ParameterizedTest"])
        assert self.checker._is_test_function(func, ".java") is True

    def test_java_override_not_test(self):
        """@Override → False for .java."""
        func = FakeFunction(name="setUp", decorators=["Override"])
        assert self.checker._is_test_function(func, ".java") is False

    def test_csharp_fact(self):
        """@Fact → True for .cs."""
        func = FakeFunction(name="ShouldLogin", decorators=["Fact"])
        assert self.checker._is_test_function(func, ".cs") is True

    def test_csharp_theory(self):
        """@Theory → True for .cs."""
        func = FakeFunction(name="ShouldLogin", decorators=["Theory"])
        assert self.checker._is_test_function(func, ".cs") is True

    def test_csharp_test_method(self):
        """@TestMethod → True for .cs."""
        func = FakeFunction(name="TestLogin", decorators=["TestMethod"])
        assert self.checker._is_test_function(func, ".cs") is True

    def test_js_it_function(self):
        """it → True for .js."""
        func = FakeFunction(name="it")
        assert self.checker._is_test_function(func, ".js") is True

    def test_js_test_function(self):
        """test → True for .js."""
        func = FakeFunction(name="test")
        assert self.checker._is_test_function(func, ".js") is True

    def test_js_describe_not_test(self):
        """describe → False for .js."""
        func = FakeFunction(name="describe")
        assert self.checker._is_test_function(func, ".js") is False

    def test_unsupported_extension(self):
        """Unknown extension → False."""
        func = FakeFunction(name="test_foo")
        assert self.checker._is_test_function(func, ".rb") is False


# =========================================================================
# _get_config_for_extension() — extension dispatch
# =========================================================================

class TestGetConfigForExtension:
    """Tests for BaseChecker._get_config_for_extension() static method."""

    def test_python_extension(self):
        """.py maps to 'py' key."""
        config = {"py": "python_config"}
        assert BaseChecker._get_config_for_extension(".py", config) == "python_config"

    def test_typescript_normalizes_to_js(self):
        """.ts maps to 'js' key."""
        config = {"js": "js_config"}
        assert BaseChecker._get_config_for_extension(".ts", config) == "js_config"

    def test_tsx_normalizes_to_js(self):
        """.tsx maps to 'js' key."""
        config = {"js": "js_config"}
        assert BaseChecker._get_config_for_extension(".tsx", config) == "js_config"

    def test_mjs_normalizes_to_js(self):
        """.mjs maps to 'js' key."""
        config = {"js": "js_config"}
        assert BaseChecker._get_config_for_extension(".mjs", config) == "js_config"

    def test_java_extension(self):
        """.java maps to 'java' key."""
        config = {"java": "java_config"}
        assert BaseChecker._get_config_for_extension(".java", config) == "java_config"

    def test_csharp_extension(self):
        """.cs maps to 'cs' key."""
        config = {"cs": "cs_config"}
        assert BaseChecker._get_config_for_extension(".cs", config) == "cs_config"

    def test_unknown_with_default(self):
        """Unknown extension falls back to 'default' key."""
        config = {"py": "python", "default": "fallback"}
        assert BaseChecker._get_config_for_extension(".unknown", config) == "fallback"

    def test_unknown_without_default(self):
        """Unknown extension without 'default' key returns empty set()."""
        config = {"py": "python"}
        assert BaseChecker._get_config_for_extension(".unknown", config) == set()
