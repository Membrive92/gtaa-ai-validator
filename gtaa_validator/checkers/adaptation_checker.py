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
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class AdaptationChecker(BaseChecker):
    """
    Verifica archivos de Page Object en busca de violaciones gTAA.

    Detecta:
    - ASSERTION_IN_POM: sentencias assert dentro de métodos de clase
    - FORBIDDEN_IMPORT: imports de pytest o unittest
    - BUSINESS_LOGIC_IN_POM: if/for/while dentro de métodos de clase
    - DUPLICATE_LOCATOR: misma cadena de localizador en múltiples Page Objects
    """

    # Módulos prohibidos en Page Objects
    FORBIDDEN_MODULES = {"pytest", "unittest"}

    # Patrones regex para extraer valores de selectores de localizadores
    LOCATOR_PATTERNS = [
        re.compile(r'By\.\w+,\s*["\']([^"\']+)["\']'),
        re.compile(r'\(By\.\w+,\s*["\']([^"\']+)["\']\)'),
    ]

    def __init__(self):
        super().__init__()
        # Rastrea localizador → lista de archivos, se reinicia por cada ejecución de análisis
        self._locator_registry: Dict[str, List[Path]] = defaultdict(list)

    def can_check(self, file_path: Path) -> bool:
        """
        True para archivos de Page Object.

        Heurísticas:
        - El archivo está dentro de un directorio pages/, page_objects/ o pom/
        - O el nombre del archivo termina en _page.py o _pom.py
        - Y el archivo NO está dentro de un directorio de test
        """
        if file_path.suffix != ".py":
            return False

        parts_lower = [p.lower() for p in file_path.parts]
        filename = file_path.name.lower()

        in_page_dir = any(
            part in {"pages", "page_objects", "pom"} for part in parts_lower
        )
        is_page_file = filename.endswith("_page.py") or filename.endswith("_pom.py")
        in_test_dir = any(part in {"tests", "test"} for part in parts_lower)

        return (in_page_dir or is_page_file) and not in_test_dir

    def check(self, file_path: Path, tree: Optional[ast.Module] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo de Page Object en busca de violaciones.

        Ejecuta cuatro sub-verificaciones:
        1. Imports prohibidos (pytest, unittest)
        2. Aserciones dentro de métodos de clase
        3. Lógica de negocio (if/for/while) dentro de métodos de clase
        4. Localizadores duplicados entre Page Objects

        Args:
            file_path: Ruta al archivo a verificar
            tree: Árbol AST pre-parseado (opcional)
        """
        violations: List[Violation] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            if tree is None:
                tree = ast.parse(source_code, filename=str(file_path))

            violations.extend(self._check_forbidden_imports(file_path, tree))
            violations.extend(self._check_assertions(file_path, tree))
            violations.extend(self._check_business_logic(file_path, tree))
            violations.extend(self._check_duplicate_locators(file_path, source_code))

        except SyntaxError:
            pass
        except Exception:
            pass

        return violations

    # ------------------------------------------------------------------
    # Sub-verificaciones
    # ------------------------------------------------------------------

    def _check_forbidden_imports(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar imports de frameworks de test en archivos de Page Object."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.FORBIDDEN_MODULES:
                        violations.append(
                            Violation(
                                violation_type=ViolationType.FORBIDDEN_IMPORT,
                                severity=Severity.HIGH,
                                file_path=file_path,
                                line_number=node.lineno,
                                message=(
                                    f"El Page Object importa el framework de test '{alias.name}'. "
                                    f"Los frameworks de test solo deben importarse en archivos de test, "
                                    f"no en la capa de Adaptación."
                                ),
                                code_snippet=f"import {alias.name}",
                            )
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module and any(
                    node.module == mod or node.module.startswith(f"{mod}.")
                    for mod in self.FORBIDDEN_MODULES
                ):
                    violations.append(
                        Violation(
                            violation_type=ViolationType.FORBIDDEN_IMPORT,
                            severity=Severity.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            message=(
                                f"El Page Object importa del framework de test '{node.module}'. "
                                f"Los frameworks de test solo deben importarse en archivos de test."
                            ),
                            code_snippet=f"from {node.module} import ...",
                        )
                    )

        return violations

    def _check_assertions(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar sentencias assert dentro de métodos de clase."""
        visitor = _AssertionVisitor(file_path)
        visitor.visit(tree)
        return visitor.violations

    def _check_business_logic(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar if/for/while dentro de métodos de clase."""
        visitor = _BusinessLogicVisitor(file_path)
        visitor.visit(tree)
        return visitor.violations

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


# ======================================================================
# Visitors AST
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
