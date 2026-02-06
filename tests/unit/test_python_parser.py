"""
Tests for gtaa_validator.parsers.python_parser

Covers:
- PythonParser.parse(): syntax errors, general exceptions
- PythonParser.parse_file(): nonexistent file, empty file, normal file
- Class with ast.Attribute base (e.g. class Foo(base.Bar))
- Complex decorators (@Name, @module.attr, @call())
- Call extraction with ast.unparse fallback
- Return None for unnamed calls (subscript, etc.)
- _get_attribute_name() for chained attributes (a.b.c)
- _get_root_object() with self.driver, chained calls
- Utility methods: is_test_function, is_fixture, is_bdd_step
- Import detection: selenium, playwright, test frameworks
- get_python_parser() factory function
"""

import pytest
from pathlib import Path

from gtaa_validator.parsers.python_parser import PythonParser, get_python_parser
from gtaa_validator.parsers.treesitter_base import ParsedFunction, ParsedImport


class TestPythonParserParse:
    """Tests for PythonParser.parse() method."""

    def test_parse_valid_python(self):
        """Valid Python source is parsed without errors."""
        parser = PythonParser()
        result = parser.parse("x = 1\n")
        assert result.parse_errors == []
        assert result.language == "python"

    def test_parse_syntax_error(self):
        """Syntax error produces a parse_errors entry."""
        parser = PythonParser()
        result = parser.parse("def foo(:\n")
        assert len(result.parse_errors) == 1
        assert "sintaxis" in result.parse_errors[0].lower() or "syntax" in result.parse_errors[0].lower()

    def test_parse_empty_source(self):
        """Empty source parses successfully with no data."""
        parser = PythonParser()
        result = parser.parse("")
        assert result.parse_errors == []
        assert result.classes == []
        assert result.functions == []

    def test_parse_extracts_imports(self):
        """Imports are correctly extracted."""
        parser = PythonParser()
        source = "import os\nfrom pathlib import Path\n"
        result = parser.parse(source)
        modules = [imp.module for imp in result.imports]
        assert "os" in modules
        assert "pathlib" in modules
        assert "pathlib.Path" in modules

    def test_parse_extracts_import_alias(self):
        """Import alias is captured."""
        parser = PythonParser()
        result = parser.parse("import numpy as np\n")
        assert result.imports[0].alias == "np"

    def test_parse_import_from_with_no_module(self):
        """from . import X (module=None) is skipped."""
        parser = PythonParser()
        result = parser.parse("from . import foo\n")
        # Relative import with no module name should not crash
        assert result.parse_errors == []


class TestPythonParserParseFile:
    """Tests for PythonParser.parse_file() method."""

    def test_parse_file_normal(self, tmp_path):
        """Normal Python file is parsed correctly."""
        f = tmp_path / "example.py"
        f.write_text("class Foo:\n    pass\n", encoding="utf-8")
        parser = PythonParser()
        result = parser.parse_file(f)
        assert result.parse_errors == []
        assert len(result.classes) == 1
        assert result.classes[0].name == "Foo"

    def test_parse_file_empty(self, tmp_path):
        """Empty file returns parse error about empty file."""
        f = tmp_path / "empty.py"
        f.write_text("", encoding="utf-8")
        parser = PythonParser()
        result = parser.parse_file(f)
        assert len(result.parse_errors) == 1
        assert "vacio" in result.parse_errors[0].lower() or "empty" in result.parse_errors[0].lower()

    def test_parse_file_nonexistent(self):
        """Nonexistent file returns parse error."""
        parser = PythonParser()
        result = parser.parse_file(Path("/nonexistent/file.py"))
        # read_file_safe returns "" for nonexistent files → triggers empty check
        assert len(result.parse_errors) >= 1


class TestClassExtraction:
    """Tests for class parsing, including inheritance."""

    def test_class_with_simple_base(self):
        """Class with a simple base class (ast.Name)."""
        parser = PythonParser()
        source = "class LoginPage(BasePage):\n    pass\n"
        result = parser.parse(source)
        assert len(result.classes) == 1
        assert "BasePage" in result.classes[0].base_classes

    def test_class_with_attribute_base(self):
        """Class with dotted base class (ast.Attribute), e.g. base.BasePage."""
        parser = PythonParser()
        source = "class LoginPage(pages.base.BasePage):\n    pass\n"
        result = parser.parse(source)
        cls = result.classes[0]
        assert "pages.base.BasePage" in cls.base_classes

    def test_class_page_object_detection(self):
        """Class with 'Page' in name or base is detected as page object."""
        parser = PythonParser()
        source = "class LoginPage:\n    pass\n"
        result = parser.parse(source)
        assert result.classes[0].is_page_object is True

    def test_class_not_page_object(self):
        """Class without 'Page' in name or base is not a page object."""
        parser = PythonParser()
        source = "class TestLogin:\n    pass\n"
        result = parser.parse(source)
        assert result.classes[0].is_page_object is False

    def test_class_page_object_by_base(self):
        """Class inheriting from *Page* base is detected as page object."""
        parser = PythonParser()
        source = "class Login(BasePage):\n    pass\n"
        result = parser.parse(source)
        assert result.classes[0].is_page_object is True

    def test_class_methods_extracted(self):
        """Methods inside a class are extracted."""
        parser = PythonParser()
        source = (
            "class Foo:\n"
            "    def bar(self):\n"
            "        pass\n"
            "    async def baz(self):\n"
            "        pass\n"
        )
        result = parser.parse(source)
        methods = result.classes[0].methods
        assert len(methods) == 2
        names = [m.name for m in methods]
        assert "bar" in names
        assert "baz" in names
        # Async detection
        baz = [m for m in methods if m.name == "baz"][0]
        assert baz.is_async is True


class TestFunctionExtraction:
    """Tests for top-level function and decorator extraction."""

    def test_top_level_function(self):
        """Top-level function is extracted."""
        parser = PythonParser()
        source = "def test_login():\n    pass\n"
        result = parser.parse(source)
        assert len(result.functions) == 1
        assert result.functions[0].name == "test_login"

    def test_async_function(self):
        """Async function is marked as async."""
        parser = PythonParser()
        source = "async def test_async():\n    pass\n"
        result = parser.parse(source)
        assert result.functions[0].is_async is True

    def test_decorator_simple_name(self):
        """Simple decorator @name is captured."""
        parser = PythonParser()
        source = "@fixture\ndef setup():\n    pass\n"
        result = parser.parse(source)
        assert "fixture" in result.functions[0].decorators

    def test_decorator_attribute(self):
        """Dotted decorator @module.attr is captured."""
        parser = PythonParser()
        source = "@pytest.fixture\ndef setup():\n    pass\n"
        result = parser.parse(source)
        assert "pytest.fixture" in result.functions[0].decorators

    def test_decorator_call_simple(self):
        """Decorator with call @name() is captured."""
        parser = PythonParser()
        source = "@fixture(scope='session')\ndef setup():\n    pass\n"
        result = parser.parse(source)
        assert "fixture" in result.functions[0].decorators

    def test_decorator_call_attribute(self):
        """Decorator with dotted call @pytest.mark.parametrize() is captured."""
        parser = PythonParser()
        source = "@pytest.mark.parametrize('x', [1,2])\ndef test_param(x):\n    pass\n"
        result = parser.parse(source)
        assert "pytest.mark.parametrize" in result.functions[0].decorators

    def test_function_parameters(self):
        """Function parameters are extracted."""
        parser = PythonParser()
        source = "def test_login(self, driver, page):\n    pass\n"
        result = parser.parse(source)
        assert result.functions[0].parameters == ["self", "driver", "page"]


class TestCallExtraction:
    """Tests for method/function call extraction."""

    def test_simple_function_call(self):
        """Simple function call (ast.Name) is extracted."""
        parser = PythonParser()
        source = "print('hello')\n"
        result = parser.parse(source)
        calls = [c for c in result.calls if c.method_name == "print"]
        assert len(calls) == 1
        assert calls[0].object_name == ""

    def test_method_call(self):
        """Method call (ast.Attribute) is extracted with object name."""
        parser = PythonParser()
        source = "driver.find_element('id', 'x')\n"
        result = parser.parse(source)
        calls = [c for c in result.calls if c.method_name == "find_element"]
        assert len(calls) == 1
        assert calls[0].object_name == "driver"

    def test_chained_call(self):
        """Chained method call extracts root object."""
        parser = PythonParser()
        source = "driver.find_element('id', 'x').click()\n"
        result = parser.parse(source)
        click_calls = [c for c in result.calls if c.method_name == "click"]
        assert len(click_calls) == 1
        assert click_calls[0].object_name == "driver"

    def test_self_driver_call(self):
        """self.driver.method() resolves to 'driver' as root object."""
        parser = PythonParser()
        source = (
            "class Page:\n"
            "    def click_btn(self):\n"
            "        self.driver.find_element('id', 'btn').click()\n"
        )
        result = parser.parse(source)
        fe_calls = [c for c in result.calls if c.method_name == "find_element"]
        assert len(fe_calls) == 1
        assert fe_calls[0].object_name == "driver"

    def test_unnamed_call_returns_none(self):
        """Call with no extractable name (e.g. subscript) returns None → skipped."""
        parser = PythonParser()
        # handlers[0]() — func is ast.Subscript, not Name/Attribute
        source = "handlers[0]()\n"
        result = parser.parse(source)
        # The subscript call should be filtered out (returns None)
        sub_calls = [c for c in result.calls if c.method_name == ""]
        assert len(sub_calls) == 0

    def test_call_full_text(self):
        """full_text is populated via ast.unparse."""
        parser = PythonParser()
        source = "print('hello')\n"
        result = parser.parse(source)
        calls = [c for c in result.calls if c.method_name == "print"]
        assert calls[0].full_text != ""


class TestStringExtraction:
    """Tests for string literal extraction."""

    def test_strings_extracted(self):
        """String constants are extracted."""
        parser = PythonParser()
        source = "x = 'hello'\ny = 42\nz = 'world'\n"
        result = parser.parse(source)
        values = [s.value for s in result.strings]
        assert "hello" in values
        assert "world" in values
        # Integer constant should NOT appear as string
        assert 42 not in values

    def test_no_integer_strings(self):
        """Non-string constants (int, float) are not captured."""
        parser = PythonParser()
        source = "x = 42\ny = 3.14\nz = True\n"
        result = parser.parse(source)
        assert result.strings == []


class TestGetAttributeName:
    """Tests for _get_attribute_name() with chained attributes."""

    def test_simple_attribute(self):
        """Single-level attribute: module.Class → 'module.Class'."""
        parser = PythonParser()
        source = "class Foo(base.Bar):\n    pass\n"
        result = parser.parse(source)
        assert "base.Bar" in result.classes[0].base_classes

    def test_deep_chain(self):
        """Multi-level attribute: a.b.c.D → 'a.b.c.D'."""
        parser = PythonParser()
        source = "class Foo(a.b.c.D):\n    pass\n"
        result = parser.parse(source)
        assert "a.b.c.D" in result.classes[0].base_classes


class TestUtilityMethods:
    """Tests for is_test_function, is_fixture, is_bdd_step."""

    def setup_method(self):
        self.parser = PythonParser()

    def test_is_test_function_true(self):
        """Function starting with test_ is a test."""
        func = ParsedFunction(name="test_login", line_start=1, line_end=5)
        assert self.parser.is_test_function(func) is True

    def test_is_test_function_false(self):
        """Function not starting with test_ is not a test."""
        func = ParsedFunction(name="setup_browser", line_start=1, line_end=5)
        assert self.parser.is_test_function(func) is False

    def test_is_fixture_pytest(self):
        """Function with @pytest.fixture decorator is a fixture."""
        func = ParsedFunction(
            name="browser", line_start=1, line_end=5,
            decorators=["pytest.fixture"]
        )
        assert self.parser.is_fixture(func) is True

    def test_is_fixture_short_name(self):
        """Function with @fixture decorator is a fixture."""
        func = ParsedFunction(
            name="browser", line_start=1, line_end=5,
            decorators=["fixture"]
        )
        assert self.parser.is_fixture(func) is True

    def test_is_fixture_false(self):
        """Function without fixture decorator is not a fixture."""
        func = ParsedFunction(
            name="browser", line_start=1, line_end=5,
            decorators=["staticmethod"]
        )
        assert self.parser.is_fixture(func) is False

    def test_is_bdd_step_given(self):
        """Function with @given decorator is a BDD step."""
        func = ParsedFunction(
            name="step_impl", line_start=1, line_end=5,
            decorators=["given"]
        )
        assert self.parser.is_bdd_step(func) is True

    def test_is_bdd_step_when(self):
        """Function with @when decorator is a BDD step."""
        func = ParsedFunction(
            name="step_impl", line_start=1, line_end=5,
            decorators=["when"]
        )
        assert self.parser.is_bdd_step(func) is True

    def test_is_bdd_step_false(self):
        """Function without BDD decorator is not a step."""
        func = ParsedFunction(
            name="step_impl", line_start=1, line_end=5,
            decorators=["fixture"]
        )
        assert self.parser.is_bdd_step(func) is False


class TestImportDetection:
    """Tests for has_selenium_imports, has_playwright_imports, has_test_framework_imports."""

    def setup_method(self):
        self.parser = PythonParser()

    def test_has_selenium_imports_true(self):
        """Detects selenium imports."""
        imports = [ParsedImport(module="selenium.webdriver", line=1)]
        assert self.parser.has_selenium_imports(imports) is True

    def test_has_selenium_imports_false(self):
        """No selenium imports returns False."""
        imports = [ParsedImport(module="requests", line=1)]
        assert self.parser.has_selenium_imports(imports) is False

    def test_has_playwright_imports_true(self):
        """Detects playwright imports."""
        imports = [ParsedImport(module="playwright.sync_api", line=1)]
        assert self.parser.has_playwright_imports(imports) is True

    def test_has_playwright_imports_false(self):
        """No playwright imports returns False."""
        imports = [ParsedImport(module="selenium", line=1)]
        assert self.parser.has_playwright_imports(imports) is False

    def test_has_test_framework_imports_pytest(self):
        """Detects pytest imports."""
        imports = [ParsedImport(module="pytest", line=1)]
        assert self.parser.has_test_framework_imports(imports) is True

    def test_has_test_framework_imports_unittest(self):
        """Detects unittest imports."""
        imports = [ParsedImport(module="unittest.mock", line=1)]
        assert self.parser.has_test_framework_imports(imports) is True

    def test_has_test_framework_imports_false(self):
        """Non-test imports return False."""
        imports = [ParsedImport(module="os", line=1)]
        assert self.parser.has_test_framework_imports(imports) is False

    def test_has_test_framework_empty(self):
        """Empty imports list returns False."""
        assert self.parser.has_test_framework_imports([]) is False


class TestGetPythonParserFactory:
    """Tests for the get_python_parser() factory function."""

    def test_returns_python_parser_instance(self):
        """Factory returns a PythonParser instance."""
        parser = get_python_parser()
        assert isinstance(parser, PythonParser)

    def test_language_is_python(self):
        """Returned parser has language='python'."""
        parser = get_python_parser()
        assert parser.language == "python"
