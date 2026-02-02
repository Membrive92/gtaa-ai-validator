"""
Checker de la Capa de Definición para gTAA Validator.

Este checker detecta violaciones en la capa de Definición (archivos de test).
La violación principal detectada es ADAPTATION_IN_DEFINITION: cuando el código de test
llama directamente a APIs de Selenium o Playwright en lugar de usar Page Objects.

Conceptos clave:
- AST (Abstract Syntax Tree): Forma nativa de Python para parsear y analizar código
- Patrón Visitor: Recorrer el árbol AST y reaccionar a tipos de nodo específicos
- Análisis Estático: Analizar código sin ejecutarlo

Según la arquitectura gTAA:
- La capa de Definición (tests) solo debe llamar a Page Objects
- La capa de Adaptación (Page Objects) encapsula Selenium/Playwright
- Los archivos de test NO deben llamar directamente a driver.find_element(), page.locator(), etc.
"""

import ast
from pathlib import Path
from typing import List, Optional, Set

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class DefinitionChecker(BaseChecker):
    """
    Verifica archivos de test en busca de llamadas directas a APIs de Selenium/Playwright.

    Este checker parsea archivos Python de test y detecta cuando las funciones de test
    llaman directamente a APIs de automatización del navegador en lugar de usar Page Objects.

    Ejemplo de violación:
        def test_login():
            driver.find_element(By.ID, "username").send_keys("user")  # ¡VIOLACIÓN!

    Debería ser:
        def test_login():
            login_page.enter_username("user")  # OK - usa Page Object
    """

    # Nombres de métodos que indican uso directo de Selenium
    SELENIUM_METHODS = {
        "find_element",
        "find_elements",
        "find_element_by_id",
        "find_element_by_name",
        "find_element_by_xpath",
        "find_element_by_css_selector",
        "find_element_by_class_name",
        "find_element_by_tag_name",
        "find_element_by_link_text",
        "find_element_by_partial_link_text",
    }

    # Nombres de métodos que indican uso directo de Playwright
    PLAYWRIGHT_METHODS = {
        "locator",
        "query_selector",
        "query_selector_all",
        "wait_for_selector",
        "click",
        "fill",
        "type",
        "select_option",
    }

    # Nombres de objetos que indican objetos de automatización del navegador
    BROWSER_OBJECTS = {
        "driver",      # Selenium WebDriver
        "page",        # Playwright Page
        "browser",     # Playwright Browser
        "context",     # Playwright BrowserContext
    }

    def __init__(self):
        """Inicializar el DefinitionChecker."""
        super().__init__()
        self.violations: List[Violation] = []
        self.current_file: Path = None

    def can_check(self, file_path: Path) -> bool:
        """
        Solo verificar archivos Python que parecen ser archivos de test.

        Args:
            file_path: Ruta al archivo a verificar

        Returns:
            True si es un archivo Python de test, False en caso contrario
        """
        if file_path.suffix != ".py":
            return False

        filename = file_path.name
        # Verificar patrones comunes de nomenclatura de archivos de test
        is_test_file = (
            filename.startswith("test_") or
            filename.endswith("_test.py") or
            any(part in ("test", "tests") for part in file_path.parts)
        )
        return is_test_file

    def check(self, file_path: Path, tree: Optional[ast.Module] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo de test en busca de violaciones ADAPTATION_IN_DEFINITION.

        Args:
            file_path: Ruta al archivo de test a verificar
            tree: Árbol AST pre-parseado (opcional)
            file_type: Clasificación del archivo ('api', 'ui' o 'unknown')

        Returns:
            Lista de objetos Violation (vacía si no hay violaciones)
        """
        # API tests no usan Page Objects — ADAPTATION_IN_DEFINITION no aplica
        if file_type == "api":
            return []

        self.violations = []
        self.current_file = file_path

        try:
            if tree is None:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
                tree = ast.parse(source_code, filename=str(file_path))

            # Crear visitor y recorrer el AST
            visitor = BrowserAPICallVisitor(self)
            visitor.visit(tree)

        except SyntaxError:
            pass
        except Exception:
            pass

        return self.violations

    def add_violation(
        self,
        line_number: int,
        method_name: str,
        object_name: str,
        code_snippet: str
    ):
        """
        Añadir una violación a la lista.

        Args:
            line_number: Número de línea donde ocurre la violación
            method_name: Nombre del método prohibido llamado
            object_name: Nombre del objeto sobre el que se llamó el método
            code_snippet: El código real que violó la regla
        """
        violation = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=self.current_file,
            line_number=line_number,
            message=(
                f"El código de test llama directamente a {object_name}.{method_name}() "
                f"en lugar de usar un método de Page Object. "
                f"Según gTAA, la capa de Definición (tests) solo debe llamar "
                f"a la capa de Adaptación (Page Objects), no a las APIs del navegador directamente."
            ),
            code_snippet=code_snippet,
            recommendation=ViolationType.ADAPTATION_IN_DEFINITION.get_recommendation()
        )
        self.violations.append(violation)


class BrowserAPICallVisitor(ast.NodeVisitor):
    """
    Visitor AST que detecta llamadas directas a APIs de automatización del navegador
    en funciones de test.

    Detecta llamadas tanto a Selenium como a Playwright (y cualquier framework futuro)
    cuando se usan directamente dentro de funciones de test en lugar de a través de Page Objects.

    El Patrón Visitor nos permite recorrer el AST y reaccionar a tipos de nodo
    específicos sin modificar el AST en sí.

    Métodos clave:
    - visit_FunctionDef: Se llama para cada definición de función
    - visit_Call: Se llama para cada llamada a función
    - generic_visit: Comportamiento por defecto para nodos que no manejamos específicamente
    """

    def __init__(self, checker: DefinitionChecker):
        """
        Inicializar el visitor.

        Args:
            checker: La instancia de DefinitionChecker que creó este visitor
        """
        self.checker = checker
        self.inside_test_function = False
        self.current_function_name = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visitar un nodo de definición de función.

        Se llama para cada función en el archivo.
        Lo usamos para rastrear cuándo estamos dentro de una función de test.

        Args:
            node: El nodo AST FunctionDef
        """
        # Verificar si esta es una función de test (empieza con "test_")
        is_test = node.name.startswith("test_")

        if is_test:
            # Recordar que estamos dentro de una función de test
            previous_state = self.inside_test_function
            previous_name = self.current_function_name

            self.inside_test_function = True
            self.current_function_name = node.name

            # Visitar todos los nodos hijos (el cuerpo de la función)
            self.generic_visit(node)

            # Restaurar el estado previo al salir de la función
            self.inside_test_function = previous_state
            self.current_function_name = previous_name
        else:
            # No es una función de test, aún así visitar hijos pero no rastrear
            self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """
        Visitar un nodo de llamada a función.

        Se llama para cada llamada a función en el código.
        Verificamos si es una llamada prohibida a Selenium/Playwright.

        Args:
            node: El nodo AST Call
        """
        # Solo verificar llamadas dentro de funciones de test
        if self.inside_test_function:
            # Verificar si es una llamada a método (ej. objeto.metodo())
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr  # El método siendo llamado

                # Intentar obtener el nombre del objeto (ej. "driver", "page")
                object_name = self._get_object_name(node.func.value)

                # Verificar si esto es una violación
                is_selenium_call = method_name in DefinitionChecker.SELENIUM_METHODS
                is_playwright_call = method_name in DefinitionChecker.PLAYWRIGHT_METHODS
                is_browser_object = object_name in DefinitionChecker.BROWSER_OBJECTS

                if (is_selenium_call or is_playwright_call) and is_browser_object:
                    # ¡Violación encontrada!
                    code_snippet = self._get_code_snippet(node)
                    self.checker.add_violation(
                        line_number=node.lineno,
                        method_name=method_name,
                        object_name=object_name,
                        code_snippet=code_snippet
                    )

        # Continuar visitando nodos hijos
        self.generic_visit(node)

    def _get_object_name(self, node: ast.AST) -> str:
        """
        Extraer el nombre del objeto de un nodo AST.

        Ejemplos:
        - driver.find_element() -> "driver"
        - self.driver.find_element() -> "driver"
        - page.locator() -> "page"

        Args:
            node: Nodo AST representando el objeto

        Returns:
            El nombre del objeto como cadena, o cadena vacía si no se encuentra
        """
        if isinstance(node, ast.Name):
            # Nombre simple: driver
            return node.id
        elif isinstance(node, ast.Attribute):
            # Acceso a atributo: self.driver
            # Obtener recursivamente el nombre más a la derecha
            return self._get_object_name(node.value)
        else:
            return ""

    def _get_code_snippet(self, node: ast.Call) -> str:
        """
        Generar un fragmento de código legible para la violación.

        Esta es una versión simplificada — en producción se usaría
        ast.unparse() (Python 3.9+) o la librería astor para mejores resultados.

        Args:
            node: El nodo Call a convertir a código

        Returns:
            Representación en cadena del código
        """
        try:
            # Python 3.9+ tiene ast.unparse()
            return ast.unparse(node)
        except AttributeError:
            # Fallback para Python 3.8
            if isinstance(node.func, ast.Attribute):
                obj = self._get_object_name(node.func.value)
                method = node.func.attr
                return f"{obj}.{method}(...)"
            return "<código>"
