"""
Checker BDD/Gherkin para gTAA Validator.

Detecta violaciones arquitectónicas en proyectos BDD:
- Archivos .feature con detalles de implementación
- Step definitions con llamadas directas al navegador
- Step definitions demasiado complejas
- Scenarios sin verificación (sin step Then)
- Step patterns duplicados entre archivos

Soporta Behave y pytest-bdd.

Fase 8: Soporte para la capa Gherkin en test automation.
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Set

logger = logging.getLogger(__name__)

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity
from gtaa_validator.parsers.gherkin_parser import GherkinParser


class BDDChecker(BaseChecker):
    """
    Verifica archivos BDD (.feature y step definitions) en busca de
    violaciones arquitectónicas gTAA.

    Detecta 5 tipos de violación:
    - GHERKIN_IMPLEMENTATION_DETAIL: detalles técnicos en .feature
    - STEP_DEF_DIRECT_BROWSER_CALL: browser API en step definitions
    - STEP_DEF_TOO_COMPLEX: step definition > 15 líneas
    - MISSING_THEN_STEP: scenario sin step Then
    - DUPLICATE_STEP_PATTERN: misma regex en múltiples step files
    """

    # Patrones técnicos que no deberían aparecer en archivos .feature
    IMPLEMENTATION_PATTERNS = [
        re.compile(r'//[\w\[\]@=\'"\.]+'),            # XPath
        re.compile(r'css='),                            # CSS selector prefix
        re.compile(r'#[\w-]{3,}'),                      # CSS ID selector (min 3 chars)
        re.compile(r'\.[\w-]{3,}\b'),                   # CSS class selector
        re.compile(r'By\.\w+'),                         # Selenium By.*
        re.compile(r'\[data-[\w-]+'),                   # data attributes
        re.compile(r'https?://\S+'),                    # URLs
        re.compile(r'SELECT\s+.+\s+FROM', re.IGNORECASE),  # SQL
        re.compile(r'INSERT\s+INTO', re.IGNORECASE),   # SQL
        re.compile(r'localhost:\d+'),                   # localhost URLs
        re.compile(r'<[\w/]+>'),                        # HTML tags
    ]

    # Métodos de Selenium/Playwright que indican llamadas directas
    BROWSER_METHODS = {
        # Selenium
        "find_element", "find_elements", "find_element_by_id",
        "find_element_by_name", "find_element_by_xpath",
        "find_element_by_css_selector",
        # Playwright
        "locator", "query_selector", "query_selector_all",
        "wait_for_selector",
    }

    # Objetos del navegador
    BROWSER_OBJECTS = {"driver", "page", "browser", "context"}

    # Umbral de líneas para step definitions complejas
    MAX_STEP_LINES = 15

    def __init__(self):
        super().__init__()
        self._parser = GherkinParser()
        self._step_patterns: Dict[str, List[Path]] = {}  # pattern → [files]

    def can_check(self, file_path: Path) -> bool:
        """Verificar archivos .feature y step definitions Python."""
        if file_path.suffix == ".feature":
            return True
        if file_path.suffix == ".py":
            return self._is_step_definition_path(file_path)
        return False

    def check(self, file_path: Path, tree: Optional[ast.Module] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo BDD en busca de violaciones.

        Para .feature: GHERKIN_IMPLEMENTATION_DETAIL, MISSING_THEN_STEP
        Para step defs: STEP_DEF_DIRECT_BROWSER_CALL, STEP_DEF_TOO_COMPLEX
        """
        if file_path.suffix == ".feature":
            return self._check_feature_file(file_path)
        else:
            return self._check_step_definition(file_path, tree)

    def check_project(self, project_path: Path) -> List[Violation]:
        """
        Verificación a nivel de proyecto: detectar step patterns duplicados.

        Escanea todos los archivos de step definitions y detecta decoradores
        @given/@when/@then con la misma regex en múltiples archivos.
        """
        self._step_patterns = {}
        violations = []

        # Recolectar patterns de todos los step files
        step_files = list(project_path.rglob("*.py"))
        for py_file in step_files:
            if not self._is_step_definition_path(py_file):
                continue
            self._collect_step_patterns(py_file)

        # Detectar duplicados
        for pattern, files in self._step_patterns.items():
            if len(files) > 1:
                # Reportar en el segundo archivo (el duplicado)
                for dup_file in files[1:]:
                    violations.append(Violation(
                        violation_type=ViolationType.DUPLICATE_STEP_PATTERN,
                        severity=Severity.LOW,
                        file_path=dup_file,
                        message=(
                            f"El step pattern '{pattern}' está duplicado. "
                            f"También definido en: {files[0]}"
                        ),
                    ))

        return violations

    # --- Verificación de archivos .feature ---

    def _check_feature_file(self, file_path: Path) -> List[Violation]:
        """Verificar un archivo .feature en busca de violaciones."""
        violations = []

        feature = self._parser.parse_file(file_path)
        if feature is None:
            return violations

        # Leer contenido para regex
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.debug("Error reading feature file %s: %s", file_path, e)
            return violations

        lines = content.splitlines()

        # 1. GHERKIN_IMPLEMENTATION_DETAIL: buscar detalles técnicos en steps
        for scenario in feature.scenarios:
            for step in scenario.steps:
                for pattern in self.IMPLEMENTATION_PATTERNS:
                    if pattern.search(step.text):
                        violations.append(Violation(
                            violation_type=ViolationType.GHERKIN_IMPLEMENTATION_DETAIL,
                            severity=Severity.HIGH,
                            file_path=file_path,
                            line_number=step.line,
                            message=(
                                f"El step '{step.keyword} {step.text}' contiene "
                                "detalles de implementación que deberían estar en step definitions"
                            ),
                            code_snippet=lines[step.line - 1].strip() if step.line <= len(lines) else "",
                        ))
                        break  # Un match por step es suficiente

        # También verificar Background
        if feature.background:
            for step in feature.background.steps:
                for pattern in self.IMPLEMENTATION_PATTERNS:
                    if pattern.search(step.text):
                        violations.append(Violation(
                            violation_type=ViolationType.GHERKIN_IMPLEMENTATION_DETAIL,
                            severity=Severity.HIGH,
                            file_path=file_path,
                            line_number=step.line,
                            message=(
                                f"El step '{step.keyword} {step.text}' contiene "
                                "detalles de implementación que deberían estar en step definitions"
                            ),
                            code_snippet=lines[step.line - 1].strip() if step.line <= len(lines) else "",
                        ))
                        break

        # 2. MISSING_THEN_STEP: scenarios sin verificación
        for scenario in feature.scenarios:
            if not scenario.has_then and len(scenario.steps) > 0:
                violations.append(Violation(
                    violation_type=ViolationType.MISSING_THEN_STEP,
                    severity=Severity.MEDIUM,
                    file_path=file_path,
                    line_number=scenario.line,
                    message=(
                        f"El Scenario '{scenario.name}' no tiene step Then "
                        "(sin verificación de resultado)"
                    ),
                    code_snippet=lines[scenario.line - 1].strip() if scenario.line <= len(lines) else "",
                ))

        return violations

    # --- Verificación de step definitions ---

    def _check_step_definition(self, file_path: Path,
                               tree: Optional[ast.Module] = None) -> List[Violation]:
        """Verificar step definitions en busca de violaciones."""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
        except Exception as e:
            logger.debug("Error reading step definition %s: %s", file_path, e)
            return violations

        if tree is None:
            try:
                tree = ast.parse(source_code, filename=str(file_path))
            except SyntaxError:
                return violations

        lines = source_code.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Detectar si es un step definition (tiene decorador @given/@when/@then)
            if not self._is_step_function(node):
                continue

            # 1. STEP_DEF_DIRECT_BROWSER_CALL
            browser_violations = self._check_browser_calls_in_step(node, file_path, lines)
            violations.extend(browser_violations)

            # 2. STEP_DEF_TOO_COMPLEX
            if hasattr(node, "end_lineno") and node.end_lineno:
                func_lines = node.end_lineno - node.lineno + 1
                if func_lines > self.MAX_STEP_LINES:
                    line_text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                    violations.append(Violation(
                        violation_type=ViolationType.STEP_DEF_TOO_COMPLEX,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=(
                            f"La step definition '{node.name}' tiene {func_lines} líneas "
                            f"(máximo recomendado: {self.MAX_STEP_LINES}). "
                            "Delegar lógica a Page Objects."
                        ),
                        code_snippet=line_text,
                    ))

        return violations

    def _check_browser_calls_in_step(self, func_node: ast.FunctionDef,
                                      file_path: Path,
                                      lines: List[str]) -> List[Violation]:
        """Detectar llamadas directas a browser APIs dentro de un step definition."""
        violations = []

        for node in ast.walk(func_node):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue

            method_name = node.func.attr
            object_name = self._get_object_name(node.func.value)

            if method_name in self.BROWSER_METHODS and object_name in self.BROWSER_OBJECTS:
                try:
                    code_snippet = ast.unparse(node)
                except AttributeError:
                    code_snippet = f"{object_name}.{method_name}(...)"

                violations.append(Violation(
                    violation_type=ViolationType.STEP_DEF_DIRECT_BROWSER_CALL,
                    severity=Severity.CRITICAL,
                    file_path=file_path,
                    line_number=node.lineno,
                    message=(
                        f"La step definition llama directamente a {object_name}.{method_name}() "
                        "en lugar de usar un Page Object"
                    ),
                    code_snippet=code_snippet,
                ))

        return violations

    # --- Utilidades ---

    def _is_step_definition_path(self, file_path: Path) -> bool:
        """Determinar si un archivo Python es un step definition por su ruta."""
        parts = [p.lower() for p in file_path.parts]
        name = file_path.name.lower()
        return (
            "steps" in parts
            or "step_defs" in parts
            or "step_definitions" in parts
            or name.startswith("step_")
            or name.startswith("steps_")
            or name.endswith("_steps.py")
        )

    def _is_step_function(self, node: ast.FunctionDef) -> bool:
        """Verificar si una función tiene decoradores @given/@when/@then."""
        step_decorators = {"given", "when", "then", "step"}

        for decorator in node.decorator_list:
            # @given("...")
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id.lower() in step_decorators:
                        return True
                # @parsers.cfparse / behave decorators
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr.lower() in step_decorators:
                        return True

            # @given (sin argumentos, raro pero posible)
            if isinstance(decorator, ast.Name):
                if decorator.id.lower() in step_decorators:
                    return True

        return False

    def _get_object_name(self, node: ast.AST) -> str:
        """Extraer nombre del objeto de un nodo AST."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_object_name(node.value)
        return ""

    def _collect_step_patterns(self, file_path: Path):
        """Recolectar step patterns de un archivo para detección de duplicados."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            logger.debug("Error parsing step patterns from %s: %s", file_path, e)
            return

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not self._is_step_function(node):
                continue

            # Extraer el pattern string del decorador
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and decorator.args:
                    arg = decorator.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        pattern = arg.value
                        if pattern not in self._step_patterns:
                            self._step_patterns[pattern] = []
                        self._step_patterns[pattern].append(file_path)
