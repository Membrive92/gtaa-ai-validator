"""
Checker de la Capa de Adaptación para gTAA Validator.

Verifica archivos de Page Object en busca de violaciones arquitectónicas:
- Aserciones (solo deben estar en tests)
- Imports prohibidos (los frameworks de test no pertenecen a Page Objects)
- Lógica de negocio (if/else/for/while — debe estar en una capa de servicio)
- Localizadores duplicados (mismo selector en múltiples Page Objects)

Según gTAA:
- Los Page Objects solo deben interactuar con la UI
- Los Page Objects NO deben contener aserciones de test
- Los Page Objects NO deben contener lógica de negocio compleja
- Los localizadores deben estar centralizados y no duplicados

Fase 9+: Refactorizado para ser agnóstico al lenguaje usando ParseResult.
Soporta: Python, Java, JavaScript/TypeScript, C#
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.file_utils import read_file_safe
from gtaa_validator.models import Violation, ViolationType, Severity
from gtaa_validator.parsers.treesitter_base import (
    ParseResult, ParsedClass, ParsedFunction, ParsedCall, ParsedImport
)


class AdaptationChecker(BaseChecker):
    """
    Verifica archivos de Page Object en busca de violaciones gTAA.

    Detecta (agnóstico al lenguaje):
    - ASSERTION_IN_POM: aserciones dentro de métodos de Page Object
    - FORBIDDEN_IMPORT: imports de frameworks de test
    - BUSINESS_LOGIC_IN_POM: if/for/while dentro de métodos de clase
    - DUPLICATE_LOCATOR: misma cadena de localizador en múltiples Page Objects

    Soporta: Python, Java, JavaScript/TypeScript, C#
    """

    # Módulos prohibidos en Page Objects por lenguaje
    FORBIDDEN_MODULES_PYTHON: Set[str] = {"pytest", "unittest"}
    FORBIDDEN_MODULES_JAVA: Set[str] = {"org.junit", "org.testng", "org.junit.jupiter", "org.assertj"}
    FORBIDDEN_MODULES_JS: Set[str] = {"jest", "mocha", "jasmine", "@jest/globals", "chai"}
    FORBIDDEN_MODULES_CSHARP: Set[str] = {"NUnit.Framework", "Xunit", "Microsoft.VisualStudio.TestTools"}

    # Métodos de aserción por lenguaje
    ASSERTION_METHODS_PYTHON: Set[str] = {"assert", "assertEqual", "assertTrue", "assertFalse"}
    ASSERTION_METHODS_JAVA: Set[str] = {
        "assertEquals", "assertNotEquals", "assertTrue", "assertFalse",
        "assertNull", "assertNotNull", "assertThat", "assertThrows", "fail",
    }
    ASSERTION_METHODS_JS: Set[str] = {
        "expect", "assert", "should", "toBe", "toEqual", "toHaveLength",
        "toContain", "toThrow", "toMatch",
    }
    ASSERTION_METHODS_CSHARP: Set[str] = {
        "Assert", "AreEqual", "AreNotEqual", "IsTrue", "IsFalse",
        "IsNull", "IsNotNull", "That", "Throws",
    }

    # Patrones regex para extraer valores de selectores de localizadores
    LOCATOR_PATTERNS = [
        re.compile(r'By\.\w+,\s*["\']([^"\']+)["\']'),
        re.compile(r'\(By\.\w+,\s*["\']([^"\']+)["\']\)'),
        re.compile(r'getByRole\(["\']([^"\']+)["\']'),
        re.compile(r'getByText\(["\']([^"\']+)["\']'),
        re.compile(r'locator\(["\']([^"\']+)["\']'),
        re.compile(r'querySelector\(["\']([^"\']+)["\']'),
        re.compile(r'\$\(["\']([^"\']+)["\']'),
        re.compile(r'cy\.get\(["\']([^"\']+)["\']'),
    ]

    def __init__(self):
        super().__init__()
        # Rastrea localizador → lista de archivos, se reinicia por cada ejecución de análisis
        self._locator_registry: Dict[str, List[Path]] = defaultdict(list)

    def can_check(self, file_path: Path) -> bool:
        """
        True para archivos de Page Object en cualquier lenguaje soportado.

        Heurísticas:
        - El archivo está dentro de un directorio pages/, page_objects/ o pom/
        - O el nombre del archivo contiene 'page'
        - Y el archivo NO está dentro de un directorio de test
        """
        extension = file_path.suffix.lower()

        # Solo verificar extensiones soportadas
        if extension not in {".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".cs", ".mjs", ".cjs"}:
            return False

        parts_lower = [p.lower() for p in file_path.parts]
        filename = file_path.name.lower()

        in_page_dir = any(
            part in {"pages", "page_objects", "pom", "pageobjects"}
            for part in parts_lower
        )

        is_page_file = (
            "_page." in filename or
            "page." in filename or
            "_pom." in filename or
            filename.endswith("page" + extension)
        )

        in_test_dir = any(
            part in {"tests", "test", "specs", "spec", "__tests__"}
            for part in parts_lower
        )

        return (in_page_dir or is_page_file) and not in_test_dir

    def check(self, file_path: Path,
              tree_or_result: Optional[Union[ast.Module, ParseResult]] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo de Page Object en busca de violaciones.

        Ejecuta verificaciones:
        1. Imports prohibidos (pytest, unittest, JUnit, etc.)
        2. Aserciones dentro de métodos de clase
        3. Lógica de negocio (if/for/while) dentro de métodos de clase
        4. Localizadores duplicados entre Page Objects

        Args:
            file_path: Ruta al archivo a verificar
            tree_or_result: AST (Python legacy) o ParseResult (multi-lang)
            file_type: Clasificación del archivo
        """
        violations: List[Violation] = []
        extension = file_path.suffix.lower()

        try:
            source_code = read_file_safe(file_path)
            if not source_code:
                return violations
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

            # Ejecutar verificaciones
            violations.extend(self._check_forbidden_imports(file_path, result, lines, extension))
            violations.extend(self._check_assertions(file_path, result, lines, extension))
            violations.extend(self._check_business_logic(file_path, source_code, lines, extension))
            violations.extend(self._check_duplicate_locators(file_path, source_code))

        except SyntaxError:
            pass
        except Exception as e:
            logger.debug("Error checking %s: %s", file_path, e)

        return violations

    # ------------------------------------------------------------------
    # Sub-verificaciones
    # ------------------------------------------------------------------

    def _check_forbidden_imports(
        self, file_path: Path, result: ParseResult, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar imports de frameworks de test en archivos de Page Object."""
        violations: List[Violation] = []
        forbidden_modules = self._get_forbidden_modules(extension)

        for imp in result.imports:
            root_module = imp.module.split(".")[0]

            # Verificar si el import es de un módulo prohibido
            is_forbidden = any(
                imp.module == mod or
                imp.module.startswith(f"{mod}.") or
                root_module == mod
                for mod in forbidden_modules
            )

            if is_forbidden:
                snippet = lines[imp.line - 1].strip() if imp.line <= len(lines) else f"import {imp.module}"
                violations.append(
                    Violation(
                        violation_type=ViolationType.FORBIDDEN_IMPORT,
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=imp.line,
                        message=(
                            f"El Page Object importa el framework de test '{imp.module}'. "
                            f"Los frameworks de test solo deben importarse en archivos de test, "
                            f"no en la capa de Adaptación."
                        ),
                        code_snippet=snippet,
                    )
                )

        return violations

    def _check_assertions(
        self, file_path: Path, result: ParseResult, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar aserciones dentro de métodos de Page Object."""
        violations: List[Violation] = []
        assertion_methods = self._get_assertion_methods(extension)

        for cls in result.classes:
            if not cls.is_page_object:
                continue

            for method in cls.methods:
                # Buscar llamadas a métodos de aserción dentro de este método
                assertion_calls = self._find_assertion_calls_in_method(
                    method, result.calls, assertion_methods
                )

                for call in assertion_calls:
                    snippet = lines[call.line - 1].strip() if call.line <= len(lines) else call.full_text
                    violations.append(
                        Violation(
                            violation_type=ViolationType.ASSERTION_IN_POM,
                            severity=Severity.HIGH,
                            file_path=file_path,
                            line_number=call.line,
                            message=(
                                f"El método '{method.name}' del Page Object contiene una aserción "
                                f"'{call.method_name}'. Las aserciones pertenecen a la capa de "
                                f"Definición (tests), no a los Page Objects. "
                                f"Devuelva el valor y deje que el test lo verifique."
                            ),
                            code_snippet=snippet,
                        )
                    )

        # Para Python, también detectar sentencias 'assert' (no son llamadas)
        if extension == ".py":
            try:
                tree = ast.parse("\n".join(lines))
                visitor = _AssertionVisitor(file_path)
                visitor.visit(tree)
                violations.extend(visitor.violations)
            except SyntaxError:
                pass

        return violations

    def _check_business_logic(
        self, file_path: Path, source_code: str, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar lógica de negocio compleja en Page Objects."""
        violations: List[Violation] = []

        # Para Python, usar AST para detección precisa
        if extension == ".py":
            try:
                tree = ast.parse(source_code)
                visitor = _BusinessLogicVisitor(file_path)
                visitor.visit(tree)
                violations.extend(visitor.violations)
            except SyntaxError:
                pass
        else:
            # Para otros lenguajes, usar detección basada en regex/patrones
            violations.extend(self._check_business_logic_regex(file_path, source_code, lines))

        return violations

    def _check_business_logic_regex(
        self, file_path: Path, source_code: str, lines: List[str]
    ) -> List[Violation]:
        """Detección de lógica de negocio usando regex (para lenguajes no-Python)."""
        violations = []

        # Patrones de control flow
        control_patterns = [
            (re.compile(r'^\s*if\s*\('), "if/else"),
            (re.compile(r'^\s*for\s*\('), "bucle for"),
            (re.compile(r'^\s*while\s*\('), "bucle while"),
            (re.compile(r'^\s*switch\s*\('), "switch"),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern, construct in control_patterns:
                if pattern.search(line):
                    violations.append(
                        Violation(
                            violation_type=ViolationType.BUSINESS_LOGIC_IN_POM,
                            severity=Severity.MEDIUM,
                            file_path=file_path,
                            line_number=i,
                            message=(
                                f"El Page Object contiene {construct}. "
                                f"La lógica compleja debe estar en una capa de servicio separada, "
                                f"no en los Page Objects."
                            ),
                            code_snippet=line.strip(),
                        )
                    )

        return violations

    def _check_duplicate_locators(
        self, file_path: Path, source_code: str
    ) -> List[Violation]:
        """Detectar cadenas de localizador que aparecen en múltiples archivos de Page Object."""
        violations: List[Violation] = []

        for pattern in self.LOCATOR_PATTERNS:
            for match in pattern.finditer(source_code):
                locator = match.group(1)
                existing = self._locator_registry[locator]

                if existing and file_path not in existing:
                    line_number = source_code[: match.start()].count("\n") + 1
                    other_names = ", ".join(f.name for f in existing)
                    violations.append(
                        Violation(
                            violation_type=ViolationType.DUPLICATE_LOCATOR,
                            severity=Severity.MEDIUM,
                            file_path=file_path,
                            line_number=line_number,
                            message=(
                                f"El localizador '{locator}' está duplicado entre Page Objects. "
                                f"También se encuentra en: {other_names}. "
                                f"Considere centralizar los localizadores en una página base o repositorio."
                            ),
                            code_snippet=locator,
                        )
                    )

                if file_path not in existing:
                    existing.append(file_path)

        return violations

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_forbidden_modules(self, extension: str) -> Set[str]:
        """Obtiene los módulos prohibidos para un lenguaje."""
        if extension == ".py":
            return self.FORBIDDEN_MODULES_PYTHON
        elif extension == ".java":
            return self.FORBIDDEN_MODULES_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.FORBIDDEN_MODULES_JS
        elif extension == ".cs":
            return self.FORBIDDEN_MODULES_CSHARP
        return set()

    def _get_assertion_methods(self, extension: str) -> Set[str]:
        """Obtiene los métodos de aserción para un lenguaje."""
        if extension == ".py":
            return self.ASSERTION_METHODS_PYTHON
        elif extension == ".java":
            return self.ASSERTION_METHODS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.ASSERTION_METHODS_JS
        elif extension == ".cs":
            return self.ASSERTION_METHODS_CSHARP
        return set()

    def _find_assertion_calls_in_method(
        self, method: ParsedFunction, all_calls: List[ParsedCall], assertion_methods: Set[str]
    ) -> List[ParsedCall]:
        """Encuentra llamadas a aserciones dentro de un método."""
        assertion_calls = []

        for call in all_calls:
            # Verificar si la llamada está dentro del rango del método
            if method.line_start <= call.line <= method.line_end:
                # Verificar si es una llamada a método de aserción
                if (call.method_name in assertion_methods or
                    call.method_name.startswith("assert") or
                    call.method_name.startswith("verify") or
                    call.object_name in {"Assert", "Assertions", "expect"}):
                    assertion_calls.append(call)

        return assertion_calls


# ======================================================================
# Visitors AST (solo para Python)
# ======================================================================


class _AssertionVisitor(ast.NodeVisitor):
    """Detecta sentencias assert dentro de métodos de clase."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: List[Violation] = []
        self._in_class = False
        self._in_method = False

    def visit_ClassDef(self, node: ast.ClassDef):
        prev = self._in_class
        self._in_class = True
        self.generic_visit(node)
        self._in_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._in_class:
            prev = self._in_method
            self._in_method = True
            self.generic_visit(node)
            self._in_method = prev
        else:
            self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert):
        if self._in_class and self._in_method:
            try:
                snippet = ast.unparse(node)
            except AttributeError:
                snippet = "assert ..."
            self.violations.append(
                Violation(
                    violation_type=ViolationType.ASSERTION_IN_POM,
                    severity=Severity.HIGH,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    message=(
                        "El método del Page Object contiene una aserción. "
                        "Las aserciones pertenecen a la capa de Definición (tests), no a los Page Objects. "
                        "Devuelva el valor y deje que el test lo verifique."
                    ),
                    code_snippet=snippet,
                )
            )
        self.generic_visit(node)


class _BusinessLogicVisitor(ast.NodeVisitor):
    """Detecta if/for/while dentro de métodos de clase."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: List[Violation] = []
        self._in_class = False
        self._in_method = False

    def visit_ClassDef(self, node: ast.ClassDef):
        prev = self._in_class
        self._in_class = True
        self.generic_visit(node)
        self._in_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._in_class:
            prev = self._in_method
            self._in_method = True
            self.generic_visit(node)
            self._in_method = prev
        else:
            self.generic_visit(node)

    def _add_violation(self, node: ast.AST, construct: str):
        self.violations.append(
            Violation(
                violation_type=ViolationType.BUSINESS_LOGIC_IN_POM,
                severity=Severity.MEDIUM,
                file_path=self.file_path,
                line_number=node.lineno,
                message=(
                    f"El método del Page Object contiene {construct}. "
                    f"La lógica compleja debe estar en una capa de servicio separada, "
                    f"no en los Page Objects."
                ),
                code_snippet=f"sentencia {construct}",
            )
        )

    def visit_If(self, node: ast.If):
        if self._in_class and self._in_method:
            self._add_violation(node, "if/else")
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        if self._in_class and self._in_method:
            self._add_violation(node, "bucle for")
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        if self._in_class and self._in_method:
            self._add_violation(node, "bucle while")
        self.generic_visit(node)
