"""
Tests for gtaa_validator.classifier

Covers:
- FileClassifier.classify(): file classification by imports, code patterns, and path
- API detection, UI detection, mixed files, unknown files
"""

import ast
import pytest
from pathlib import Path

from gtaa_validator.file_classifier import FileClassifier
from gtaa_validator.parsers.treesitter_base import (
    ParseResult, ParsedImport, ParsedFunction, ParsedClass,
)


@pytest.fixture
def classifier():
    """Fresh FileClassifier instance."""
    return FileClassifier()


def _parse(source: str) -> ast.Module:
    """Helper to parse source code into AST."""
    return ast.parse(source)


# =========================================================================
# API file detection
# =========================================================================

class TestAPIDetection:
    """Files with API imports/patterns should be classified as 'api'."""

    def test_requests_import(self, classifier):
        source = "import requests\n\ndef test_get(): pass\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"

    def test_httpx_import(self, classifier):
        source = "import httpx\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"

    def test_aiohttp_import(self, classifier):
        source = "import aiohttp\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"

    def test_from_requests_import(self, classifier):
        source = "from requests import Session\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"

    def test_fastapi_import(self, classifier):
        source = "from fastapi.testclient import TestClient\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"

    def test_flask_import(self, classifier):
        source = "from flask import Flask\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"

    def test_rest_framework_import(self, classifier):
        source = "from rest_framework.test import APIClient\n"
        result = classifier.classify(Path("test_api.py"), source, _parse(source))
        assert result == "api"


# =========================================================================
# API code patterns (regex)
# =========================================================================

class TestAPICodePatterns:
    """API code patterns in source should boost API score."""

    def test_status_code_pattern(self, classifier):
        source = "response.status_code\n"
        result = classifier.classify(Path("test_foo.py"), source, _parse(source))
        assert result == "api"

    def test_json_call_pattern(self, classifier):
        source = "data = response.json()\n"
        result = classifier.classify(Path("test_foo.py"), source, _parse(source))
        assert result == "api"

    def test_http_method_pattern(self, classifier):
        source = "client.get('/api/users')\n"
        result = classifier.classify(Path("test_foo.py"), source, _parse(source))
        assert result == "api"

    def test_status_code_comparison(self, classifier):
        source = "assert status_code == 200\n"
        result = classifier.classify(Path("test_foo.py"), source, _parse(source))
        assert result == "api"


# =========================================================================
# API path patterns
# =========================================================================

class TestAPIPathPatterns:
    """Path patterns should indicate API tests."""

    def test_api_directory(self, classifier):
        source = "x = 1\n"
        result = classifier.classify(Path("tests/api/test_users.py"), source, _parse(source))
        assert result == "api"

    def test_test_api_prefix(self, classifier):
        source = "x = 1\n"
        result = classifier.classify(Path("test_api_users.py"), source, _parse(source))
        assert result == "api"

    def test_api_test_suffix(self, classifier):
        source = "x = 1\n"
        result = classifier.classify(Path("users_api_test.py"), source, _parse(source))
        assert result == "api"


# =========================================================================
# UI file detection
# =========================================================================

class TestUIDetection:
    """Files with UI imports should be classified as 'ui'."""

    def test_selenium_import(self, classifier):
        source = "from selenium import webdriver\n"
        result = classifier.classify(Path("test_login.py"), source, _parse(source))
        assert result == "ui"

    def test_playwright_import(self, classifier):
        source = "from playwright.sync_api import Page\n"
        result = classifier.classify(Path("test_login.py"), source, _parse(source))
        assert result == "ui"


# =========================================================================
# Mixed files — UI wins (conservative)
# =========================================================================

class TestMixedDetection:
    """Files with both API and UI signals should classify as 'ui' (conservative)."""

    def test_mixed_imports_ui_wins(self, classifier):
        source = "import requests\nfrom selenium import webdriver\n"
        result = classifier.classify(Path("test_mixed.py"), source, _parse(source))
        assert result == "ui"

    def test_api_patterns_plus_ui_import(self, classifier):
        source = "from selenium import webdriver\nresponse.status_code\n"
        result = classifier.classify(Path("test_mixed.py"), source, _parse(source))
        assert result == "ui"


# =========================================================================
# Unknown files
# =========================================================================

class TestUnknownDetection:
    """Files without API or UI signals should be 'unknown'."""

    def test_no_signals(self, classifier):
        source = "def test_something():\n    assert True\n"
        result = classifier.classify(Path("test_something.py"), source, _parse(source))
        assert result == "unknown"

    def test_unrelated_imports(self, classifier):
        source = "import os\nimport json\n"
        result = classifier.classify(Path("test_foo.py"), source, _parse(source))
        assert result == "unknown"


# =========================================================================
# classify_detailed() and framework detection
# =========================================================================

class TestClassifyDetailed:
    """classify_detailed() returns ClassificationResult with frameworks."""

    def test_playwright_detected_as_framework(self, classifier):
        source = "from playwright.sync_api import Page\n"
        result = classifier.classify_detailed(Path("test_login.py"), source, _parse(source))
        assert result.file_type == "ui"
        assert "playwright" in result.frameworks

    def test_playwright_has_auto_wait(self, classifier):
        source = "from playwright.sync_api import Page\n"
        result = classifier.classify_detailed(Path("test_login.py"), source, _parse(source))
        assert result.has_auto_wait is True

    def test_selenium_no_auto_wait(self, classifier):
        source = "from selenium import webdriver\n"
        result = classifier.classify_detailed(Path("test_login.py"), source, _parse(source))
        assert result.file_type == "ui"
        assert "selenium" in result.frameworks
        assert result.has_auto_wait is False

    def test_api_no_auto_wait(self, classifier):
        source = "import requests\n"
        result = classifier.classify_detailed(Path("test_api.py"), source, _parse(source))
        assert result.file_type == "api"
        assert result.has_auto_wait is False

    def test_unknown_no_auto_wait(self, classifier):
        source = "x = 1\n"
        result = classifier.classify_detailed(Path("test_foo.py"), source, _parse(source))
        assert result.has_auto_wait is False

    def test_mixed_playwright_and_selenium(self, classifier):
        source = "from playwright.sync_api import Page\nfrom selenium import webdriver\n"
        result = classifier.classify_detailed(Path("test_mixed.py"), source, _parse(source))
        assert result.file_type == "ui"
        assert result.has_auto_wait is True  # Playwright present → auto-wait


# =========================================================================
# No tree/result fallback (lines 177-184)
# =========================================================================

class TestNoTreeFallback:
    """classify_detailed() without tree/result parses source as Python."""

    def test_classify_without_tree_parses_python(self, classifier):
        """When tree_or_result is None and ext is .py, auto-parses."""
        source = "import requests\ndef test_api(): pass\n"
        result = classifier.classify(Path("test_api.py"), source, None)
        assert result == "api"

    def test_classify_without_tree_syntax_error(self, classifier):
        """SyntaxError in source when no tree falls back to pattern matching."""
        source = "def @@invalid syntax\n"
        result = classifier.classify(Path("test_foo.py"), source, None)
        assert result == "unknown"


# =========================================================================
# Page Object detection by path (lines 339-401)
# =========================================================================

class TestPageObjectPathDetection:
    """_is_page_object_path() for multi-language file paths."""

    def test_java_page_file(self, classifier):
        result = classifier._is_page_object_path(Path("src/pages/LoginPage.java"))
        assert result is True

    def test_js_page_file(self, classifier):
        result = classifier._is_page_object_path(Path("src/pages/login.page.js"))
        assert result is True

    def test_cs_page_file(self, classifier):
        result = classifier._is_page_object_path(Path("src/pages/LoginPage.cs"))
        assert result is True

    def test_page_in_test_dir_not_page_object(self, classifier):
        """Files in test directories are NOT page objects."""
        result = classifier._is_page_object_path(Path("tests/pages/LoginPage.py"))
        assert result is False

    def test_pom_directory(self, classifier):
        result = classifier._is_page_object_path(Path("pom/login.py"))
        assert result is True


# =========================================================================
# Test file path detection (lines 364-401)
# =========================================================================

class TestTestFilePathDetection:
    """_is_test_file_path() for multi-language test files."""

    def test_java_test_file(self, classifier):
        assert classifier._is_test_file_path(Path("LoginTest.java"), ".java") is True

    def test_java_tests_file(self, classifier):
        assert classifier._is_test_file_path(Path("LoginTests.java"), ".java") is True

    def test_java_non_test_file(self, classifier):
        assert classifier._is_test_file_path(Path("LoginPage.java"), ".java") is False

    def test_js_spec_file(self, classifier):
        assert classifier._is_test_file_path(Path("login.spec.js"), ".js") is True

    def test_ts_test_file(self, classifier):
        assert classifier._is_test_file_path(Path("login.test.ts"), ".ts") is True

    def test_js_in_tests_dir(self, classifier):
        assert classifier._is_test_file_path(Path("tests/login.js"), ".js") is True

    def test_js_non_test_file(self, classifier):
        assert classifier._is_test_file_path(Path("src/utils.js"), ".js") is False

    def test_cs_test_file(self, classifier):
        assert classifier._is_test_file_path(Path("LoginTest.cs"), ".cs") is True

    def test_cs_tests_file(self, classifier):
        assert classifier._is_test_file_path(Path("LoginTests.cs"), ".cs") is True

    def test_cs_non_test_file(self, classifier):
        assert classifier._is_test_file_path(Path("LoginPage.cs"), ".cs") is False

    def test_unknown_extension(self, classifier):
        assert classifier._is_test_file_path(Path("test.rb"), ".rb") is False


# =========================================================================
# Test function detection (lines 317-337)
# =========================================================================

class TestTestFunctionDetection:
    """_is_test_function() for multi-language test methods."""

    def test_python_test_function(self, classifier):
        assert classifier._is_test_function("test_login", [], ".py") is True

    def test_python_non_test_function(self, classifier):
        assert classifier._is_test_function("login", [], ".py") is False

    def test_java_test_annotation(self, classifier):
        assert classifier._is_test_function("loginTest", ["Test"], ".java") is True

    def test_java_parameterized_test(self, classifier):
        assert classifier._is_test_function("loginTest", ["ParameterizedTest"], ".java") is True

    def test_java_no_test_annotation(self, classifier):
        assert classifier._is_test_function("setup", ["Before"], ".java") is False

    def test_csharp_test_attribute(self, classifier):
        assert classifier._is_test_function("LoginTest", ["Test"], ".cs") is True

    def test_csharp_fact_attribute(self, classifier):
        assert classifier._is_test_function("LoginTest", ["Fact"], ".cs") is True

    def test_csharp_theory_attribute(self, classifier):
        assert classifier._is_test_function("LoginTest", ["Theory"], ".cs") is True

    def test_csharp_no_test_attribute(self, classifier):
        assert classifier._is_test_function("Setup", ["SetUp"], ".cs") is False

    def test_js_it_function(self, classifier):
        assert classifier._is_test_function("it", [], ".js") is True

    def test_js_test_function(self, classifier):
        assert classifier._is_test_function("test", [], ".ts") is True

    def test_js_test_prefix(self, classifier):
        assert classifier._is_test_function("testLogin", [], ".tsx") is True

    def test_js_non_test_function(self, classifier):
        assert classifier._is_test_function("setup", [], ".js") is False

    def test_unknown_extension(self, classifier):
        assert classifier._is_test_function("test_x", [], ".rb") is False


# =========================================================================
# Import set getters (lines 403-449)
# =========================================================================

class TestImportSetGetters:
    """_get_*_imports_for_language() return correct sets."""

    def test_api_imports_java(self, classifier):
        result = classifier._get_api_imports_for_language(".java")
        assert "io.restassured" in result

    def test_api_imports_js(self, classifier):
        result = classifier._get_api_imports_for_language(".js")
        assert "axios" in result

    def test_api_imports_cs(self, classifier):
        result = classifier._get_api_imports_for_language(".cs")
        assert "RestSharp" in result

    def test_api_imports_unknown(self, classifier):
        assert classifier._get_api_imports_for_language(".rb") == set()

    def test_ui_imports_java(self, classifier):
        result = classifier._get_ui_imports_for_language(".java")
        assert "org.openqa.selenium" in result

    def test_ui_imports_js(self, classifier):
        result = classifier._get_ui_imports_for_language(".ts")
        assert "@playwright/test" in result

    def test_ui_imports_cs(self, classifier):
        result = classifier._get_ui_imports_for_language(".cs")
        assert "OpenQA.Selenium" in result

    def test_ui_imports_unknown(self, classifier):
        assert classifier._get_ui_imports_for_language(".rb") == set()

    def test_bdd_imports_java(self, classifier):
        result = classifier._get_bdd_imports_for_language(".java")
        assert "cucumber" in result

    def test_bdd_imports_js(self, classifier):
        result = classifier._get_bdd_imports_for_language(".js")
        assert "@cucumber/cucumber" in result

    def test_bdd_imports_cs(self, classifier):
        result = classifier._get_bdd_imports_for_language(".cs")
        assert "TechTalk.SpecFlow" in result

    def test_bdd_imports_unknown(self, classifier):
        assert classifier._get_bdd_imports_for_language(".rb") == set()

    def test_test_imports_java(self, classifier):
        result = classifier._get_test_imports_for_language(".java")
        assert "org.junit" in result

    def test_test_imports_js(self, classifier):
        result = classifier._get_test_imports_for_language(".js")
        assert "jest" in result

    def test_test_imports_cs(self, classifier):
        result = classifier._get_test_imports_for_language(".cs")
        assert "NUnit.Framework" in result

    def test_test_imports_unknown(self, classifier):
        assert classifier._get_test_imports_for_language(".rb") == set()


# =========================================================================
# _has_test_methods with ParseResult (lines 297-315)
# =========================================================================

class TestHasTestMethods:
    """_has_test_methods() detects test functions in ParseResult."""

    def test_no_test_methods(self, classifier):
        result = ParseResult(functions=[], classes=[])
        assert classifier._has_test_methods(result, ".py") is False

    def test_python_test_function(self, classifier):
        result = ParseResult(
            functions=[ParsedFunction(name="test_login", line_start=1, line_end=5)],
            classes=[],
        )
        assert classifier._has_test_methods(result, ".py") is True

    def test_java_test_method_in_class(self, classifier):
        method = ParsedFunction(name="loginTest", line_start=5, line_end=10, decorators=["Test"])
        cls = ParsedClass(name="LoginTest", line_start=1, line_end=20, methods=[method])
        result = ParseResult(functions=[], classes=[cls])
        assert classifier._has_test_methods(result, ".java") is True

    def test_java_no_test_methods(self, classifier):
        method = ParsedFunction(name="setup", line_start=5, line_end=10, decorators=["Before"])
        cls = ParsedClass(name="LoginTest", line_start=1, line_end=20, methods=[method])
        result = ParseResult(functions=[], classes=[cls])
        assert classifier._has_test_methods(result, ".java") is False


# =========================================================================
# classify with ParseResult (multi-language, lines 166-171)
# =========================================================================

class TestClassifyWithParseResult:
    """classify_detailed() with ParseResult for multi-language support."""

    def test_java_selenium_via_parse_result(self, classifier):
        imports = [ParsedImport(module="org.openqa.selenium", line=1)]
        result = ParseResult(imports=imports)
        classification = classifier.classify_detailed(
            Path("LoginTest.java"), "import org.openqa.selenium;", result
        )
        assert classification.file_type == "ui"
        assert "selenium" in classification.frameworks

    def test_js_playwright_via_parse_result(self, classifier):
        imports = [ParsedImport(module="@playwright/test", line=1)]
        result = ParseResult(imports=imports)
        classification = classifier.classify_detailed(
            Path("login.spec.ts"), "import { test } from '@playwright/test';", result
        )
        assert classification.file_type == "ui"
        assert "playwright" in classification.frameworks
        assert classification.has_auto_wait is True

    def test_page_object_from_parse_result(self, classifier):
        cls = ParsedClass(
            name="LoginPage", line_start=1, line_end=20, is_page_object=True
        )
        result = ParseResult(classes=[cls])
        classification = classifier.classify_detailed(
            Path("src/LoginPage.java"), "class LoginPage {}", result
        )
        assert classification.file_type == "page_object"

    def test_cypress_framework_detection(self, classifier):
        imports = [ParsedImport(module="cypress", line=1)]
        result = ParseResult(imports=imports)
        classification = classifier.classify_detailed(
            Path("login.spec.js"), "import cypress;", result
        )
        assert classification.file_type == "ui"
        assert "cypress" in classification.frameworks


