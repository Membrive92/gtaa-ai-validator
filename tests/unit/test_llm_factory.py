"""Tests para LLMClientFactory."""

import os
import pytest
from unittest.mock import patch

from gtaa_validator.llm.factory import create_llm_client, get_available_providers
from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.api_client import APILLMClient


class TestCreateLLMClientMock:
    """Tests para provider mock."""

    def test_mock_explicit(self):
        """Provider mock crea MockLLMClient."""
        client = create_llm_client(provider="mock")
        assert isinstance(client, MockLLMClient)

    @patch.dict(os.environ, {"LLM_PROVIDER": "mock"}, clear=False)
    def test_mock_from_env(self):
        """LLM_PROVIDER=mock crea MockLLMClient."""
        client = create_llm_client()
        assert isinstance(client, MockLLMClient)


class TestCreateLLMClientGemini:
    """Tests para provider gemini."""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_gemini_with_api_key_param(self, mock_genai):
        """Provider gemini con api_key crea APILLMClient."""
        client = create_llm_client(provider="gemini", api_key="test-key")
        assert isinstance(client, APILLMClient)
        mock_genai.assert_called_once_with(api_key="test-key")

    @patch("gtaa_validator.llm.api_client.genai.Client")
    @patch.dict(os.environ, {"LLM_API_KEY": "env-key"}, clear=False)
    def test_gemini_with_llm_api_key_env(self, mock_genai):
        """LLM_API_KEY se usa para gemini."""
        client = create_llm_client(provider="gemini")
        assert isinstance(client, APILLMClient)
        mock_genai.assert_called_once_with(api_key="env-key")

    @patch("gtaa_validator.llm.api_client.genai.Client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-key"}, clear=False)
    def test_gemini_with_gemini_api_key_env(self, mock_genai):
        """GEMINI_API_KEY se usa como fallback."""
        # Limpiar LLM_API_KEY si existe
        env = os.environ.copy()
        env.pop("LLM_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            os.environ["GEMINI_API_KEY"] = "gemini-key"
            client = create_llm_client(provider="gemini")
            assert isinstance(client, APILLMClient)

    def test_gemini_without_key_fallback_to_mock(self):
        """Provider gemini sin API key usa MockLLMClient como fallback."""
        with patch.dict(os.environ, {}, clear=True):
            client = create_llm_client(provider="gemini")
            assert isinstance(client, MockLLMClient)

    @patch("gtaa_validator.llm.api_client.genai.Client")
    @patch.dict(os.environ, {"GEMINI_MODEL": "gemini-pro"}, clear=False)
    def test_gemini_custom_model_from_env(self, mock_genai):
        """GEMINI_MODEL configura modelo."""
        client = create_llm_client(provider="gemini", api_key="test")
        assert client.model == "gemini-pro"


class TestCreateLLMClientEnvDefault:
    """Tests para default desde entorno (auto-detección)."""

    def test_default_without_api_key_is_mock(self):
        """Sin API key ni LLM_PROVIDER, default es MockLLMClient."""
        with patch.dict(os.environ, {}, clear=True):
            client = create_llm_client()
            assert isinstance(client, MockLLMClient)

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_default_with_api_key_is_gemini(self, mock_genai):
        """Con GEMINI_API_KEY, auto-detecta y usa Gemini."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "auto-key"}, clear=True):
            client = create_llm_client()
            assert isinstance(client, APILLMClient)

    @patch.dict(os.environ, {"LLM_PROVIDER": "mock"}, clear=False)
    def test_env_provider_used(self):
        """LLM_PROVIDER del entorno se usa."""
        client = create_llm_client()
        assert isinstance(client, MockLLMClient)


class TestCreateLLMClientErrors:
    """Tests de errores."""

    def test_invalid_provider_raises(self):
        """Provider inválido lanza error."""
        with pytest.raises(ValueError, match="no soportado"):
            create_llm_client(provider="openai")

    def test_invalid_provider_lists_options(self):
        """Error lista providers soportados."""
        with pytest.raises(ValueError, match="gemini"):
            create_llm_client(provider="invalid")


class TestGetAvailableProviders:
    """Tests para get_available_providers()."""

    def test_mock_always_available(self):
        """Mock siempre está disponible."""
        providers = get_available_providers()
        assert providers["mock"]["available"] is True

    @patch.dict(os.environ, {"LLM_API_KEY": "test-key"}, clear=False)
    def test_gemini_available_with_key(self):
        """Gemini disponible si hay API key."""
        providers = get_available_providers()
        assert providers["gemini"]["available"] is True
        assert providers["gemini"]["configured"] is True

    def test_gemini_not_available_without_key(self):
        """Gemini no disponible sin API key."""
        with patch.dict(os.environ, {}, clear=True):
            providers = get_available_providers()
            assert providers["gemini"]["available"] is False

    def test_only_two_providers(self):
        """Solo hay dos proveedores: gemini y mock."""
        providers = get_available_providers()
        assert set(providers.keys()) == {"gemini", "mock"}
