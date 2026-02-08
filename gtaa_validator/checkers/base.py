"""
Clase base para todos los checkers de violaciones gTAA.

Este módulo define la clase base abstracta de la que deben heredar todos los checkers.
Implementa el Patrón Strategy, permitiendo al analizador ejecutar diferentes
estrategias de verificación sin conocer los detalles de implementación.

Conceptos clave:
- Clase Base Abstracta (ABC): Obliga a las subclases a implementar los métodos requeridos
- Patrón Strategy: Encapsula diferentes algoritmos (checkers) tras una interfaz común
- Template Method: Define el esqueleto de check() que las subclases implementan
"""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from gtaa_validator.models import Violation

if TYPE_CHECKING:
    from gtaa_validator.parsers.treesitter_base import ParseResult, ParsedFunction


class BaseChecker(ABC):
    """
    Clase base abstracta para todos los checkers de violaciones gTAA.

    Todos los checkers deben heredar de esta clase e implementar el método check().
    El método check() recibe una ruta de archivo y devuelve una lista de violaciones encontradas.

    Subclases:
    - DefinitionChecker: Verifica archivos de test en busca de violaciones
    - StructureChecker: Valida la estructura del proyecto
    - AdaptationChecker: Valida Page Objects
    - QualityChecker: Verificaciones generales de calidad de código
    - BDDChecker: Verifica archivos BDD/Gherkin

    Uso:
        class MiChecker(BaseChecker):
            def check(self, file_path: Path) -> List[Violation]:
                # Implementación aquí
                return violations
    """

    def __init__(self):
        """Inicializar el checker."""
        self.name = self.__class__.__name__

    @abstractmethod
    def check(self, file_path: Path,
              tree: Optional[Union[ast.Module, ParseResult]] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo en busca de violaciones gTAA.

        Este es el método principal que deben implementar todas las subclases.
        Analiza un único archivo y devuelve una lista de violaciones encontradas.

        Args:
            file_path: Ruta al archivo a verificar
            tree: Árbol AST pre-parseado o ParseResult multi-lenguaje (opcional).
                  Si se proporciona, el checker debe usarlo en lugar de parsear
                  el archivo de nuevo.
            file_type: Clasificación del archivo ('api', 'ui' o 'unknown').
                  Los checkers pueden usar esto para saltar reglas no aplicables.

        Returns:
            Lista de objetos Violation encontrados en el archivo (lista vacía si no hay violaciones)

        Raises:
            NotImplementedError: Si la subclase no implementa este método
        """
        pass

    def check_project(self, project_path: Path) -> List[Violation]:
        """
        Verificar violaciones a nivel de proyecto (ej. estructura de directorios ausente).

        Sobrescribir este método para checkers que analizan el proyecto completo
        en lugar de archivos individuales. Por defecto devuelve lista vacía.

        Args:
            project_path: Directorio raíz del proyecto

        Returns:
            Lista de objetos Violation (vacía por defecto)
        """
        return []

    def can_check(self, file_path: Path) -> bool:
        """
        Determinar si este checker puede analizar el archivo dado.

        Sobrescribir este método si el checker solo debe ejecutarse sobre ciertos tipos de archivo.
        La implementación por defecto devuelve True para todos los archivos Python.

        Args:
            file_path: Ruta al archivo a verificar

        Returns:
            True si este checker puede analizar el archivo, False en caso contrario

        Ejemplo:
            def can_check(self, file_path: Path) -> bool:
                # Solo verificar archivos en el directorio tests/
                return "tests" in file_path.parts
        """
        return file_path.suffix == ".py"

    # Extensiones JS/TS compartidas por todos los checkers
    _JS_EXTENSIONS = frozenset({".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"})

    # Extensiones soportadas por el análisis multilenguaje
    _SUPPORTED_EXTENSIONS = frozenset(
        {".py", ".java", ".cs"} | {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}
    )

    def _is_test_file(self, file_path: Path) -> bool:
        """Determina si un archivo es un archivo de test (multilenguaje).

        Lógica compartida por DefinitionChecker y QualityChecker.
        """
        extension = file_path.suffix.lower()
        if extension not in self._SUPPORTED_EXTENSIONS:
            return False

        filename = file_path.name.lower()
        parts_lower = [p.lower() for p in file_path.parts]

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
        if extension in self._JS_EXTENSIONS:
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

    def _is_test_function(self, func: ParsedFunction, extension: str) -> bool:
        """Determina si una función/método es un test (multilenguaje)."""
        if extension == ".py":
            return func.name.startswith("test_")
        if extension == ".java":
            test_annotations = {"Test", "ParameterizedTest", "RepeatedTest"}
            return any(d in test_annotations for d in func.decorators)
        if extension == ".cs":
            test_attributes = {"Test", "Fact", "Theory", "TestMethod"}
            return any(d in test_attributes for d in func.decorators)
        if extension in self._JS_EXTENSIONS:
            return func.name in {"it", "test"} or func.name.startswith("test")
        return False

    @staticmethod
    def _get_config_for_extension(extension: str, config_map: dict):
        """Dispatch genérico de extensión a configuración por lenguaje.

        Args:
            extension: Extensión del archivo (ej: ".py", ".java")
            config_map: Dict con claves "py", "java", "js", "cs" y opcionalmente "default"

        Returns:
            El valor correspondiente al lenguaje, o config_map["default"] si existe, o set().
        """
        ext = extension.lstrip(".")
        if ext in ("js", "ts", "jsx", "tsx", "mjs", "cjs"):
            ext = "js"
        return config_map.get(ext, config_map.get("default", set()))

    def __repr__(self) -> str:
        """Representación en cadena del checker."""
        return f"<{self.name}>"

    def __str__(self) -> str:
        """Representación legible del checker."""
        return self.name
