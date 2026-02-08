"""
Clasificador de archivos de test: API vs UI + detección de framework.

Determina si un archivo de test es de tipo API, UI o desconocido
usando heurísticas basadas en imports, patrones de código (regex)
y patrones de ruta del archivo.

También detecta el framework UI usado (Selenium, Playwright) para
ajustar automáticamente las reglas aplicables. Por ejemplo, Playwright
tiene auto-wait nativo, así que MISSING_WAIT_STRATEGY no aplica.

Diseño agnóstico al lenguaje: soporta Python, Java, JavaScript/TypeScript y C#
usando ParseResult unificado.

Fase 7: Reduce falsos positivos en proyectos mixtos (API + front-end).
Fase 9+: Soporte multi-lenguaje con ParseResult unificado.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, List, Optional, Union

from gtaa_validator.parsers.treesitter_base import ParseResult, ParsedImport


# --- Frameworks con auto-wait nativo (no necesitan MISSING_WAIT_STRATEGY) ---
AUTO_WAIT_FRAMEWORKS: Set[str] = {"playwright"}


@dataclass
class ClassificationResult:
    """Resultado de la clasificación de un archivo."""
    file_type: str  # 'api', 'ui', 'bdd_step', 'page_object' o 'unknown'
    frameworks: Set[str] = field(default_factory=set)  # ej. {'playwright'}, {'selenium'}
    is_bdd: bool = False  # True si es un step definition BDD
    is_test_file: bool = False  # True si es un archivo de test
    is_page_object: bool = False  # True si es un Page Object

    @property
    def has_auto_wait(self) -> bool:
        """True si algún framework detectado tiene auto-wait nativo."""
        return bool(self.frameworks & AUTO_WAIT_FRAMEWORKS)


class FileClassifier:
    """
    Clasifica archivos de test como 'api', 'ui', 'page_object' o 'unknown'.

    Estrategia de clasificación por scoring:
    - Imports API: señal fuerte positiva para API
    - Imports UI: señal fuerte positiva para UI
    - Patrones de código API (regex): señal moderada
    - Patrones de ruta: señal moderada

    Soporta múltiples lenguajes (Python, Java, JS/TS, C#) mediante
    ParseResult unificado.

    Decisión conservadora: si hay indicios UI, se clasifica como UI
    aunque también tenga indicios API. 'unknown' se trata como UI
    para no perder violaciones.
    """

    # --- Señales de imports API (módulos raíz) ---
    # Python
    API_IMPORTS_PYTHON: Set[str] = {
        "requests", "httpx", "aiohttp", "urllib",
        "fastapi", "starlette", "flask", "rest_framework",
    }
    # Java
    API_IMPORTS_JAVA: Set[str] = {
        "io.restassured", "okhttp3", "org.apache.http",
        "java.net.http", "retrofit2",
    }
    # JavaScript/TypeScript
    API_IMPORTS_JS: Set[str] = {
        "axios", "supertest", "node-fetch", "got", "ky",
        "fetch", "request",
    }
    # C#
    API_IMPORTS_CSHARP: Set[str] = {
        "RestSharp", "System.Net.Http", "Flurl",
    }

    # --- Señales de imports BDD (módulos raíz) ---
    BDD_IMPORTS_PYTHON: Set[str] = {"behave", "pytest_bdd"}
    BDD_IMPORTS_JAVA: Set[str] = {"cucumber", "io.cucumber"}
    BDD_IMPORTS_JS: Set[str] = {"cypress-cucumber-preprocessor", "@cucumber/cucumber"}
    BDD_IMPORTS_CSHARP: Set[str] = {"TechTalk.SpecFlow", "Reqnroll"}

    # --- Señales de imports UI (módulos raíz) ---
    UI_IMPORTS_PYTHON: Set[str] = {"selenium", "playwright", "webdriver"}
    UI_IMPORTS_JAVA: Set[str] = {
        "org.openqa.selenium", "com.microsoft.playwright",
        "io.appium",
    }
    UI_IMPORTS_JS: Set[str] = {
        "@playwright/test", "playwright", "cypress", "puppeteer",
        "webdriverio", "selenium-webdriver",
    }
    UI_IMPORTS_CSHARP: Set[str] = {
        "OpenQA.Selenium", "Microsoft.Playwright",
    }

    # --- Test framework imports (no deben estar en Page Objects) ---
    TEST_IMPORTS_PYTHON: Set[str] = {"pytest", "unittest"}
    TEST_IMPORTS_JAVA: Set[str] = {"org.junit", "org.testng", "org.junit.jupiter"}
    TEST_IMPORTS_JS: Set[str] = {"jest", "mocha", "jasmine", "@jest/globals"}
    TEST_IMPORTS_CSHARP: Set[str] = {"NUnit.Framework", "Xunit", "Microsoft.VisualStudio.TestTools"}

    # --- Patrones de código API (regex sobre source) ---
    API_CODE_PATTERNS = [
        re.compile(r"response\.status_code"),
        re.compile(r"\.json\(\)"),
        re.compile(r"\.(get|post|put|delete|patch)\s*\("),
        re.compile(r"status_code\s*==\s*\d{3}"),
        re.compile(r"application/json"),
        re.compile(r"statusCode\s*===?\s*\d{3}"),  # JS
    ]

    # --- Patrones de ruta que indican API test ---
    API_PATH_PATTERNS = ["/api/", "test_api_", "_api_test", "/api_"]

    # Pesos para el scoring
    IMPORT_WEIGHT = 5
    CODE_PATTERN_WEIGHT = 2
    PATH_PATTERN_WEIGHT = 3

    def classify(self, file_path: Path, source: str,
                 tree_or_result: Union[ast.Module, ParseResult, None] = None) -> str:
        """
        Clasifica un archivo de test.

        Args:
            file_path: Ruta al archivo
            source: Código fuente del archivo
            tree_or_result: AST (Python) o ParseResult (multi-lang)

        Returns:
            'api', 'ui', 'page_object' o 'unknown'
        """
        result = self.classify_detailed(file_path, source, tree_or_result)
        return result.file_type

    def classify_detailed(self, file_path: Path, source: str,
                          tree_or_result: Union[ast.Module, ParseResult, None] = None
                          ) -> ClassificationResult:
        """
        Clasifica un archivo con información detallada (tipo + frameworks).

        Args:
            file_path: Ruta al archivo
            source: Código fuente del archivo
            tree_or_result: AST (Python legacy) o ParseResult (multi-lang)

        Returns:
            ClassificationResult con file_type, frameworks detectados, etc.
        """
        # Determinar el lenguaje y obtener imports
        extension = file_path.suffix.lower()
        imports: List[ParsedImport] = []
        is_page_object = False
        has_test_methods = False

        if isinstance(tree_or_result, ParseResult):
            # Usar ParseResult unificado (recomendado)
            imports = tree_or_result.imports
            is_page_object = any(cls.is_page_object for cls in tree_or_result.classes)
            # Detectar si tiene métodos/funciones de test
            has_test_methods = self._has_test_methods(tree_or_result, extension)
        elif isinstance(tree_or_result, ast.Module):
            # Legacy: AST de Python
            imports = self._ast_to_parsed_imports(tree_or_result)
            is_page_object = self._detect_page_object_from_ast(tree_or_result)
        else:
            # Sin árbol, intentar parsear
            if extension == ".py":
                try:
                    tree = ast.parse(source)
                    imports = self._ast_to_parsed_imports(tree)
                    is_page_object = self._detect_page_object_from_ast(tree)
                except SyntaxError:
                    pass

        # Determinar conjuntos de imports según el lenguaje
        api_imports_set = self._get_api_imports_for_language(extension)
        ui_imports_set = self._get_ui_imports_for_language(extension)
        bdd_imports_set = self._get_bdd_imports_for_language(extension)
        test_imports_set = self._get_test_imports_for_language(extension)

        # Scoring
        api_score = 0
        ui_score = 0
        ui_frameworks: Set[str] = set()
        is_bdd = False
        has_test_imports = False

        # 1. Análisis de imports
        for imp in imports:
            root_module = imp.module.split(".")[0]
            full_module = imp.module

            # API imports
            if root_module in api_imports_set or full_module in api_imports_set:
                api_score += self.IMPORT_WEIGHT

            # UI imports
            for ui_imp in ui_imports_set:
                if full_module.startswith(ui_imp) or root_module == ui_imp:
                    ui_score += self.IMPORT_WEIGHT
                    # Detectar framework específico
                    if "playwright" in full_module.lower():
                        ui_frameworks.add("playwright")
                    elif "selenium" in full_module.lower():
                        ui_frameworks.add("selenium")
                    elif "cypress" in full_module.lower():
                        ui_frameworks.add("cypress")
                    break

            # BDD imports
            for bdd_imp in bdd_imports_set:
                if full_module.startswith(bdd_imp) or root_module == bdd_imp:
                    is_bdd = True
                    break

            # Test imports
            for test_imp in test_imports_set:
                if full_module.startswith(test_imp) or root_module == test_imp:
                    has_test_imports = True
                    break

        # 2. Patrones de código API (regex)
        for pattern in self.API_CODE_PATTERNS:
            if pattern.search(source):
                api_score += self.CODE_PATTERN_WEIGHT

        # 3. Patrones de ruta
        path_str = str(file_path).lower().replace("\\", "/")
        for pattern in self.API_PATH_PATTERNS:
            if pattern in path_str:
                api_score += self.PATH_PATTERN_WEIGHT

        # 4. Detectar si es Page Object por ruta
        if not is_page_object:
            is_page_object = self._is_page_object_path(file_path)

        # 5. Detectar si es archivo de test por ruta
        is_test_file = self._is_test_file_path(file_path, extension) or has_test_methods

        # 6. Decisión
        if is_page_object:
            file_type = "page_object"
        elif ui_score > 0:
            file_type = "ui"
        elif api_score > 0:
            file_type = "api"
        else:
            file_type = "unknown"

        return ClassificationResult(
            file_type=file_type,
            frameworks=ui_frameworks,
            is_bdd=is_bdd,
            is_test_file=is_test_file,
            is_page_object=is_page_object,
        )

    def _ast_to_parsed_imports(self, tree: ast.Module) -> List[ParsedImport]:
        """Convierte imports de AST Python a ParsedImport."""
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

        return imports

    def _detect_page_object_from_ast(self, tree: ast.Module) -> bool:
        """Detecta si el AST contiene una clase Page Object."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "Page" in node.name or "PageObject" in node.name:
                    return True
                # Verificar clases base
                for base in node.bases:
                    if isinstance(base, ast.Name) and "Page" in base.id:
                        return True
        return False

    def _has_test_methods(self, result: ParseResult, extension: str) -> bool:
        """Detecta si el ParseResult contiene métodos de test."""
        # Funciones de nivel superior
        for func in result.functions:
            if self._is_test_function(func.name, func.decorators, extension):
                return True

        # Métodos de clase
        for cls in result.classes:
            for method in cls.methods:
                if self._is_test_function(method.name, method.decorators, extension):
                    return True

        return False

    def _is_test_function(self, name: str, decorators: List[str], extension: str) -> bool:
        """Determina si una función es un test basado en nombre y decoradores."""
        # Python: test_*
        if extension == ".py":
            return name.startswith("test_")

        # Java: @Test
        if extension == ".java":
            test_annotations = {"Test", "ParameterizedTest", "RepeatedTest"}
            return any(d in test_annotations for d in decorators)

        # C#: [Test], [Fact], [Theory]
        if extension == ".cs":
            test_attributes = {"Test", "Fact", "Theory", "TestMethod"}
            return any(d in test_attributes for d in decorators)

        # JS/TS: describe/it/test patterns (harder to detect from decorators alone)
        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return name in {"it", "test"} or name.startswith("test")

        return False

    def _is_page_object_path(self, file_path: Path) -> bool:
        """Detecta si la ruta indica un Page Object."""
        parts_lower = [p.lower() for p in file_path.parts]
        filename = file_path.name.lower()

        in_page_dir = any(
            part in {"pages", "page_objects", "pom", "pageobjects"}
            for part in parts_lower
        )

        is_page_file = (
            filename.endswith("_page.py") or
            filename.endswith("_pom.py") or
            filename.endswith("page.java") or
            filename.endswith("page.ts") or
            filename.endswith("page.js") or
            filename.endswith("page.cs") or
            "page" in filename
        )

        # No considerar archivos de test como Page Objects
        in_test_dir = any(part in {"tests", "test", "specs", "spec"} for part in parts_lower)

        return (in_page_dir or is_page_file) and not in_test_dir

    def _is_test_file_path(self, file_path: Path, extension: str) -> bool:
        """Detecta si la ruta indica un archivo de test."""
        filename = file_path.name.lower()
        parts_lower = [p.lower() for p in file_path.parts]

        # Python
        if extension == ".py":
            return (
                filename.startswith("test_") or
                filename.endswith("_test.py") or
                any(part in ("test", "tests") for part in parts_lower)
            )

        # Java
        if extension == ".java":
            return (
                filename.endswith("test.java") or
                filename.endswith("tests.java") or
                "test" in filename
            )

        # JS/TS
        if extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return (
                ".spec." in filename or
                ".test." in filename or
                any(part in ("tests", "test", "specs", "__tests__") for part in parts_lower)
            )

        # C#
        if extension == ".cs":
            return (
                filename.endswith("tests.cs") or
                filename.endswith("test.cs") or
                "test" in filename
            )

        return False

    def _get_api_imports_for_language(self, extension: str) -> Set[str]:
        """Obtiene el conjunto de imports API para un lenguaje."""
        if extension == ".py":
            return self.API_IMPORTS_PYTHON
        elif extension == ".java":
            return self.API_IMPORTS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.API_IMPORTS_JS
        elif extension == ".cs":
            return self.API_IMPORTS_CSHARP
        return set()

    def _get_ui_imports_for_language(self, extension: str) -> Set[str]:
        """Obtiene el conjunto de imports UI para un lenguaje."""
        if extension == ".py":
            return self.UI_IMPORTS_PYTHON
        elif extension == ".java":
            return self.UI_IMPORTS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.UI_IMPORTS_JS
        elif extension == ".cs":
            return self.UI_IMPORTS_CSHARP
        return set()

    def _get_bdd_imports_for_language(self, extension: str) -> Set[str]:
        """Obtiene el conjunto de imports BDD para un lenguaje."""
        if extension == ".py":
            return self.BDD_IMPORTS_PYTHON
        elif extension == ".java":
            return self.BDD_IMPORTS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.BDD_IMPORTS_JS
        elif extension == ".cs":
            return self.BDD_IMPORTS_CSHARP
        return set()

    def _get_test_imports_for_language(self, extension: str) -> Set[str]:
        """Obtiene el conjunto de imports de test para un lenguaje."""
        if extension == ".py":
            return self.TEST_IMPORTS_PYTHON
        elif extension == ".java":
            return self.TEST_IMPORTS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
            return self.TEST_IMPORTS_JS
        elif extension == ".cs":
            return self.TEST_IMPORTS_CSHARP
        return set()

