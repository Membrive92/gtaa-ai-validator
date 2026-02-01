"""Tests para el paquete LLM — MockLLMClient."""

import pytest

from gtaa_validator.llm.client import MockLLMClient


@pytest.fixture
def mock_client():
    """Instancia de MockLLMClient."""
    return MockLLMClient()


# --- MockLLMClient.analyze_file ---

class TestMockAnalyzeFile:
    """Tests para detección de violaciones semánticas."""

    def test_unclear_test_purpose_sin_docstring_nombre_corto(self, mock_client):
        """Test corto sin docstring → UNCLEAR_TEST_PURPOSE."""
        code = '''
def test_login():
    assert True
'''
        result = mock_client.analyze_file(code, "tests/test_auth.py")
        types = [v["type"] for v in result]
        assert "UNCLEAR_TEST_PURPOSE" in types

    def test_unclear_test_no_aplica_con_docstring(self, mock_client):
        """Test con docstring no genera violación."""
        code = '''
def test_login():
    """Verifica que el usuario puede hacer login."""
    assert True
'''
        result = mock_client.analyze_file(code, "tests/test_auth.py")
        types = [v["type"] for v in result]
        assert "UNCLEAR_TEST_PURPOSE" not in types

    def test_unclear_test_no_aplica_nombre_largo(self, mock_client):
        """Test con nombre descriptivo largo no genera violación."""
        code = '''
def test_user_can_login_with_valid_credentials():
    assert True
'''
        result = mock_client.analyze_file(code, "tests/test_auth.py")
        types = [v["type"] for v in result]
        assert "UNCLEAR_TEST_PURPOSE" not in types

    def test_page_object_too_much(self, mock_client):
        """Page Object con >10 métodos → PAGE_OBJECT_DOES_TOO_MUCH."""
        methods = "\n".join(
            f"    def method_{i}(self): pass" for i in range(12)
        )
        code = f"class LoginPage:\n{methods}\n"
        result = mock_client.analyze_file(code, "pages/login_page.py")
        types = [v["type"] for v in result]
        assert "PAGE_OBJECT_DOES_TOO_MUCH" in types

    def test_page_object_ok_pocos_metodos(self, mock_client):
        """Page Object con <=10 métodos no genera violación."""
        methods = "\n".join(
            f"    def method_{i}(self): pass" for i in range(5)
        )
        code = f"class LoginPage:\n{methods}\n"
        result = mock_client.analyze_file(code, "pages/login_page.py")
        types = [v["type"] for v in result]
        assert "PAGE_OBJECT_DOES_TOO_MUCH" not in types

    def test_implicit_test_dependency(self, mock_client):
        """Variable mutable global en test → IMPLICIT_TEST_DEPENDENCY."""
        code = '''
shared_data = {"user": "admin"}

def test_login():
    assert shared_data["user"] == "admin"
'''
        result = mock_client.analyze_file(code, "tests/test_auth.py")
        types = [v["type"] for v in result]
        assert "IMPLICIT_TEST_DEPENDENCY" in types

    def test_implicit_dependency_ignora_constantes(self, mock_client):
        """Constantes en MAYÚSCULAS no generan violación."""
        code = '''
BASE_URL = "http://example.com"

def test_home():
    assert True
'''
        result = mock_client.analyze_file(code, "tests/test_home.py")
        deps = [v for v in result if v["type"] == "IMPLICIT_TEST_DEPENDENCY"]
        assert len(deps) == 0

    def test_missing_wait_strategy(self, mock_client):
        """Click sin wait previo en Page Object → MISSING_WAIT_STRATEGY."""
        code = '''
class LoginPage:
    def submit(self):
        self.button.click()
'''
        result = mock_client.analyze_file(code, "pages/login_page.py")
        types = [v["type"] for v in result]
        assert "MISSING_WAIT_STRATEGY" in types

    def test_missing_wait_no_aplica_con_wait(self, mock_client):
        """Click con wait previo no genera violación."""
        code = '''
class LoginPage:
    def submit(self):
        self.wait.until(lambda d: self.button.is_displayed())
        self.button.click()
'''
        result = mock_client.analyze_file(code, "pages/login_page.py")
        waits = [v for v in result if v["type"] == "MISSING_WAIT_STRATEGY"]
        assert len(waits) == 0

    def test_archivo_limpio_sin_violaciones(self, mock_client):
        """Código limpio no genera violaciones."""
        code = '''
def test_user_can_login_with_valid_credentials():
    """Verifica login con credenciales válidas."""
    assert True
'''
        result = mock_client.analyze_file(code, "tests/test_auth.py")
        assert result == []

    def test_syntax_error_retorna_vacio(self, mock_client):
        """Archivo con error de sintaxis retorna lista vacía."""
        result = mock_client.analyze_file("def :", "tests/test_bad.py")
        assert result == []

    def test_no_analiza_test_en_page_object(self, mock_client):
        """No busca UNCLEAR_TEST_PURPOSE en Page Objects."""
        code = '''
def test_foo():
    pass
'''
        result = mock_client.analyze_file(code, "pages/login_page.py")
        types = [v["type"] for v in result]
        assert "UNCLEAR_TEST_PURPOSE" not in types

    def test_no_analiza_page_en_test(self, mock_client):
        """No busca PAGE_OBJECT_DOES_TOO_MUCH en tests."""
        methods = "\n".join(
            f"    def method_{i}(self): pass" for i in range(12)
        )
        code = f"class Helper:\n{methods}\n"
        result = mock_client.analyze_file(code, "tests/test_helper.py")
        types = [v["type"] for v in result]
        assert "PAGE_OBJECT_DOES_TOO_MUCH" not in types

    def test_violation_dict_estructura(self, mock_client):
        """Las violaciones retornadas tienen la estructura esperada."""
        code = '''
def test_x():
    pass
'''
        result = mock_client.analyze_file(code, "tests/test_x.py")
        assert len(result) > 0
        v = result[0]
        assert "type" in v
        assert "line" in v
        assert "message" in v
        assert "code_snippet" in v


# --- MockLLMClient.enrich_violation ---

class TestMockEnrichViolation:
    """Tests para enriquecimiento de violaciones."""

    def test_enrich_adaptation_in_definition(self, mock_client):
        """Enriquecimiento de ADAPTATION_IN_DEFINITION."""
        violation = {
            "type": "ADAPTATION_IN_DEFINITION",
            "message": "Llamada directa a Selenium",
            "code_snippet": "driver.find_element(By.ID, 'user')",
        }
        result = mock_client.enrich_violation(violation, "# code")
        assert isinstance(result, str)
        assert len(result) > 20
        assert "Page Object" in result

    def test_enrich_hardcoded_test_data(self, mock_client):
        """Enriquecimiento de HARDCODED_TEST_DATA."""
        violation = {
            "type": "HARDCODED_TEST_DATA",
            "message": "Dato hardcodeado",
            "code_snippet": "admin@test.com",
        }
        result = mock_client.enrich_violation(violation, "# code")
        assert "datos" in result.lower() or "data" in result.lower() or "fichero" in result.lower()

    def test_enrich_tipo_desconocido(self, mock_client):
        """Tipo desconocido genera sugerencia genérica."""
        violation = {
            "type": "UNKNOWN_TYPE",
            "message": "Algo raro",
        }
        result = mock_client.enrich_violation(violation, "# code")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_enrich_todos_los_tipos_conocidos(self, mock_client):
        """Cada tipo estático conocido genera una sugerencia específica."""
        known_types = [
            "ADAPTATION_IN_DEFINITION", "HARDCODED_TEST_DATA",
            "ASSERTION_IN_POM", "FORBIDDEN_IMPORT", "BUSINESS_LOGIC_IN_POM",
            "DUPLICATE_LOCATOR", "LONG_TEST_FUNCTION", "POOR_TEST_NAMING",
            "MISSING_LAYER_STRUCTURE",
        ]
        for vtype in known_types:
            result = mock_client.enrich_violation(
                {"type": vtype, "message": "test", "code_snippet": "x"},
                "# code",
            )
            assert isinstance(result, str)
            assert len(result) > 20, f"Sugerencia corta para {vtype}"


