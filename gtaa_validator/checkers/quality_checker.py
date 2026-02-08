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

Fase 9+: Refactorizado para ser agnóstico al lenguaje usando ParseResult.
Soporta: Python, Java, JavaScript/TypeScript, C#
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Optional, Union, Set

logger = logging.getLogger(__name__)

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.file_utils import read_file_safe
from gtaa_validator.models import Violation, ViolationType, Severity
from gtaa_validator.parsers.treesitter_base import (
    ParseResult, ParsedFunction, ParsedString
)


class QualityChecker(BaseChecker):
    """
    Verifica archivos de test en busca de problemas de calidad.

    Detecta (agnóstico al lenguaje):
    - HARDCODED_TEST_DATA: emails, URLs, teléfonos, contraseñas en código de test
    - LONG_TEST_FUNCTION: funciones de test que exceden MAX_TEST_LINES
    - POOR_TEST_NAMING: nombres genéricos como test_1, test_a

    Detecta (solo Python):
    - BROAD_EXCEPTION_HANDLING: except: o except Exception:
    - HARDCODED_CONFIGURATION: localhost URLs, sleeps, paths absolutos
    - SHARED_MUTABLE_STATE: estado global mutable

    Soporta: Python, Java, JavaScript/TypeScript, C#
    """

    # Patrones regex para datos hardcodeados
    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )
    URL_PATTERN = re.compile(r"https?://[^\s\"']+")
    PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")

    # Palabras clave que sugieren una cadena de contraseña
    PASSWORD_KEYWORDS = {"password", "passwd", "pwd", "secret", "token", "apikey"}

    # Patrones de nombres genéricos de test por lenguaje
    GENERIC_NAME_PATTERNS_PYTHON = re.compile(
        r"^test_[0-9]+$|^test_[a-z]$|^test_case[0-9]*$"
    )
    GENERIC_NAME_PATTERNS_JAVA = re.compile(
        r"^test[0-9]+$|^test[A-Z]$|^testCase[0-9]*$", re.IGNORECASE
    )
    GENERIC_NAME_PATTERNS_JS = re.compile(
        r"^test\s*\d+$|^test$|^it\s*\d+$"
    )
    GENERIC_NAME_PATTERNS_CSHARP = re.compile(
        r"^Test[0-9]+$|^Test[A-Z]$|^TestCase[0-9]*$"
    )

    # Patrones de configuración hardcodeada (Python-specific)
    LOCALHOST_PATTERN = re.compile(r"https?://localhost[:\d/]|https?://127\.0\.0\.1[:\d/]")
    SLEEP_PATTERN = re.compile(r"time\.sleep\s*\(\s*\d|Thread\.sleep\s*\(\s*\d|sleep\s*\(\s*\d")
    ABSOLUTE_PATH_PATTERN = re.compile(r'["\'][A-Z]:\\|["\']/home/|["\']/usr/|["\']/tmp/')

    MAX_TEST_LINES = 50

    def can_check(self, file_path: Path) -> bool:
        """True para archivos de test en cualquier lenguaje soportado."""
        return self._is_test_file(file_path)

    def check(self, file_path: Path,
              tree_or_result: Optional[Union[ast.Module, ParseResult]] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo de test en busca de violaciones de calidad.

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

            # Verificaciones agnósticas al lenguaje
            violations.extend(self._check_hardcoded_data(file_path, result, lines, extension))
            violations.extend(self._check_long_functions(file_path, result, lines, extension))
            violations.extend(self._check_test_naming(file_path, result, lines, extension))

            # Verificaciones específicas de Python (requieren AST)
            if extension == ".py":
                try:
                    tree = ast.parse(source_code)
                    violations.extend(self._check_broad_exception_handling(file_path, tree))
                    violations.extend(self._check_hardcoded_configuration(file_path, source_code))
                    violations.extend(self._check_shared_mutable_state(file_path, tree))
                except SyntaxError:
                    pass

        except SyntaxError:
            pass
        except Exception as e:
            logger.debug("Error checking %s: %s", file_path, e)

        return violations

    # ------------------------------------------------------------------
    # Sub-verificaciones (agnósticas al lenguaje)
    # ------------------------------------------------------------------

    def _check_hardcoded_data(
        self, file_path: Path, result: ParseResult, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar datos de test hardcodeados usando ParseResult.strings."""
        violations: List[Violation] = []

        # Para JS/TS: el archivo entero es un archivo de test (ya pasó can_check)
        # Verificar todas las cadenas en el archivo
        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            for s in result.strings:
                # Ignorar cadenas muy cortas
                if len(s.value) < 5:
                    continue

                # Verificar patrones de datos hardcodeados
                violation = self._check_string_for_hardcoded_data(file_path, s, lines)
                if violation:
                    violations.append(violation)

            return violations

        # Para otros lenguajes: verificar solo strings dentro de funciones de test
        test_functions = self._get_test_functions(result, extension)
        test_ranges = [(f.line_start, f.line_end) for f in test_functions]

        for s in result.strings:
            # Verificar si el string está dentro de una función de test
            in_test = any(start <= s.line <= end for start, end in test_ranges)
            if not in_test:
                continue

            # Ignorar cadenas muy cortas
            if len(s.value) < 5:
                continue

            # Verificar patrones de datos hardcodeados
            violation = self._check_string_for_hardcoded_data(file_path, s, lines)
            if violation:
                violations.append(violation)

        return violations

    def _check_string_for_hardcoded_data(
        self, file_path: Path, s: ParsedString, lines: List[str]
    ) -> Optional[Violation]:
        """Verifica si un string contiene datos hardcodeados."""
        snippet = lines[s.line - 1].strip() if s.line <= len(lines) else f'"{s.value}"'

        if self.EMAIL_PATTERN.search(s.value):
            return Violation(
                violation_type=ViolationType.HARDCODED_TEST_DATA,
                severity=Severity.HIGH,
                file_path=file_path,
                line_number=s.line,
                message=f"Email hardcodeado encontrado: '{s.value}'. Los datos de test deben externalizarse.",
                code_snippet=snippet,
            )

        if self.URL_PATTERN.search(s.value):
            return Violation(
                violation_type=ViolationType.HARDCODED_TEST_DATA,
                severity=Severity.HIGH,
                file_path=file_path,
                line_number=s.line,
                message=f"URL hardcodeada encontrada: '{s.value}'. Los datos de test deben externalizarse.",
                code_snippet=snippet,
            )

        if self.PHONE_PATTERN.search(s.value):
            return Violation(
                violation_type=ViolationType.HARDCODED_TEST_DATA,
                severity=Severity.HIGH,
                file_path=file_path,
                line_number=s.line,
                message=f"Teléfono hardcodeado encontrado: '{s.value}'. Los datos de test deben externalizarse.",
                code_snippet=snippet,
            )

        if any(kw in s.value.lower() for kw in self.PASSWORD_KEYWORDS):
            return Violation(
                violation_type=ViolationType.HARDCODED_TEST_DATA,
                severity=Severity.HIGH,
                file_path=file_path,
                line_number=s.line,
                message="Posible contraseña/secreto hardcodeado. Los datos de test deben externalizarse.",
                code_snippet=snippet,
            )

        return None

    def _check_long_functions(
        self, file_path: Path, result: ParseResult, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar funciones de test demasiado largas."""
        violations: List[Violation] = []
        test_functions = self._get_test_functions(result, extension)

        for func in test_functions:
            length = func.line_end - func.line_start + 1
            if length > self.MAX_TEST_LINES:
                snippet = lines[func.line_start - 1].strip() if func.line_start <= len(lines) else f"def {func.name}(...)"
                violations.append(
                    Violation(
                        violation_type=ViolationType.LONG_TEST_FUNCTION,
                        severity=Severity.MEDIUM,
                        file_path=file_path,
                        line_number=func.line_start,
                        message=(
                            f"La función de test '{func.name}' tiene {length} líneas "
                            f"(límite: {self.MAX_TEST_LINES}). "
                            f"Los tests largos son difíciles de entender y mantener."
                        ),
                        code_snippet=snippet,
                    )
                )

        return violations

    def _check_test_naming(
        self, file_path: Path, result: ParseResult, lines: List[str], extension: str
    ) -> List[Violation]:
        """Detectar nombres de test genéricos."""
        violations: List[Violation] = []

        # Para JS/TS: verificar argumentos de llamadas a test(), it(), describe()
        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            for call in result.calls:
                # Verificar si es una llamada a test/it/describe
                if call.method_name not in {"test", "it", "describe"}:
                    continue

                # Buscar el string del nombre del test en la misma línea
                for s in result.strings:
                    if s.line == call.line:
                        # Verificar si el nombre es genérico
                        if self.GENERIC_NAME_PATTERNS_JS.match(s.value):
                            snippet = lines[call.line - 1].strip() if call.line <= len(lines) else call.full_text
                            violations.append(
                                Violation(
                                    violation_type=ViolationType.POOR_TEST_NAMING,
                                    severity=Severity.LOW,
                                    file_path=file_path,
                                    line_number=call.line,
                                    message=(
                                        f"El test tiene un nombre genérico '{s.value}'. "
                                        f"Use nombres descriptivos que expliquen qué se está probando."
                                    ),
                                    code_snippet=snippet,
                                )
                            )
                        break  # Solo verificar el primer string en la línea

            return violations

        # Para otros lenguajes: verificar nombres de funciones de test
        test_functions = self._get_test_functions(result, extension)
        pattern = self._get_generic_name_pattern(extension)

        for func in test_functions:
            if pattern and pattern.match(func.name):
                snippet = lines[func.line_start - 1].strip() if func.line_start <= len(lines) else func.name
                violations.append(
                    Violation(
                        violation_type=ViolationType.POOR_TEST_NAMING,
                        severity=Severity.LOW,
                        file_path=file_path,
                        line_number=func.line_start,
                        message=(
                            f"El test tiene un nombre genérico '{func.name}'. "
                            f"Use nombres descriptivos que expliquen qué se está probando."
                        ),
                        code_snippet=snippet,
                    )
                )

        return violations

    # ------------------------------------------------------------------
    # Sub-verificaciones (Python-specific)
    # ------------------------------------------------------------------

    def _check_broad_exception_handling(
        self, file_path: Path, tree: ast.Module
    ) -> List[Violation]:
        """Detectar except genérico (except: o except Exception:) en tests."""
        violations: List[Violation] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

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
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
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
                        message="sleep() hardcodeado. Usar esperas condicionales o configuración centralizada.",
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
        """Detectar estado mutable compartido a nivel de módulo (Python only)."""
        violations: List[Violation] = []

        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id.isupper() or target.id.startswith("_"):
                    continue

                val = node.value
                is_mutable = (
                    isinstance(val, ast.List) or
                    isinstance(val, ast.Dict) or
                    isinstance(val, ast.Set) or
                    (isinstance(val, ast.Call) and
                     isinstance(val.func, ast.Name) and
                     val.func.id in ("list", "dict", "set"))
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_test_functions(self, result: ParseResult, extension: str) -> List[ParsedFunction]:
        """Obtiene todas las funciones de test del ParseResult."""
        test_functions = []

        # Funciones de nivel superior
        for func in result.functions:
            if self._is_test_function(func, extension):
                test_functions.append(func)

        # Métodos de clase
        for cls in result.classes:
            for method in cls.methods:
                if self._is_test_function(method, extension):
                    test_functions.append(method)

        return test_functions

    def _get_generic_name_pattern(self, extension: str):
        """Obtiene el patrón de nombres genéricos para un lenguaje."""
        return self._get_config_for_extension(extension, {
            "py": self.GENERIC_NAME_PATTERNS_PYTHON, "java": self.GENERIC_NAME_PATTERNS_JAVA,
            "js": self.GENERIC_NAME_PATTERNS_JS, "cs": self.GENERIC_NAME_PATTERNS_CSHARP,
            "default": None,
        })
