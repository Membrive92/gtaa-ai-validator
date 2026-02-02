"""
Configuración por proyecto para gTAA Validator.

Carga un archivo .gtaa.yaml del directorio raíz del proyecto analizado
para personalizar reglas, excluir checks y definir patrones de API tests.

Si el archivo no existe, se usan valores por defecto (sin restricciones).
Si PyYAML no está instalado o el YAML es inválido, se degrada elegantemente.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ProjectConfig:
    """
    Configuración de un proyecto de test automation.

    Attributes:
        exclude_checks: Tipos de violación a ignorar globalmente
        ignore_paths: Patrones glob de archivos a excluir del análisis
        api_test_patterns: Patrones glob para forzar clasificación API
    """
    exclude_checks: List[str] = field(default_factory=list)
    ignore_paths: List[str] = field(default_factory=list)
    api_test_patterns: List[str] = field(default_factory=list)


def load_config(project_path: Path) -> ProjectConfig:
    """
    Carga .gtaa.yaml del directorio raíz del proyecto.

    Si el archivo no existe o PyYAML no está instalado,
    devuelve un ProjectConfig con valores por defecto.

    Args:
        project_path: Directorio raíz del proyecto analizado

    Returns:
        ProjectConfig con la configuración cargada o defaults
    """
    config_path = project_path / ".gtaa.yaml"
    if not config_path.exists():
        return ProjectConfig()

    try:
        import yaml
    except ImportError:
        return ProjectConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return ProjectConfig()

    if not isinstance(data, dict):
        return ProjectConfig()

    return ProjectConfig(
        exclude_checks=data.get("exclude_checks", []) or [],
        ignore_paths=data.get("ignore_paths", []) or [],
        api_test_patterns=data.get("api_test_patterns", []) or [],
    )
