"""Tests para GeminiLLMClient."""

import pytest
from unittest.mock import MagicMock, patch

from gtaa_validator.llm.gemini_client import GeminiLLMClient


class TestGeminiClientInit:
    """Tests de inicialización."""

    def test_sin_api_key_lanza_error(self):
        """Constructor sin API key lanza ValueError."""
        with pytest.raises(ValueError, match="API key"):
            GeminiLLMClient(api_key="")

    def test_sin_api_key_none_lanza_error(self):
        """Constructor con None lanza error."""
        with pytest.raises(ValueError, match="API key"):
            GeminiLLMClient(api_key=None)

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_con_api_key_crea_cliente(self, mock_genai_client):
        """Constructor con API key válida crea instancia."""
        client = GeminiLLMClient(api_key="test-key-123")
        assert client.model == "gemini-2.5-flash-lite"
        mock_genai_client.assert_called_once_with(api_key="test-key-123")


class TestGeminiAnalyzeFile:
    """Tests para analyze_file()."""

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
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

        client = GeminiLLMClient(api_key="test-key")
        result = client.analyze_file("def test_x(): pass", "tests/test_x.py")

        assert len(result) == 1
        assert result[0]["type"] == "UNCLEAR_TEST_PURPOSE"
        assert result[0]["line"] == 5

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_parse_json_envuelto_en_markdown(self, mock_genai_client):
        """Parsea JSON envuelto en bloques ```json."""
        mock_response = MagicMock()
        mock_response.text = '```json\n[{"type": "MISSING_WAIT_STRATEGY", "line": 3, "message": "Sin wait", "code_snippet": "btn.click()"}]\n```'
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="test-key")
        result = client.analyze_file("btn.click()", "pages/login_page.py")

        assert len(result) == 1
        assert result[0]["type"] == "MISSING_WAIT_STRATEGY"

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_filtra_tipos_invalidos(self, mock_genai_client):
        """Ignora violaciones con tipo no reconocido."""
        mock_response = MagicMock()
        mock_response.text = '[{"type": "TIPO_INVENTADO", "line": 1, "message": "x", "code_snippet": "x"}]'
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="test-key")
        result = client.analyze_file("code", "test.py")

        assert result == []

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_respuesta_vacia_retorna_lista_vacia(self, mock_genai_client):
        """Respuesta vacía retorna []."""
        mock_response = MagicMock()
        mock_response.text = "[]"
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="test-key")
        result = client.analyze_file("clean code", "test.py")

        assert result == []

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_respuesta_no_json_retorna_lista_vacia(self, mock_genai_client):
        """Respuesta que no es JSON retorna []."""
        mock_response = MagicMock()
        mock_response.text = "No encontré violaciones en este archivo."
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="test-key")
        result = client.analyze_file("code", "test.py")

        assert result == []

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_error_api_retorna_lista_vacia(self, mock_genai_client):
        """Error de API retorna [] sin propagar excepción."""
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("API error")

        client = GeminiLLMClient(api_key="test-key")
        result = client.analyze_file("code", "test.py")

        assert result == []


class TestGeminiEnrichViolation:
    """Tests para enrich_violation()."""

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_retorna_sugerencia(self, mock_genai_client):
        """Retorna texto de sugerencia del modelo."""
        mock_response = MagicMock()
        mock_response.text = "Deberías encapsular esta llamada en un Page Object."
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="test-key")
        result = client.enrich_violation(
            {"type": "ADAPTATION_IN_DEFINITION", "message": "test", "code_snippet": "x"},
            "# code"
        )

        assert "Page Object" in result

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_error_api_retorna_string_vacio(self, mock_genai_client):
        """Error de API retorna '' sin propagar excepción."""
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("API error")

        client = GeminiLLMClient(api_key="test-key")
        result = client.enrich_violation({"type": "X", "message": "x"}, "# code")

        assert result == ""

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_respuesta_vacia_retorna_string_vacio(self, mock_genai_client):
        """Respuesta vacía retorna ''."""
        mock_response = MagicMock()
        mock_response.text = "   "
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="test-key")
        result = client.enrich_violation({"type": "X", "message": "x"}, "# code")

        assert result == ""


class TestGeminiValidTypes:
    """Tests para VALID_TYPES."""

    def test_valid_types_includes_aaa(self):
        assert "MISSING_AAA_STRUCTURE" in GeminiLLMClient.VALID_TYPES

    @patch("gtaa_validator.llm.gemini_client.genai.Client")
    def test_parse_missing_aaa_structure(self, mock_genai_client):
        client = GeminiLLMClient(api_key="test-key")
        text = '[{"type": "MISSING_AAA_STRUCTURE", "line": 5, "message": "test", "code_snippet": "x"}]'
        result = client._parse_violations(text)
        assert len(result) == 1
        assert result[0]["type"] == "MISSING_AAA_STRUCTURE"
