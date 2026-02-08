"""Tests para APILLMClient."""

import pytest
from unittest.mock import MagicMock, patch

from gtaa_validator.llm.api_client import APILLMClient


class TestAPIClientInit:
    """Tests de inicialización."""

    def test_sin_api_key_lanza_error(self):
        """Constructor sin API key lanza ValueError."""
        with pytest.raises(ValueError, match="API key"):
            APILLMClient(api_key="")

    def test_sin_api_key_none_lanza_error(self):
        """Constructor con None lanza error."""
        with pytest.raises(ValueError, match="API key"):
            APILLMClient(api_key=None)

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_con_api_key_crea_cliente(self, mock_genai_client):
        """Constructor con API key válida crea instancia."""
        client = APILLMClient(api_key="test-key-123")
        assert client.model == "gemini-2.5-flash-lite"
        mock_genai_client.assert_called_once_with(api_key="test-key-123")


class TestAPIClientAnalyzeFile:
    """Tests para analyze_file()."""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_parse_respuesta_json_valida(self, mock_genai_client):
        """Parsea correctamente JSON con violaciones."""
        mock_response = MagicMock()
        mock_response.text = '''[
            {
                "type": "UNCLEAR_TEST_PURPOSE",
                "line": 5,
                "message": "Test sin propósito claro",
                "code_snippet": "def test_x():"
            }
        ]'''
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.analyze_file("def test_x(): pass", "tests/test_x.py")

        assert len(result) == 1
        assert result[0]["type"] == "UNCLEAR_TEST_PURPOSE"
        assert result[0]["line"] == 5

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_parse_json_envuelto_en_markdown(self, mock_genai_client):
        """Parsea JSON envuelto en bloques ```json."""
        mock_response = MagicMock()
        mock_response.text = '```json\n[{"type": "MISSING_WAIT_STRATEGY", "line": 3, "message": "Sin wait", "code_snippet": "btn.click()"}]\n```'
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.analyze_file("btn.click()", "pages/login_page.py")

        assert len(result) == 1
        assert result[0]["type"] == "MISSING_WAIT_STRATEGY"

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_filtra_tipos_invalidos(self, mock_genai_client):
        """Ignora violaciones con tipo no reconocido."""
        mock_response = MagicMock()
        mock_response.text = '[{"type": "TIPO_INVENTADO", "line": 1, "message": "x", "code_snippet": "x"}]'
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.analyze_file("code", "test.py")

        assert result == []

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_respuesta_vacia_retorna_lista_vacia(self, mock_genai_client):
        """Respuesta vacía retorna []."""
        mock_response = MagicMock()
        mock_response.text = "[]"
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.analyze_file("clean code", "test.py")

        assert result == []

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_respuesta_no_json_retorna_lista_vacia(self, mock_genai_client):
        """Respuesta que no es JSON retorna []."""
        mock_response = MagicMock()
        mock_response.text = "No encontré violaciones en este archivo."
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.analyze_file("code", "test.py")

        assert result == []

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_error_api_retorna_lista_vacia(self, mock_genai_client):
        """Error de API retorna [] sin propagar excepción."""
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("API error")

        client = APILLMClient(api_key="test-key")
        result = client.analyze_file("code", "test.py")

        assert result == []


class TestAPIClientEnrichViolation:
    """Tests para enrich_violation()."""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_retorna_sugerencia(self, mock_genai_client):
        """Retorna texto de sugerencia del modelo."""
        mock_response = MagicMock()
        mock_response.text = "Deberías encapsular esta llamada en un Page Object."
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.enrich_violation(
            {"type": "ADAPTATION_IN_DEFINITION", "message": "test", "code_snippet": "x"},
            "# code"
        )

        assert "Page Object" in result

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_error_api_retorna_string_vacio(self, mock_genai_client):
        """Error de API retorna '' sin propagar excepción."""
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("API error")

        client = APILLMClient(api_key="test-key")
        result = client.enrich_violation({"type": "X", "message": "x"}, "# code")

        assert result == ""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_respuesta_vacia_retorna_string_vacio(self, mock_genai_client):
        """Respuesta vacía retorna ''."""
        mock_response = MagicMock()
        mock_response.text = "   "
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = APILLMClient(api_key="test-key")
        result = client.enrich_violation({"type": "X", "message": "x"}, "# code")

        assert result == ""


class TestAPIClientValidTypes:
    """Tests para VALID_TYPES."""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_parse_missing_aaa_structure(self, mock_genai_client):
        client = APILLMClient(api_key="test-key")
        text = '[{"type": "MISSING_AAA_STRUCTURE", "line": 5, "message": "test", "code_snippet": "x"}]'
        result = client._parse_violations(text)
        assert len(result) == 1
        assert result[0]["type"] == "MISSING_AAA_STRUCTURE"


class TestRateLimitError:
    """Tests para manejo de rate limit (HTTP 429 y quota)."""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_rate_limit_error_on_analyze(self, mock_genai_client):
        """429 en analyze_file → RateLimitError."""
        from gtaa_validator.llm.api_client import RateLimitError
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("429 Too Many Requests")
        client = APILLMClient(api_key="test-key")
        with pytest.raises(RateLimitError):
            client.analyze_file("code", "test.py")

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_rate_limit_error_on_enrich(self, mock_genai_client):
        """429 en enrich_violation → RateLimitError."""
        from gtaa_validator.llm.api_client import RateLimitError
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("Resource exhausted")
        client = APILLMClient(api_key="test-key")
        with pytest.raises(RateLimitError):
            client.enrich_violation({"type": "X", "message": "x"}, "# code")

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_is_rate_limit_429_pattern(self, mock_genai_client):
        """'429' in error → is_rate_limit_error() returns True."""
        client = APILLMClient(api_key="test-key")
        assert client._is_rate_limit_error(Exception("Error 429")) is True

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_is_rate_limit_quota_pattern(self, mock_genai_client):
        """'quota' in error → is_rate_limit_error() returns True."""
        client = APILLMClient(api_key="test-key")
        assert client._is_rate_limit_error(Exception("Quota exceeded")) is True

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_is_rate_limit_resource_exhausted(self, mock_genai_client):
        """'resource exhausted' → is_rate_limit_error() returns True."""
        client = APILLMClient(api_key="test-key")
        assert client._is_rate_limit_error(Exception("RESOURCE EXHAUSTED")) is True

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_is_not_rate_limit_generic_error(self, mock_genai_client):
        """Generic API error → is_rate_limit_error() returns False."""
        client = APILLMClient(api_key="test-key")
        assert client._is_rate_limit_error(Exception("Connection timeout")) is False


class TestAPIClientRepr:
    """Tests para __repr__() — SEC-04."""

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_repr_does_not_expose_api_key(self, mock_genai_client):
        """repr(client) must NOT contain the API key (SEC-04)."""
        client = APILLMClient(api_key="sk-secret-key-12345")
        representation = repr(client)
        assert "sk-secret-key-12345" not in representation
        assert "APILLMClient" in representation


class TestBackwardsCompatibility:
    """Tests de compatibilidad hacia atrás con GeminiLLMClient."""

    def test_alias_disponible_en_modulo(self):
        """El alias GeminiLLMClient está disponible."""
        from gtaa_validator.llm.api_client import GeminiLLMClient
        assert GeminiLLMClient is APILLMClient

    def test_alias_disponible_en_init(self):
        """El alias está disponible vía __init__.py."""
        from gtaa_validator.llm import GeminiLLMClient, APILLMClient
        assert GeminiLLMClient is APILLMClient
