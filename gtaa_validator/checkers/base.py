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

import ast
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from gtaa_validator.models import Violation


class BaseChecker(ABC):
    """
    Clase base abstracta para todos los checkers de violaciones gTAA.

    Todos los checkers deben heredar de esta clase e implementar el método check().
    El método check() recibe una ruta de archivo y devuelve una lista de violaciones encontradas.

    Subclases:
    - DefinitionChecker: Verifica archivos de test en busca de violaciones (Fase 2)
    - StructureChecker: Valida la estructura del proyecto (Fase 3)
    - AdaptationChecker: Valida Page Objects (Fase 3)
    - QualityChecker: Verificaciones generales de calidad de código (Fase 3)

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
    def check(self, file_path: Path, tree: Optional[ast.Module] = None,
              file_type: str = "unknown") -> List[Violation]:
        """
        Verificar un archivo en busca de violaciones gTAA.

        Este es el método principal que deben implementar todas las subclases.
        Analiza un único archivo y devuelve una lista de violaciones encontradas.

        Args:
            file_path: Ruta al archivo a verificar
            tree: Árbol AST pre-parseado (opcional). Si se proporciona, el checker
                  debe usarlo en lugar de parsear el archivo de nuevo.
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

    def __repr__(self) -> str:
        """Representación en cadena del checker."""
        return f"<{self.name}>"

    def __str__(self) -> str:
        """Representación legible del checker."""
        return self.name
