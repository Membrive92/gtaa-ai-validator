"""
Checker de Calidad para gTAA Validator.

Verifica archivos de test en busca de problemas de calidad de código:
- Datos de test hardcodeados (emails, URLs, números de teléfono, contraseñas)
- Funciones de test largas (>50 líneas)
- Convenciones de nomenclatura pobres (test_1, test_2, test_a)
- Manejo de excepciones genérico (except: / except Exception:)
- Configuración hardcodeada (URLs base, sleeps, timeouts)
- Estado mutable compartido a nivel de módulo

Estas violaciones indican pobre mantenibilidad y diseño de tests,
incluso si no rompen directamente la separación de capas gTAA.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class QualityChecker(BaseChecker):
    """
    Verifica archivos de test en busca de problemas de calidad.

    Detecta:
    - HARDCODED_TEST_DATA: emails, URLs, teléfonos, contraseñas en código de test
    - LONG_TEST_FUNCTION: funciones de test que exceden MAX_TEST_LINES
    - POOR_TEST_NAMING: nombres genéricos como test_1, test_a
    """

    # Patrones regex para datos hardcodeados
    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )
    URL_PATTERN = re.compile(r"https?://[^\s\"']+")
    PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")

    # Palabras clave que sugieren una cadena de contraseña
    PASSWORD_KEYWORDS = {"password", "passwd", "pwd"}

    # Patrones de nombres genéricos de test
    GENERIC_NAME_RE = re.compile(
        r"^test_[0-9]+$|^test_[a-z]$|^test_case[0-9]*$"
    )

    # Patrones de configuración hardcodeada
    LOCALHOST_PATTERN = re.compile(r"https?://localhost[:\d/]|https?://127\.0\.0\.1[:\d/]")
    SLEEP_PATTERN = re.compile(r"time\.sleep\s*\(\s*\d")
    ABSOLUTE_PATH_PATTERN = re.compile(r'["\'][A-Z]:\\|["\']/home/|["\']/usr/|["\']/tmp/')

    MAX_TEST_LINES = 50

    def can_check(self, file_path: Path) -> bool:
        """
        True para archivos de test (misma heurística que DefinitionChecker).
        """
        if file_path.suffix != ".py":
            return False

        filename = file_path.name
        return (
            filename.startswith("test_")
            or filename.endswith("_test.py")
            or any(part in ("test", "tests") for part in file_path.parts)
        )

    def check(self, file_path: Path, tree: Optional[ast.Module] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo de test en busca de violaciones de calidad.

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

            violations.extend(self._check_hardcoded_data(file_path, tree))
            violations.extend(self._check_long_functions(file_path, tree))
            violations.extend(self._check_test_naming(file_path, tree))
            violations.extend(self._check_broad_exception_handling(file_path, tree))
            violations.extend(self._check_hardcoded_configuration(file_path, source_code))
            violations.extend(self._check_shared_mutable_state(file_path, tree))

        except SyntaxError:
            pass
        except Exception:
            pass

        return violations

    # ------------------------------------------------------------------
    # Sub-verificaciones
    # ------------------------------------------------------------------

    def _check_hardcoded_data(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar datos de test hardcodeados (emails, URLs, teléfonos, contraseñas)."""
        visitor = _HardcodedDataVisitor(file_path)
        visitor.visit(tree)
        return visitor.violations

    def _check_long_functions(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar funciones de test más largas que MAX_TEST_LINES."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
                continue

            # Recopilar todos los números de línea dentro de la función para medir la extensión
            lines = set()
            for child in ast.walk(node):
                if hasattr(child, "lineno"):
                    lines.add(child.lineno)
                if hasattr(child, "end_lineno") and child.end_lineno:
                    lines.add(child.end_lineno)

            if not lines:
                continue

            length = max(lines) - min(lines) + 1
            if length > self.MAX_TEST_LINES:
                violations.append(
                    Violation(
                        violation_type=ViolationType.LONG_TEST_FUNCTION,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=(
                            f"La función de test '{node.name}' tiene {length} líneas "
                            f"(límite: {self.MAX_TEST_LINES}). "
                            f"Los tests largos son difíciles de entender y mantener. "
                            f"Considere dividirlo en tests más pequeños y enfocados."
                        ),
                        code_snippet=f"def {node.name}(...):",
                    )
                )

        return violations

    def _check_test_naming(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar nombres de funciones de test genéricos / no descriptivos."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
                continue

            if self.GENERIC_NAME_RE.match(node.name):
                violations.append(
                    Violation(
                        violation_type=ViolationType.POOR_TEST_NAMING,
                        severity=Severity.LOW,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=(
                            f"El test tiene un nombre genérico '{node.name}'. "
                            f"Use nombres descriptivos como "
                            f"'test_usuario_puede_hacer_login_con_credenciales_validas' "
                            f"en lugar de '{node.name}'."
                        ),
                        code_snippet=f"def {node.name}(...):",
                    )
                )

        return violations

    def _check_broad_exception_handling(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar except genérico (except: o except Exception:) en tests."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            # except: (bare) — node.type is None
            # except Exception: — node.type is ast.Name with id "Exception"
            is_bare = node.type is None
            is_broad = (
                isinstance(node.type, ast.Name) and node.type.id == "Exception"
            )

            if is_bare or is_broad:
                kind = "except:" if is_bare else "except Exception:"
                violations.append(
                    Violation(
                        violation_type=ViolationType.BROAD_EXCEPTION_HANDLING,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=(
                            f"Manejo de excepción genérico '{kind}' detectado. "
                            f"Capturar excepciones específicas para no ocultar fallos reales."
                        ),
                        code_snippet=kind,
                    )
                )

        return violations

    def _check_hardcoded_configuration(
        self, file_path: Path, source_code: str
    ) -> List[Violation]:
        """Detectar configuración hardcodeada (localhost URLs, sleeps, paths absolutos)."""
        violations: List[Violation] = []

        for i, line in enumerate(source_code.splitlines(), start=1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            if self.LOCALHOST_PATTERN.search(line):
                violations.append(
                    Violation(
                        violation_type=ViolationType.HARDCODED_CONFIGURATION,
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=i,
                        message="URL localhost hardcodeada. Externalizar en configuración o fixtures.",
                        code_snippet=stripped,
                    )
                )

            if self.SLEEP_PATTERN.search(line):
                violations.append(
                    Violation(
                        violation_type=ViolationType.HARDCODED_CONFIGURATION,
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=i,
                        message="time.sleep() hardcodeado. Usar esperas condicionales o configuración centralizada.",
                        code_snippet=stripped,
                    )
                )

            if self.ABSOLUTE_PATH_PATTERN.search(line):
                violations.append(
                    Violation(
                        violation_type=ViolationType.HARDCODED_CONFIGURATION,
                        severity=Severity.HIGH,
                        file_path=file_path,
                        line_number=i,
                        message="Path absoluto hardcodeado. Usar paths relativos o configuración.",
                        code_snippet=stripped,
                    )
                )

        return violations

    def _check_shared_mutable_state(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar estado mutable compartido a nivel de módulo y uso de global."""
        violations: List[Violation] = []

        # Check module-level mutable assignments (list, dict, set literals)
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                # Skip UPPERCASE constants and private vars
                if target.id.isupper() or target.id.startswith("_"):
                    continue
                # Check if value is mutable literal: [], {}, set()
                val = node.value
                is_mutable = (
                    isinstance(val, ast.List)
                    or isinstance(val, ast.Dict)
                    or isinstance(val, ast.Set)
                    or (isinstance(val, ast.Call)
                        and isinstance(val.func, ast.Name)
                        and val.func.id in ("list", "dict", "set"))
                )
                if is_mutable:
                    violations.append(
                        Violation(
                            violation_type=ViolationType.SHARED_MUTABLE_STATE,
                            severity=Severity.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            message=(
                                f"Variable mutable '{target.id}' a nivel de módulo. "
                                f"Los tests comparten este estado, creando dependencias implícitas."
                            ),
                            code_snippet=f"{target.id} = ...",
                        )
                    )

        # Check 'global' keyword usage inside test functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                for child in ast.walk(node):
                    if isinstance(child, ast.Global):
                        for name in child.names:
                            violations.append(
                                Violation(
                                    violation_type=ViolationType.SHARED_MUTABLE_STATE,
                                    severity=Severity.HIGH,
                                    file_path=file_path,
                                    line_number=child.lineno,
                                    message=(
                                        f"Uso de 'global {name}' en test. "
                                        f"Los tests deben ser independientes sin estado global."
                                    ),
                                    code_snippet=f"global {name}",
                                )
                            )

        return violations


# ======================================================================
# Visitor AST
# ======================================================================


class _HardcodedDataVisitor(ast.NodeVisitor):
    """Detecta datos de test hardcodeados dentro de funciones de test."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: List[Violation] = []
        self._in_test = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name.startswith("test_"):
            prev = self._in_test
            self._in_test = True
            self.generic_visit(node)
            self._in_test = prev
        else:
            self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        """Verificar constantes de cadena (Python 3.8+)."""
        if self._in_test and isinstance(node.value, str):
            self._check_string(node.value, node.lineno)
        self.generic_visit(node)

    # Compatibilidad con Python 3.7
    visit_Str = visit_Constant

    def _check_string(self, value: str, lineno: int):
        # Ignorar cadenas muy cortas (probablemente IDs de localizador, palabras sueltas)
        if len(value) < 5:
            return

        if QualityChecker.EMAIL_PATTERN.search(value):
            self._add(lineno, f"Email hardcodeado encontrado: '{value}'", value)

        if QualityChecker.URL_PATTERN.search(value):
            self._add(lineno, f"URL hardcodeada encontrada: '{value}'", value)

        if QualityChecker.PHONE_PATTERN.search(value):
            self._add(lineno, f"Número de teléfono hardcodeado encontrado: '{value}'", value)

        value_lower = value.lower()
        for kw in QualityChecker.PASSWORD_KEYWORDS:
            if kw in value_lower:
                self._add(
                    lineno,
                    "Cadena con aspecto de contraseña hardcodeada encontrada en el test.",
                    value,
                )
                break

    def _add(self, lineno: int, message: str, value: str):
        self.violations.append(
            Violation(
                violation_type=ViolationType.HARDCODED_TEST_DATA,
                severity=Severity.HIGH,
                file_path=self.file_path,
                line_number=lineno,
                message=f"{message} Los datos de test deben externalizarse en fixtures o archivos de datos.",
                code_snippet=f'"{value}"',
            )
        )
