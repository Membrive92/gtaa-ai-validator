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


# =========================================================================
# MISSING_AAA_STRUCTURE heuristic
# =========================================================================

class TestMissingAAAStructure:

    def test_test_without_assert_detected(self, mock_client):
        source = '''\
def test_sum_values():
    x = 1 + 1
    y = x * 2
'''
        results = mock_client.analyze_file(source, "test_example.py")
        aaa = [v for v in results if v["type"] == "MISSING_AAA_STRUCTURE"]
        assert len(aaa) == 1

    def test_test_with_assert_ok(self, mock_client):
        source = '''\
def test_with_assert():
    x = 1 + 1
    assert x == 2
'''
        results = mock_client.analyze_file(source, "test_example.py")
        aaa = [v for v in results if v["type"] == "MISSING_AAA_STRUCTURE"]
        assert len(aaa) == 0

    def test_test_with_assertEqual_ok(self, mock_client):
        source = '''\
def test_unittest_style():
    x = 1 + 1
    self.assertEqual(x, 2)
'''
        results = mock_client.analyze_file(source, "test_example.py")
        aaa = [v for v in results if v["type"] == "MISSING_AAA_STRUCTURE"]
        assert len(aaa) == 0


# =========================================================================
# MIXED_ABSTRACTION_LEVEL heuristic
# =========================================================================

class TestMixedAbstractionLevel:

    def test_method_with_xpath_detected(self, mock_client):
        source = '''\
class LoginPage:
    def login(self):
        self.driver.find_element("//input[@id='user']")
'''
        results = mock_client.analyze_file(source, "pages/login_page.py")
        mixed = [v for v in results if v["type"] == "MIXED_ABSTRACTION_LEVEL"]
        assert len(mixed) == 1

    def test_method_with_by_selector_detected(self, mock_client):
        source = '''\
class LoginPage:
    def submit_form(self):
        self.driver.find_element(By.ID, "submit")
'''
        results = mock_client.analyze_file(source, "pages/login_page.py")
        mixed = [v for v in results if v["type"] == "MIXED_ABSTRACTION_LEVEL"]
        assert len(mixed) == 1

    def test_private_method_not_detected(self, mock_client):
        source = '''\
class LoginPage:
    def _find_button(self):
        self.driver.find_element(By.ID, "submit")
'''
        results = mock_client.analyze_file(source, "pages/login_page.py")
        mixed = [v for v in results if v["type"] == "MIXED_ABSTRACTION_LEVEL"]
        assert len(mixed) == 0

    def test_clean_method_not_detected(self, mock_client):
        source = '''\
class LoginPage:
    def login(self):
        self.username_input.fill("user")
'''
        results = mock_client.analyze_file(source, "pages/login_page.py")
        mixed = [v for v in results if v["type"] == "MIXED_ABSTRACTION_LEVEL"]
        assert len(mixed) == 0


# =========================================================================
# BDD step definition heuristics
# =========================================================================

class TestStepDefDirectBrowser:
    """Tests for _check_step_def_direct_browser() heuristic."""

    def test_step_def_with_browser_call_detected(self, mock_client):
        """Step definition with page.locator() → STEP_DEF_DIRECT_BROWSER_CALL."""
        source = '''\
from behave import given

@given("the user navigates to login")
def step_navigate(context):
    context.page.locator("#login").click()
'''
        results = mock_client.analyze_file(source, "steps/login_steps.py")
        types = [v["type"] for v in results]
        assert "STEP_DEF_DIRECT_BROWSER_CALL" in types

    def test_step_def_clean_no_violation(self, mock_client):
        """Step definition without browser calls → no violation."""
        source = '''\
from behave import given

@given("the user is on the login page")
def step_login_page(context):
    context.login_page.navigate()
'''
        results = mock_client.analyze_file(source, "steps/login_steps.py")
        types = [v["type"] for v in results]
        assert "STEP_DEF_DIRECT_BROWSER_CALL" not in types


class TestStepDefTooComplex:
    """Tests for _check_step_def_too_complex() heuristic."""

    def test_step_def_over_15_lines_detected(self, mock_client):
        """Step definition >15 lines → STEP_DEF_TOO_COMPLEX."""
        body_lines = "\n".join(f"    step_{i} = {i}" for i in range(20))
        source = f'''\
from behave import when

@when("the user fills the long form")
def step_fill_form(context):
{body_lines}
'''
        results = mock_client.analyze_file(source, "steps/form_steps.py")
        types = [v["type"] for v in results]
        assert "STEP_DEF_TOO_COMPLEX" in types

    def test_step_def_short_no_violation(self, mock_client):
        """Step definition ≤15 lines → no violation."""
        source = '''\
from behave import then

@then("the user sees the dashboard")
def step_dashboard(context):
    assert context.page_title == "Dashboard"
'''
        results = mock_client.analyze_file(source, "steps/nav_steps.py")
        types = [v["type"] for v in results]
        assert "STEP_DEF_TOO_COMPLEX" not in types


# =========================================================================
# Boundary tests for thresholds
# =========================================================================

class TestBoundaryThresholds:
    """Boundary tests for MockLLMClient heuristic thresholds."""

    def test_page_object_10_methods_no_violation(self, mock_client):
        """POM with exactly 10 public methods → no violation."""
        methods = "\n".join(f"    def method_{i}(self): pass" for i in range(10))
        code = f"class LoginPage:\n{methods}\n"
        results = mock_client.analyze_file(code, "pages/login_page.py")
        types = [v["type"] for v in results]
        assert "PAGE_OBJECT_DOES_TOO_MUCH" not in types

    def test_page_object_11_methods_violation(self, mock_client):
        """POM with 11 public methods → PAGE_OBJECT_DOES_TOO_MUCH."""
        methods = "\n".join(f"    def method_{i}(self): pass" for i in range(11))
        code = f"class LoginPage:\n{methods}\n"
        results = mock_client.analyze_file(code, "pages/login_page.py")
        types = [v["type"] for v in results]
        assert "PAGE_OBJECT_DOES_TOO_MUCH" in types

    def test_unclear_purpose_name_20_chars_no_violation(self, mock_client):
        """Test with name exactly 20 chars → no UNCLEAR_TEST_PURPOSE."""
        # "test_exactly_20chars" = 20 chars (name < 20 is the threshold)
        code = '''\
def test_exactly_20chars1():
    x = 1
'''
        results = mock_client.analyze_file(code, "tests/test_x.py")
        unclear = [v for v in results if v["type"] == "UNCLEAR_TEST_PURPOSE"]
        assert len(unclear) == 0

    def test_unclear_purpose_name_19_chars_violation(self, mock_client):
        """Test with name < 20 chars and no docstring → UNCLEAR_TEST_PURPOSE."""
        code = '''\
def test_short_name():
    x = 1
'''
        results = mock_client.analyze_file(code, "tests/test_x.py")
        unclear = [v for v in results if v["type"] == "UNCLEAR_TEST_PURPOSE"]
        assert len(unclear) == 1


class TestUsageTracking:
    """Tests for token usage tracking after analysis."""

    def test_usage_increments_after_analyze(self, mock_client):
        """usage.total_calls increments after analyze_file()."""
        assert mock_client.usage.total_calls == 0
        mock_client.analyze_file("def test_x(): pass", "test.py")
        assert mock_client.usage.total_calls == 1

    def test_file_type_api_skips_wait_strategy(self, mock_client):
        """file_type='api' skips MISSING_WAIT_STRATEGY checks."""
        code = '''\
class ApiClient:
    def send_request(self):
        self.button.click()
'''
        results = mock_client.analyze_file(code, "pages/api_client.py", file_type="api", has_auto_wait=True)
        waits = [v for v in results if v["type"] == "MISSING_WAIT_STRATEGY"]
        assert len(waits) == 0

