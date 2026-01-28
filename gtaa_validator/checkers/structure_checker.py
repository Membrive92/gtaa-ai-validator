"""
Checker de Estructura para gTAA Validator.

Valida que el proyecto tenga la estructura de capas gTAA correcta:
- Directorio de tests (tests/ o test/)
- Directorio de Page Objects (pages/, page_objects/ o pom/)

Este es un checker a NIVEL DE PROYECTO — se ejecuta una vez vía check_project(),
no por archivo vía check().

Según la arquitectura gTAA, los proyectos deben tener directorios separados
para la capa de Definición (tests) y la capa de Adaptación (Page Objects).
"""

import ast
from pathlib import Path
from typing import List, Optional

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class StructureChecker(BaseChecker):
    """
    Verifica la estructura del proyecto en busca de directorios gTAA requeridos.

    Este checker valida que el proyecto tenga al menos:
    - Un directorio de tests (tests/ o test/)
    - Un directorio de page objects (pages/, page_objects/ o pom/)

    Si falta alguno, reporta una violación MISSING_LAYER_STRUCTURE.
    """

    # Nombres de directorio aceptables para cada capa
    TEST_DIR_NAMES = {"tests", "test"}
    PAGE_DIR_NAMES = {"pages", "page_objects", "pom"}

    def can_check(self, file_path: Path) -> bool:
        """StructureChecker nunca se ejecuta sobre archivos individuales."""
        return False

    def check(self, file_path: Path, tree: Optional[ast.Module] = None) -> List[Violation]:
        """No se usa — StructureChecker solo implementa check_project()."""
        return []

    def check_project(self, project_path: Path) -> List[Violation]:
        """
        Verificar si el proyecto tiene la estructura de directorios gTAA requerida.

        Busca subdirectorios inmediatos que coincidan con los nombres de capa esperados.
        Crea una única violación listando todas las capas ausentes.

        Args:
            project_path: Directorio raíz del proyecto

        Returns:
            Lista con 0 o 1 violación
        """
        try:
            subdirs = {d.name.lower() for d in project_path.iterdir() if d.is_dir()}
        except OSError:
            return []

        has_test_dir = bool(subdirs & self.TEST_DIR_NAMES)
        has_page_dir = bool(subdirs & self.PAGE_DIR_NAMES)

        if has_test_dir and has_page_dir:
            return []

        missing = []
        if not has_test_dir:
            missing.append(
                f"directorio de tests (se esperaba uno de: {', '.join(sorted(self.TEST_DIR_NAMES))})"
            )
        if not has_page_dir:
            missing.append(
                f"directorio de page objects (se esperaba uno de: {', '.join(sorted(self.PAGE_DIR_NAMES))})"
            )

        violation = Violation(
            violation_type=ViolationType.MISSING_LAYER_STRUCTURE,
            severity=Severity.CRITICAL,
            file_path=project_path,
            line_number=None,
            message=(
                f"El proyecto carece de la estructura de directorios gTAA requerida. "
                f"Falta: {'; '.join(missing)}. "
                f"Según gTAA, los proyectos deben tener directorios separados "
                f"para la capa de Definición (tests) y la capa de Adaptación (Page Objects)."
            ),
            recommendation=ViolationType.MISSING_LAYER_STRUCTURE.get_recommendation(),
        )
        return [violation]
