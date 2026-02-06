"""
Parser de Python usando el módulo ast estándar.

Produce ParseResult unificado para que los checkers sean agnósticos al lenguaje.
Este parser permite que los mismos checkers funcionen para Python, Java, JS y C#.

Fase 9+: Refactorización para checkers agnósticos.
"""

import ast
from pathlib import Path
from typing import List, Optional, Set

from gtaa_validator.parsers.treesitter_base import (
    ParseResult,
    ParsedImport,
    ParsedClass,
    ParsedFunction,
    ParsedCall,
    ParsedString,
)


class PythonParser:
    """
    Parser para archivos Python.

    Produce ParseResult compatible con el sistema unificado de checkers,
    permitiendo que los mismos checkers funcionen para Python y otros lenguajes.
    """

    # Decoradores de test en Python
    TEST_DECORATORS = {"pytest.fixture", "fixture"}

    # Anotaciones BDD
    BDD_DECORATORS = {"given", "when", "then", "step", "before", "after"}

    def __init__(self):
        self.language = "python"

    def parse(self, source: str) -> ParseResult:
        """
        Parsea código fuente Python y extrae información estructurada.

        Args:
            source: Código fuente como string

        Returns:
            ParseResult con imports, clases, funciones, llamadas y strings
        """
        result = ParseResult(language=self.language)

        try:
            tree = ast.parse(source)

            # Extraer información
            result.imports = self._extract_imports(tree)
            result.classes = self._extract_classes(tree, source)
            result.functions = self._extract_top_level_functions(tree, source)
            result.calls = self._extract_calls(tree, source)
            result.strings = self._extract_strings(tree)

        except SyntaxError as e:
            result.parse_errors.append(f"Error de sintaxis: {str(e)}")
        except Exception as e:
            result.parse_errors.append(f"Error de parsing: {str(e)}")

        return result

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parsea un archivo Python y extrae información estructurada.

        Args:
            file_path: Ruta al archivo

        Returns:
            ParseResult con información extraída
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            return self.parse(source)
        except Exception as e:
            result = ParseResult(language=self.language)
            result.parse_errors.append(f"Error leyendo archivo: {str(e)}")
            return result

    def _extract_imports(self, tree: ast.Module) -> List[ParsedImport]:
        """Extrae imports del AST Python."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ParsedImport(
                        module=alias.name,
                        line=node.lineno,
                        alias=alias.asname,
                    ))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(ParsedImport(
                        module=node.module,
                        line=node.lineno,
                    ))
                    # También añadir los nombres importados para detección más precisa
                    for alias in node.names:
                        full_name = f"{node.module}.{alias.name}"
                        imports.append(ParsedImport(
                            module=full_name,
                            line=node.lineno,
                            alias=alias.asname,
                        ))

        return imports

    def _extract_classes(self, tree: ast.Module, source: str) -> List[ParsedClass]:
        """Extrae clases y sus métodos del AST Python."""
        classes = []
        lines = source.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                parsed_class = self._parse_class(node, lines)
                classes.append(parsed_class)

        return classes

    def _parse_class(self, node: ast.ClassDef, lines: List[str]) -> ParsedClass:
        """Parsea una definición de clase Python."""
        # Obtener clases base
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(self._get_attribute_name(base))

        # Detectar si es un Page Object
        is_page_object = (
            "Page" in node.name or
            "PageObject" in node.name or
            any("Page" in bc for bc in base_classes)
        )

        # Extraer métodos
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                method = self._parse_function(item, lines)
                methods.append(method)

        return ParsedClass(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            methods=methods,
            base_classes=base_classes,
            is_page_object=is_page_object,
        )

    def _extract_top_level_functions(self, tree: ast.Module, source: str) -> List[ParsedFunction]:
        """Extrae funciones de nivel superior (no métodos de clase)."""
        functions = []
        lines = source.splitlines()

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func = self._parse_function(node, lines)
                functions.append(func)

        return functions

    def _parse_function(self, node, lines: List[str]) -> ParsedFunction:
        """Parsea una definición de función Python."""
        # Obtener decoradores
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(self._get_attribute_name(decorator))
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    decorators.append(self._get_attribute_name(decorator.func))

        # Obtener parámetros
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)

        is_async = isinstance(node, ast.AsyncFunctionDef)

        return ParsedFunction(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            decorators=decorators,
            parameters=parameters,
            is_async=is_async,
        )

    def _extract_calls(self, tree: ast.Module, source: str) -> List[ParsedCall]:
        """Extrae llamadas a métodos del AST Python."""
        calls = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call = self._parse_call(node, source)
                if call:
                    calls.append(call)

        return calls

    def _parse_call(self, node: ast.Call, source: str) -> Optional[ParsedCall]:
        """Parsea una llamada a función/método Python."""
        object_name = ""
        method_name = ""
        full_text = ""

        try:
            full_text = ast.unparse(node)
        except AttributeError:
            pass

        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            object_name = self._get_root_object(node.func.value)
        elif isinstance(node.func, ast.Name):
            method_name = node.func.id

        if method_name:
            return ParsedCall(
                object_name=object_name,
                method_name=method_name,
                line=node.lineno,
                full_text=full_text,
            )

        return None

    def _extract_strings(self, tree: ast.Module) -> List[ParsedString]:
        """Extrae strings literales del AST Python."""
        strings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(ParsedString(
                    value=node.value,
                    line=node.lineno,
                ))

        return strings

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Obtiene el nombre completo de un atributo (ej: 'module.Class')."""
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        return ".".join(reversed(parts))

    def _get_root_object(self, node) -> str:
        """Obtiene el nombre del objeto raíz de una cadena de atributos."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Para self.driver, retorna 'driver'
            # Para driver.method, retorna 'driver'
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                return node.attr
            return self._get_root_object(node.value)
        elif isinstance(node, ast.Call):
            # Para método().otro(), obtener el objeto del método
            return self._get_root_object(node.func)
        return ""

    # --- Utilidades específicas de Python ---

    def is_test_function(self, func: ParsedFunction) -> bool:
        """Verifica si una función es un test (test_*)."""
        return func.name.startswith("test_")

    def is_fixture(self, func: ParsedFunction) -> bool:
        """Verifica si una función es un fixture de pytest."""
        return any(d in ("fixture", "pytest.fixture") for d in func.decorators)

    def is_bdd_step(self, func: ParsedFunction) -> bool:
        """Verifica si una función es un step de BDD."""
        return any(d.lower() in self.BDD_DECORATORS for d in func.decorators)

    def has_selenium_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de Selenium."""
        return any("selenium" in imp.module.lower() for imp in imports)

    def has_playwright_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de Playwright."""
        return any("playwright" in imp.module.lower() for imp in imports)

    def has_test_framework_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de frameworks de test (pytest, unittest)."""
        test_modules = {"pytest", "unittest"}
        return any(
            any(imp.module.startswith(mod) for mod in test_modules)
            for imp in imports
        )


def get_python_parser() -> PythonParser:
    """Factory function para obtener el parser de Python."""
    return PythonParser()
