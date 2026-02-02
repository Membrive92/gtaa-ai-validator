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
