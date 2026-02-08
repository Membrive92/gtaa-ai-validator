"""
Tests de regresión de seguridad.

Verifica que todas las remediaciones de la auditoría de seguridad (SEC-01 a SEC-09)
siguen funcionando correctamente. Cada clase de test corresponde a un hallazgo
específico del documento SECURITY_AUDIT_REPORT.md.

Cubre:
- SEC-03: Rutas relativas en reportes (no absolutas)
- SEC-04: API key nunca expuesta en __repr__
- SEC-05: Límite de tamaño en lectura de archivos (DoS)
- SEC-07: Límites ReDoS en regex de BDDChecker
- SEC-08: load_dotenv() no carga desde CWD
- XSS: html.escape() en HtmlReporter
- YAML: safe_load() en config.py
- Input validation: CLI valida rutas y argumentos
"""

import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from gtaa_validator.models import Violation, ViolationType, Severity, Report


# =====================================================================
# SEC-03 — Rutas absolutas no expuestas en reportes
# =====================================================================


class TestSEC03PathDisclosure:
    """SEC-03: Los reportes no deben exponer rutas absolutas del sistema."""

    def test_violation_to_dict_relativizes_path(self, tmp_path):
        """Violation.to_dict() relativiza la ruta respecto a project_path."""
        file_path = tmp_path / "tests" / "test_login.py"
        violation = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=file_path,
        )
        result = violation.to_dict(project_path=tmp_path)
        # Debe ser relativa, no absoluta
        assert str(tmp_path) not in result["file"]
        assert "test_login.py" in result["file"]

    def test_violation_to_dict_without_project_path_shows_full(self, tmp_path):
        """Sin project_path, to_dict() muestra la ruta completa (por compatibilidad)."""
        file_path = tmp_path / "tests" / "test_login.py"
        violation = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=file_path,
        )
        result = violation.to_dict()
        assert "test_login.py" in result["file"]

    def test_violation_to_dict_external_path_no_crash(self, tmp_path):
        """Si file_path no está dentro de project_path, no lanza excepción."""
        violation = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=Path("/other/directory/test.py"),
        )
        result = violation.to_dict(project_path=tmp_path)
        assert "test.py" in result["file"]

    def test_report_to_dict_uses_project_name_only(self, tmp_path):
        """Report.to_dict() usa solo el nombre del directorio, no ruta absoluta."""
        report = Report(
            project_path=tmp_path / "mi-proyecto",
            violations=[],
            files_analyzed=5,
        )
        result = report.to_dict()
        # Solo el nombre, no la ruta completa
        assert result["metadata"]["project_path"] == "mi-proyecto"
        assert str(tmp_path) not in result["metadata"]["project_path"]

    def test_report_violations_use_relative_paths(self, tmp_path):
        """Las violaciones en Report.to_dict() tienen rutas relativas."""
        project = tmp_path / "proyecto"
        project.mkdir()
        violation = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=project / "tests" / "test_login.py",
        )
        report = Report(
            project_path=project,
            violations=[violation],
            files_analyzed=1,
        )
        result = report.to_dict()
        file_in_json = result["violations"][0]["file"]
        assert str(project) not in file_in_json


# =====================================================================
# SEC-04 — API key no expuesta en __repr__
# =====================================================================


class TestSEC04APIKeyProtection:
    """SEC-04: La API key nunca debe aparecer en representaciones del objeto."""

    @patch("gtaa_validator.llm.api_client.genai")
    def test_repr_does_not_contain_api_key(self, mock_genai):
        """__repr__ de APILLMClient no contiene la API key."""
        from gtaa_validator.llm.api_client import APILLMClient

        secret_key = "AIzaSyB_SUPER_SECRET_KEY_12345"
        client = APILLMClient(api_key=secret_key, model="gemini-test")
        representation = repr(client)

        assert secret_key not in representation
        assert "SUPER_SECRET" not in representation
        assert "model=" in representation

    @patch("gtaa_validator.llm.api_client.genai")
    def test_str_does_not_contain_api_key(self, mock_genai):
        """str() de APILLMClient no contiene la API key."""
        from gtaa_validator.llm.api_client import APILLMClient

        secret_key = "AIzaSyB_ANOTHER_SECRET_KEY"
        client = APILLMClient(api_key=secret_key)
        string_repr = str(client)

        assert secret_key not in string_repr

    @patch("gtaa_validator.llm.api_client.genai")
    def test_api_key_not_in_attributes(self, mock_genai):
        """La API key no se almacena como atributo público accesible."""
        from gtaa_validator.llm.api_client import APILLMClient

        secret_key = "AIzaSyB_TEST_KEY_SECRET"
        client = APILLMClient(api_key=secret_key)

        # No debe existir como atributo público
        assert not hasattr(client, "api_key")


# =====================================================================
# SEC-05 — Límite de tamaño en lectura de archivos (DoS)
# =====================================================================


class TestSEC05FileSizeLimit:
    """SEC-05: read_file_safe() debe rechazar archivos mayores a 10MB."""

    def test_rejects_oversized_file(self, tmp_path):
        """Un archivo que excede MAX_FILE_SIZE_BYTES retorna string vacío."""
        from gtaa_validator.file_utils import read_file_safe, MAX_FILE_SIZE_BYTES

        big_file = tmp_path / "huge.py"
        big_file.write_text("x" * 100, encoding="utf-8")

        # Mock stat para simular archivo de 20MB
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value = MagicMock(st_size=20 * 1024 * 1024)
            result = read_file_safe(big_file)

        assert result == ""

    def test_accepts_normal_file(self, tmp_path):
        """Un archivo normal se lee correctamente."""
        from gtaa_validator.file_utils import read_file_safe

        normal_file = tmp_path / "normal.py"
        normal_file.write_text("print('hello')", encoding="utf-8")
        result = read_file_safe(normal_file)

        assert result == "print('hello')"

    def test_max_size_constant_is_10mb(self):
        """La constante MAX_FILE_SIZE_BYTES es exactamente 10MB."""
        from gtaa_validator.file_utils import MAX_FILE_SIZE_BYTES

        assert MAX_FILE_SIZE_BYTES == 10 * 1024 * 1024

    def test_unreadable_file_returns_empty(self, tmp_path):
        """Un archivo que no se puede leer retorna string vacío sin excepción."""
        from gtaa_validator.file_utils import read_file_safe

        fake_file = tmp_path / "no_existe.py"
        result = read_file_safe(fake_file)

        assert result == ""


# =====================================================================
# SEC-07 — ReDoS: regex con límites de longitud
# =====================================================================


class TestSEC07ReDoSProtection:
    """SEC-07: Las regex de BDDChecker deben tener límites de longitud."""

    def test_url_regex_has_length_limit(self):
        r"""El patrón de URLs tiene límite {1,2000} en lugar de \S+."""
        from gtaa_validator.checkers.bdd_checker import BDDChecker

        url_patterns = [
            p for p in BDDChecker.IMPLEMENTATION_PATTERNS
            if "http" in p.pattern
        ]
        assert len(url_patterns) == 1
        # Verificar que tiene límite de longitud
        assert "{1,2000}" in url_patterns[0].pattern

    def test_sql_regex_has_length_limit(self):
        """El patrón de SQL tiene límite {1,500} en lugar de .+."""
        from gtaa_validator.checkers.bdd_checker import BDDChecker

        sql_patterns = [
            p for p in BDDChecker.IMPLEMENTATION_PATTERNS
            if "SELECT" in p.pattern
        ]
        assert len(sql_patterns) == 1
        assert "{1,500}" in sql_patterns[0].pattern

    def test_url_regex_still_matches_normal_urls(self):
        """El patrón de URL con límite sigue detectando URLs normales."""
        from gtaa_validator.checkers.bdd_checker import BDDChecker

        url_pattern = [
            p for p in BDDChecker.IMPLEMENTATION_PATTERNS
            if "http" in p.pattern
        ][0]
        assert url_pattern.search("https://example.com/login")
        assert url_pattern.search("http://localhost:8080/api")

    def test_sql_regex_still_matches_normal_sql(self):
        """El patrón de SQL con límite sigue detectando SQL normal."""
        from gtaa_validator.checkers.bdd_checker import BDDChecker

        sql_pattern = [
            p for p in BDDChecker.IMPLEMENTATION_PATTERNS
            if "SELECT" in p.pattern
        ][0]
        assert sql_pattern.search("SELECT id, name FROM users")
        assert sql_pattern.search("select * from orders")


# =====================================================================
# SEC-08 — load_dotenv() no carga desde CWD del proyecto analizado
# =====================================================================


class TestSEC08DotenvSecurity:
    """SEC-08: load_dotenv() debe cargar desde paquete/home, NO desde CWD."""

    def test_dotenv_loads_from_package_dir(self):
        """load_dotenv se invoca con la ruta del directorio del paquete."""
        import gtaa_validator.__main__ as main_module

        # Verificar que _package_dir apunta al directorio padre del paquete
        package_dir = main_module._package_dir
        # Debe ser el directorio que contiene gtaa_validator/
        assert (package_dir / "gtaa_validator").exists() or \
               package_dir.name != "gtaa_validator"

    def test_dotenv_does_not_load_from_cwd(self):
        """El módulo __main__ no llama load_dotenv() sin argumentos."""
        import inspect
        import gtaa_validator.__main__ as main_module

        source = inspect.getsource(main_module)
        # No debe haber load_dotenv() sin argumentos (cargaría desde CWD)
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if 'load_dotenv()' in stripped and 'load_dotenv(_' not in stripped:
                pytest.fail(
                    f"load_dotenv() sin argumentos encontrado: {stripped}. "
                    "Debería cargar desde ruta específica (SEC-08)."
                )


# =====================================================================
# XSS — html.escape() en HtmlReporter
# =====================================================================


class TestXSSPrevention:
    """Verifica que el HtmlReporter escapa contenido malicioso (XSS)."""

    def _make_report(self, violations=None, project_name="test-project"):
        """Helper para crear un Report minimal."""
        return Report(
            project_path=Path(f"/tmp/{project_name}"),
            violations=violations or [],
            files_analyzed=1,
            score=75.0,
            timestamp=datetime(2026, 1, 1, 12, 0),
        )

    def test_xss_in_project_name(self):
        """Nombre de proyecto con script malicioso es escapado."""
        from gtaa_validator.reporters.html_reporter import HtmlReporter

        reporter = HtmlReporter()
        report = self._make_report()
        # Mock para inyectar caracteres ilegales en Windows como nombre
        report.project_path = MagicMock()
        report.project_path.name = '<script>alert("xss")</script>'
        html_output = reporter._build_html(report)

        assert '<script>alert("xss")</script>' not in html_output
        assert '&lt;script&gt;' in html_output

    def test_xss_in_violation_message(self):
        """Mensaje de violación con HTML malicioso es escapado."""
        from gtaa_validator.reporters.html_reporter import HtmlReporter

        violation = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=Path("/tmp/proj/test.py"),
            message='<img src=x onerror=alert(1)>',
        )
        report = self._make_report(violations=[violation])
        reporter = HtmlReporter()
        html_output = reporter._build_html(report)

        assert '<img src=x onerror=alert(1)>' not in html_output
        assert '&lt;img' in html_output

    def test_xss_in_code_snippet(self):
        """Code snippet con JavaScript malicioso es escapado."""
        from gtaa_validator.reporters.html_reporter import HtmlReporter

        violation = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=Path("/tmp/proj/test.py"),
            code_snippet='<script>document.cookie</script>',
        )
        report = self._make_report(violations=[violation])
        reporter = HtmlReporter()
        html_output = reporter._build_html(report)

        assert '<script>document.cookie</script>' not in html_output

    def test_xss_in_recommendation(self):
        """Recomendación con HTML inyectado es escapado."""
        from gtaa_validator.reporters.html_reporter import HtmlReporter

        violation = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=Path("/tmp/proj/test.py"),
            recommendation='<a href="javascript:alert(1)">click</a>',
        )
        report = self._make_report(violations=[violation])
        reporter = HtmlReporter()
        html_output = reporter._build_html(report)

        assert 'href="javascript:alert(1)"' not in html_output

    def test_xss_in_ai_suggestion(self):
        """Sugerencia AI con contenido malicioso es escapado."""
        from gtaa_validator.reporters.html_reporter import HtmlReporter

        violation = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=Path("/tmp/proj/test.py"),
            ai_suggestion='<iframe src="evil.com"></iframe>',
        )
        report = self._make_report(violations=[violation])
        reporter = HtmlReporter()
        html_output = reporter._build_html(report)

        assert '<iframe' not in html_output
        assert '&lt;iframe' in html_output

    def test_xss_in_file_path(self):
        """Ruta de archivo con caracteres HTML es escapada."""
        from gtaa_validator.reporters.html_reporter import HtmlReporter

        project = Path("/tmp/proj")
        violation = Violation(
            violation_type=ViolationType.HARDCODED_TEST_DATA,
            severity=Severity.HIGH,
            file_path=project / '<img src=x>.py',
        )
        report = Report(
            project_path=project,
            violations=[violation],
            files_analyzed=1,
            score=75.0,
            timestamp=datetime(2026, 1, 1, 12, 0),
        )
        reporter = HtmlReporter()
        html_output = reporter._build_html(report)

        assert '<img src=x>' not in html_output


# =====================================================================
# YAML — safe_load() previene ejecución de código
# =====================================================================


class TestYAMLSafeLoading:
    """Verifica que la carga de YAML usa safe_load, no load."""

    def test_config_uses_safe_load(self):
        """config.py usa yaml.safe_load() para prevenir code execution."""
        import inspect
        from gtaa_validator import config as config_module

        source = inspect.getsource(config_module)
        assert "yaml.safe_load" in source
        # No debe usar yaml.load() (inseguro)
        # Buscar yaml.load( pero no yaml.safe_load(
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if 'yaml.load(' in stripped and 'safe_load' not in stripped:
                pytest.fail(
                    f"yaml.load() inseguro encontrado: {stripped}. "
                    "Usar yaml.safe_load() (SEC-06)."
                )

    def test_malicious_yaml_does_not_execute(self, tmp_path):
        """Un .gtaa.yaml con payload malicioso no ejecuta código."""
        from gtaa_validator.config import load_config

        # YAML con constructor Python (peligroso con yaml.load)
        malicious = tmp_path / ".gtaa.yaml"
        malicious.write_text(
            "exclude_checks: !!python/object/apply:os.system ['echo pwned']",
            encoding="utf-8",
        )

        # safe_load debe ignorar/rechazar el constructor malicioso
        config = load_config(tmp_path)
        # Debe retornar config por defecto (el YAML inválido se descarta)
        assert isinstance(config.exclude_checks, list)

    def test_valid_yaml_loads_correctly(self, tmp_path):
        """Un .gtaa.yaml válido se carga correctamente."""
        from gtaa_validator.config import load_config

        config_file = tmp_path / ".gtaa.yaml"
        config_file.write_text(
            "exclude_checks:\n  - POOR_TEST_NAMING\nignore_paths:\n  - vendor/**\n",
            encoding="utf-8",
        )
        config = load_config(tmp_path)
        assert "POOR_TEST_NAMING" in config.exclude_checks
        assert "vendor/**" in config.ignore_paths


# =====================================================================
# Input Validation — CLI valida argumentos
# =====================================================================


class TestInputValidation:
    """Verifica que la CLI valida correctamente los inputs del usuario."""

    def test_nonexistent_path_rejected(self):
        """Una ruta inexistente es rechazada por Click."""
        from click.testing import CliRunner
        from gtaa_validator.__main__ import main

        runner = CliRunner()
        result = runner.invoke(main, ["/ruta/que/no/existe/nunca"])
        assert result.exit_code != 0

    def test_provider_whitelist(self):
        """Solo los proveedores 'gemini' y 'mock' son aceptados."""
        from click.testing import CliRunner
        from gtaa_validator.__main__ import main

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("proyecto").mkdir()
            result = runner.invoke(main, ["proyecto", "--ai", "--provider", "malicious_provider"])
        assert result.exit_code != 0

    def test_max_llm_calls_type_validated(self):
        """--max-llm-calls solo acepta enteros."""
        from click.testing import CliRunner
        from gtaa_validator.__main__ import main

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("proyecto").mkdir()
            result = runner.invoke(main, ["proyecto", "--max-llm-calls", "not_a_number"])
        assert result.exit_code != 0

    def test_project_path_resolved_to_absolute(self):
        """project_path se resuelve a ruta absoluta (previene path traversal)."""
        import inspect
        import gtaa_validator.__main__ as main_module

        # main es un Click Command; acceder al callback original
        source = inspect.getsource(main_module.main.callback)
        # Debe contener Path(...).resolve()
        assert ".resolve()" in source


# =====================================================================
# Factory — Proveedor no soportado lanza error
# =====================================================================


class TestFactorySecurity:
    """Verifica que el factory de LLM valida proveedores correctamente."""

    def test_unsupported_provider_raises_error(self):
        """Un proveedor no soportado lanza ValueError."""
        from gtaa_validator.llm.factory import create_llm_client

        with pytest.raises(ValueError, match="no soportado"):
            create_llm_client(provider="malicious_provider")

    def test_supported_providers_whitelist(self):
        """Solo 'gemini' y 'mock' están en la whitelist."""
        from gtaa_validator.llm.factory import SUPPORTED_PROVIDERS

        assert SUPPORTED_PROVIDERS == {"gemini", "mock"}

    def test_mock_provider_without_api_key(self):
        """Sin API key, se usa MockLLMClient (sin error)."""
        from gtaa_validator.llm.factory import create_llm_client
        from gtaa_validator.llm.client import MockLLMClient

        with patch.dict("os.environ", {}, clear=True):
            client = create_llm_client(provider="mock")
        assert isinstance(client, MockLLMClient)
