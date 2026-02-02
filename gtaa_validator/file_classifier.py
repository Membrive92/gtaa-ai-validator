"""
Clasificador de archivos de test: API vs UI + detección de framework.

Determina si un archivo de test es de tipo API, UI o desconocido
usando heurísticas basadas en imports (AST), patrones de código (regex)
y patrones de ruta del archivo.

También detecta el framework UI usado (Selenium, Playwright) para
ajustar automáticamente las reglas aplicables. Por ejemplo, Playwright
tiene auto-wait nativo, así que MISSING_WAIT_STRATEGY no aplica.

Diseño agnóstico al lenguaje: los patrones son extensibles para soportar
múltiples frameworks de testing (Python, JS, Java, C#).

Fase 7: Reduce falsos positivos en proyectos mixtos (API + front-end).
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set


# --- Frameworks con auto-wait nativo (no necesitan MISSING_WAIT_STRATEGY) ---
AUTO_WAIT_FRAMEWORKS: Set[str] = {"playwright"}


@dataclass
class ClassificationResult:
    """Resultado de la clasificación de un archivo."""
    file_type: str  # 'api', 'ui' o 'unknown'
    frameworks: Set[str] = field(default_factory=set)  # ej. {'playwright'}, {'selenium'}

    @property
    def has_auto_wait(self) -> bool:
        """True si algún framework detectado tiene auto-wait nativo."""
        return bool(self.frameworks & AUTO_WAIT_FRAMEWORKS)


class FileClassifier:
    """
    Clasifica archivos de test como 'api', 'ui' o 'unknown'.

    Estrategia de clasificación por scoring:
    - Imports API (AST): señal fuerte positiva para API
    - Imports UI (AST): señal fuerte positiva para UI
    - Patrones de código API (regex): señal moderada
    - Patrones de ruta: señal moderada

    Decisión conservadora: si hay indicios UI, se clasifica como UI
    aunque también tenga indicios API. 'unknown' se trata como UI
    para no perder violaciones.
    """

    # --- Señales de imports API (módulos raíz) ---
    API_IMPORTS: Set[str] = {
        # Python HTTP clients
        "requests", "httpx", "aiohttp", "urllib",
        # Framework test clients
        "fastapi", "starlette", "flask", "rest_framework",
        # JS/TS (para futuro soporte multi-lenguaje)
        # "axios", "supertest", "node-fetch",
        # Java (para futuro)
        # "io.restassured", "okhttp3",
    }

    # --- Señales de imports UI (módulos raíz) ---
    UI_IMPORTS: Set[str] = {
        "selenium", "playwright", "webdriver",
        # JS/TS (futuro)
        # "cypress", "puppeteer",
        # Java (futuro)
        # "org.openqa.selenium",
    }

    # --- Patrones de código API (regex sobre source) ---
    API_CODE_PATTERNS = [
        re.compile(r"response\.status_code"),
        re.compile(r"\.json\(\)"),
        re.compile(r"\.(get|post|put|delete|patch)\s*\("),
        re.compile(r"status_code\s*==\s*\d{3}"),
        re.compile(r"application/json"),
    ]

    # --- Patrones de ruta que indican API test ---
    API_PATH_PATTERNS = ["/api/", "test_api_", "_api_test", "/api_"]

    # Pesos para el scoring
    IMPORT_WEIGHT = 5
    CODE_PATTERN_WEIGHT = 2
    PATH_PATTERN_WEIGHT = 3

    def classify(self, file_path: Path, source: str, tree: ast.Module) -> str:
        """
        Clasifica un archivo de test.

        Args:
            file_path: Ruta al archivo
            source: Código fuente del archivo
            tree: AST pre-parseado

        Returns:
            'api', 'ui' o 'unknown'
        """
        result = self.classify_detailed(file_path, source, tree)
        return result.file_type

    def classify_detailed(self, file_path: Path, source: str,
                          tree: ast.Module) -> ClassificationResult:
        """
        Clasifica un archivo con información detallada (tipo + frameworks).

        Returns:
            ClassificationResult con file_type y frameworks detectados
        """
        api_score = 0
        ui_score = 0

        # 1. Análisis de imports via AST (más preciso que regex)
        api_imports, ui_imports = self._analyze_imports(tree)
        api_score += len(api_imports) * self.IMPORT_WEIGHT
        ui_score += len(ui_imports) * self.IMPORT_WEIGHT

        # 2. Patrones de código API (regex)
        for pattern in self.API_CODE_PATTERNS:
            if pattern.search(source):
                api_score += self.CODE_PATTERN_WEIGHT

        # 3. Patrones de ruta
        path_str = str(file_path).lower().replace("\\", "/")
        for pattern in self.API_PATH_PATTERNS:
            if pattern in path_str:
                api_score += self.PATH_PATTERN_WEIGHT

        # 4. Decisión conservadora
        if ui_score > 0:
            file_type = "ui"
        elif api_score > 0:
            file_type = "api"
        else:
            file_type = "unknown"

        return ClassificationResult(
            file_type=file_type,
            frameworks=ui_imports,  # Los UI imports son los frameworks detectados
        )

    def _analyze_imports(self, tree: ast.Module):
        """
        Extrae imports del AST y los clasifica como API o UI.

        Returns:
            Tupla (api_imports_encontrados, ui_imports_encontrados)
        """
        api_found = set()
        ui_found = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split(".")[0]
                    if root_module in self.API_IMPORTS:
                        api_found.add(root_module)
                    if root_module in self.UI_IMPORTS:
                        ui_found.add(root_module)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split(".")[0]
                    if root_module in self.API_IMPORTS:
                        api_found.add(root_module)
                    if root_module in self.UI_IMPORTS:
                        ui_found.add(root_module)

        return api_found, ui_found
