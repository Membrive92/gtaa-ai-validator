"""
Configuración centralizada de logging para gTAA Validator.

Proporciona una función setup_logging() que configura el sistema de logging
de Python con handlers para consola (stderr) y opcionalmente fichero.

Uso:
    from gtaa_validator.logging_config import setup_logging
    setup_logging(verbose=True, log_file="analysis.log")
"""

import logging
import sys
from pathlib import Path


def setup_logging(verbose: bool = False, log_file: str = None) -> None:
    """
    Configura el sistema de logging para gTAA Validator.

    Args:
        verbose: Si True, muestra mensajes DEBUG en consola. Si False, solo WARNING+.
        log_file: Ruta opcional a fichero de log (siempre nivel DEBUG).
    """
    logger = logging.getLogger("gtaa_validator")

    # Evitar duplicación de handlers si se llama múltiples veces
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    # Handler de consola (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)
    console_format = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Handler de fichero (opcional, siempre DEBUG)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
