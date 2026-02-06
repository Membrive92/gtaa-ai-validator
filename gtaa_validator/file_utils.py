"""
Utilidades de lectura segura de archivos.

Implementa limite de tamano para prevenir DoS por archivos extremadamente
grandes (SEC-05).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Limite maximo de tamano de archivo: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def read_file_safe(file_path: Path, max_size: int = MAX_FILE_SIZE_BYTES) -> str:
    """Lee un archivo con limite de tamano.

    Args:
        file_path: Ruta al archivo a leer.
        max_size: Tamano maximo en bytes (default: 10 MB).

    Returns:
        Contenido del archivo como string, o string vacio si excede el limite.
    """
    # Verificar tamano antes de leer (si el archivo existe en disco)
    try:
        size = file_path.stat().st_size
        if size > max_size:
            logger.warning(
                "Archivo omitido por tamano: %s (%d bytes > %d bytes limite)",
                file_path, size, max_size
            )
            return ""
    except OSError:
        pass  # stat() puede fallar en tests con mock_open; continuamos con la lectura

    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as e:
        logger.debug("Error leyendo archivo %s: %s", file_path, e)
        return ""
