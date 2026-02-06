"""
Checker de la Capa de Definición para gTAA Validator.

Este checker detecta violaciones en la capa de Definición (archivos de test).
La violación principal detectada es ADAPTATION_IN_DEFINITION: cuando el código de test
llama directamente a APIs de Selenium o Playwright en lugar de usar Page Objects.

Según la arquitectura gTAA:
- La capa de Definición (tests) solo debe llamar a Page Objects
- La capa de Adaptación (Page Objects) encapsula Selenium/Playwright
- Los archivos de test NO deben llamar directamente a driver.find_element(), page.locator(), etc.

Fase 9+: Refactorizado para ser agnóstico al lenguaje usando ParseResult.
Soporta: Python, Java, JavaScript/TypeScript, C#
"""

import ast
from pathlib import Path
from typing import List, Optional, Set, Union

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity
from gtaa_validator.parsers.treesitter_base import (
    ParseResult, ParsedClass, ParsedFunction, ParsedCall
)


class DefinitionChecker(BaseChecker):
    """
    Verifica archivos de test en busca de llamadas directas a APIs de browser.

    Detecta ADAPTATION_IN_DEFINITION cuando el código de test llama directamente
    a APIs de automatización del navegador en lugar de usar Page Objects.

    Soporta: Python, Java, JavaScript/TypeScript, C#

    Ejemplo de violación (Python):
        def test_login():
            driver.find_element(By.ID, "username").send_keys("user")  # VIOLACIÓN

    Ejemplo de violación (Java):
        @Test
        public void testLogin() {
            driver.findElement(By.id("username")).sendKeys("user");  // VIOLACIÓN
        }

    Ejemplo de violación (JS/TS):
        test('login', async ({ page }) => {
            await page.locator('#username').fill('user');  // VIOLACIÓN
        });
    """

    # --- Python: Selenium/Playwright methods ---
    BROWSER_METHODS_PYTHON: Set[str] = {
        # Selenium
        "find_element", "find_elements",
        "find_element_by_id", "find_element_by_name", "find_element_by_xpath",
        "find_element_by_css_selector", "find_element_by_class_name",
        "find_element_by_tag_name", "find_element_by_link_text",
        # Playwright
        "locator", "query_selector", "query_selector_all",
        "wait_for_selector", "click", "fill", "type", "select_option",
    }

    # --- Java: Selenium methods ---
    BROWSER_METHODS_JAVA: Set[str] = {
        "findElement", "findElements", "get", "navigate", "switchTo",
        "getWindowHandle", "getWindowHandles", "close", "quit",
        "sendKeys", "click", "clear", "submit",
    }

    # --- JavaScript/TypeScript: Playwright/Cypress methods ---
    BROWSER_METHODS_JS: Set[str] = {
        # Playwright
        "locator", "getByRole", "getByText", "getByLabel", "getByPlaceholder",
        "getByAltText", "getByTitle", "getByTestId",
        "fill", "click", "type", "press", "check", "uncheck", "selectOption",
        "goto", "waitForSelector", "waitForLoadState",
        # Cypress
        "get", "find", "contains", "visit", "type", "click", "check", "select",
    }

    # --- C#: Selenium methods ---
    BROWSER_METHODS_CSHARP: Set[str] = {
        "FindElement", "FindElements", "Navigate", "SwitchTo",
        "GetWindowHandle", "GetWindowHandles", "Close", "Quit",
        "SendKeys", "Click", "Clear", "Submit",
    }

    # --- Browser objects por lenguaje ---
    BROWSER_OBJECTS_PYTHON: Set[str] = {"driver", "page", "browser", "context"}
    BROWSER_OBJECTS_JAVA: Set[str] = {"driver", "webDriver", "WebDriver", "this"}
    BROWSER_OBJECTS_JS: Set[str] = {"page", "browser", "context", "cy"}
    BROWSER_OBJECTS_CSHARP: Set[str] = {"driver", "_driver", "Driver", "WebDriver"}

    def __init__(self):
        """Inicializar el DefinitionChecker."""
        super().__init__()
        self.violations: List[Violation] = []
        self.current_file: Path = None

    def can_check(self, file_path: Path) -> bool:
        """
        True para archivos de test en cualquier lenguaje soportado.

        Args:
            file_path: Ruta al archivo a verificar

        Returns:
            True si es un archivo de test soportado
        """
        extension = file_path.suffix.lower()

        # Solo verificar extensiones soportadas
        if extension not in {".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".cs", ".mjs", ".cjs"}:
            return False

        filename = file_path.name.lower()
        parts_lower = [p.lower() for p in file_path.parts]

        # Detectar archivos de test según el lenguaje
        if extension == ".py":
            return (
                filename.startswith("test_") or
                filename.endswith("_test.py") or
                any(part in ("test", "tests") for part in parts_lower)
            )

        if extension == ".java":
            return (
                "test" in filename or
                any(part in ("test", "tests") for part in parts_lower)
            )

        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return (
                ".spec." in filename or
                ".test." in filename or
                any(part in ("tests", "test", "specs", "__tests__") for part in parts_lower)
            )

        if extension == ".cs":
            return (
                "test" in filename or
                any(part in ("test", "tests") for part in parts_lower)
            )

        return False

    def check(self, file_path: Path,
              tree_or_result: Optional[Union[ast.Module, ParseResult]] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo de test en busca de violaciones ADAPTATION_IN_DEFINITION.

        Args:
            file_path: Ruta al archivo de test a verificar
            tree_or_result: AST (Python legacy) o ParseResult (multi-lang)
            file_type: Clasificación del archivo ('api', 'ui' o 'unknown')

        Returns:
            Lista de objetos Violation
        """
        # API tests no usan Page Objects — ADAPTATION_IN_DEFINITION no aplica
        if file_type == "api":
            return []

        violations: List[Violation] = []
        self.current_file = file_path
        extension = file_path.suffix.lower()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            lines = source_code.splitlines()

            # Obtener ParseResult
            if isinstance(tree_or_result, ParseResult):
                result = tree_or_result
            elif isinstance(tree_or_result, ast.Module):
                # Legacy Python AST - convertir a ParseResult
                from gtaa_validator.parsers.python_parser import PythonParser
                parser = PythonParser()
                result = parser.parse(source_code)
            else:
                # Sin resultado previo - parsear
                from gtaa_validator.parsers.treesitter_base import get_parser_for_file
                parser = get_parser_for_file(file_path)
                if parser:
                    result = parser.parse(source_code)
                else:
                    return violations

            # Detectar llamadas a browser API en funciones de test
            violations.extend(self._check_browser_calls(
                file_path, result, lines, extension
            ))

        except SyntaxError:
            pass
        except Exception:
            pass

        return violations

    def _check_browser_calls(
        self, file_path: Path, result: ParseResult, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar llamadas directas a browser API en funciones de test."""
        violations: List[Violation] = []

        browser_methods = self._get_browser_methods(extension)
        browser_objects = self._get_browser_objects(extension)

        # Para JS/TS: los tests son callbacks, no funciones nombradas.
        # Si can_check() retorna True, sabemos que es un archivo de test.
        # En archivos de test JS/TS, cualquier llamada a browser API es violación.
        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            for call in result.calls:
                # Verificar si es una llamada a browser API
                is_browser_method = call.method_name in browser_methods
                is_browser_object = call.object_name in browser_objects

                if is_browser_method and is_browser_object:
                    snippet = lines[call.line - 1].strip() if call.line <= len(lines) else call.full_text
                    violations.append(
                        Violation(
                            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
                            severity=Severity.CRITICAL,
                            file_path=file_path,
                            line_number=call.line,
                            message=(
                                f"El código de test llama directamente a {call.object_name}.{call.method_name}() "
                                f"en lugar de usar un método de Page Object. "
                                f"Según gTAA, la capa de Definición (tests) solo debe llamar "
                                f"a la capa de Adaptación (Page Objects), no a las APIs del navegador directamente."
                            ),
                            code_snippet=snippet,
                            recommendation=ViolationType.ADAPTATION_IN_DEFINITION.get_recommendation()
                        )
                    )
            return violations

        # Verificar funciones de nivel superior (Python)
        for func in result.functions:
            if self._is_test_function(func, extension):
                violations.extend(self._check_function_for_browser_calls(
                    file_path, func, result.calls, lines, browser_methods, browser_objects
                ))

        # Verificar métodos de clase (Java, C#, Python class-based)
        for cls in result.classes:
            for method in cls.methods:
                if self._is_test_function(method, extension):
                    violations.extend(self._check_function_for_browser_calls(
                        file_path, method, result.calls, lines, browser_methods, browser_objects
                    ))

        return violations

    def _check_function_for_browser_calls(
        self, file_path: Path, func: ParsedFunction, all_calls: List[ParsedCall],
        lines: List[str], browser_methods: Set[str], browser_objects: Set[str]
    ) -> List[Violation]:
        """Verificar una función de test por llamadas a browser API."""
        violations = []

        for call in all_calls:
            # Verificar si la llamada está dentro de la función
            if not (func.line_start <= call.line <= func.line_end):
                continue

            # Verificar si es una llamada a browser API
            is_browser_method = call.method_name in browser_methods
            is_browser_object = call.object_name in browser_objects

            if is_browser_method and is_browser_object:
                snippet = lines[call.line - 1].strip() if call.line <= len(lines) else call.full_text
                violations.append(
                    Violation(
                        violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
                        severity=Severity.CRITICAL,
                        file_path=file_path,
                        line_number=call.line,
                        message=(
                            f"El código de test llama directamente a {call.object_name}.{call.method_name}() "
                            f"en lugar de usar un método de Page Object. "
                            f"Según gTAA, la capa de Definición (tests) solo debe llamar "
                            f"a la capa de Adaptación (Page Objects), no a las APIs del navegador directamente."
                        ),
                        code_snippet=snippet,
                        recommendation=ViolationType.ADAPTATION_IN_DEFINITION.get_recommendation()
                    )
                )

        return violations

    def _is_test_function(self, func: ParsedFunction, extension: str) -> bool:
        """Determina si una función es un test."""
        # Python: test_*
        if extension == ".py":
            return func.name.startswith("test_")

        # Java: @Test decorator
        if extension == ".java":
            test_annotations = {"Test", "ParameterizedTest", "RepeatedTest"}
            return any(d in test_annotations for d in func.decorators)

        # C#: [Test], [Fact], [Theory]
        if extension == ".cs":
            test_attributes = {"Test", "Fact", "Theory", "TestMethod"}
            return any(d in test_attributes for d in func.decorators)

        # JS/TS: funciones dentro de describe/it/test
        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            # Heurística: funciones con ciertos nombres o async arrow functions
            return func.name in {"it", "test"} or func.name.startswith("test")

        return False

    def _get_browser_methods(self, extension: str) -> Set[str]:
        """Obtiene los métodos de browser API para un lenguaje."""
        if extension == ".py":
            return self.BROWSER_METHODS_PYTHON
        elif extension == ".java":
            return self.BROWSER_METHODS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.BROWSER_METHODS_JS
        elif extension == ".cs":
            return self.BROWSER_METHODS_CSHARP
        return set()

    def _get_browser_objects(self, extension: str) -> Set[str]:
        """Obtiene los nombres de objetos browser para un lenguaje."""
        if extension == ".py":
            return self.BROWSER_OBJECTS_PYTHON
        elif extension == ".java":
            return self.BROWSER_OBJECTS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.BROWSER_OBJECTS_JS
        elif extension == ".cs":
            return self.BROWSER_OBJECTS_CSHARP
        return set()

