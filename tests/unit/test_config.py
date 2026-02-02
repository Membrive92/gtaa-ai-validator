"""
Tests for gtaa_validator.config

Covers:
- ProjectConfig defaults
- load_config() with and without .gtaa.yaml
- Graceful degradation on invalid YAML
"""

import pytest
from pathlib import Path

from gtaa_validator.config import ProjectConfig, load_config


# =========================================================================
# ProjectConfig defaults
# =========================================================================

class TestProjectConfigDefaults:

    def test_default_exclude_checks(self):
        config = ProjectConfig()
        assert config.exclude_checks == []

    def test_default_ignore_paths(self):
        config = ProjectConfig()
        assert config.ignore_paths == []

    def test_default_api_test_patterns(self):
        config = ProjectConfig()
        assert config.api_test_patterns == []


# =========================================================================
# load_config()
# =========================================================================

class TestLoadConfig:

    def test_no_config_file_returns_defaults(self, tmp_path):
        """No .gtaa.yaml → default config."""
        config = load_config(tmp_path)
        assert config.exclude_checks == []
        assert config.ignore_paths == []
        assert config.api_test_patterns == []

    def test_valid_config_file(self, tmp_path):
        """Valid .gtaa.yaml loads correctly."""
        yaml_content = (
            "exclude_checks:\n"
            "  - MISSING_WAIT_STRATEGY\n"
            "ignore_paths:\n"
            "  - 'tests/legacy/**'\n"
            "api_test_patterns:\n"
            "  - '**/test_api_*.py'\n"
        )
        (tmp_path / ".gtaa.yaml").write_text(yaml_content, encoding="utf-8")
        config = load_config(tmp_path)
        assert config.exclude_checks == ["MISSING_WAIT_STRATEGY"]
        assert config.ignore_paths == ["tests/legacy/**"]
        assert config.api_test_patterns == ["**/test_api_*.py"]

    def test_empty_yaml_returns_defaults(self, tmp_path):
        """Empty YAML file → defaults."""
        (tmp_path / ".gtaa.yaml").write_text("", encoding="utf-8")
        config = load_config(tmp_path)
        assert config.exclude_checks == []

    def test_invalid_yaml_returns_defaults(self, tmp_path):
        """Malformed YAML → defaults (graceful degradation)."""
        (tmp_path / ".gtaa.yaml").write_text("{{invalid:yaml", encoding="utf-8")
        config = load_config(tmp_path)
        assert config.exclude_checks == []

    def test_yaml_with_null_values(self, tmp_path):
        """YAML with null values → empty lists."""
        yaml_content = "exclude_checks:\nignore_paths:\n"
        (tmp_path / ".gtaa.yaml").write_text(yaml_content, encoding="utf-8")
        config = load_config(tmp_path)
        assert config.exclude_checks == []
        assert config.ignore_paths == []

    def test_yaml_not_dict_returns_defaults(self, tmp_path):
        """YAML that parses to a list → defaults."""
        (tmp_path / ".gtaa.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        config = load_config(tmp_path)
        assert config.exclude_checks == []

    def test_partial_config(self, tmp_path):
        """Only some fields present → others get defaults."""
        yaml_content = "exclude_checks:\n  - POOR_TEST_NAMING\n"
        (tmp_path / ".gtaa.yaml").write_text(yaml_content, encoding="utf-8")
        config = load_config(tmp_path)
        assert config.exclude_checks == ["POOR_TEST_NAMING"]
        assert config.ignore_paths == []
        assert config.api_test_patterns == []
