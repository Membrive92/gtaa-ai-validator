"""
Módulo de generación de reportes para gTAA Validator.

Proporciona exportación de resultados de análisis en múltiples formatos:
- JSON: Para integración programática y CI/CD
- HTML: Dashboard visual autocontenido para revisión humana
"""

from gtaa_validator.reporters.json_reporter import JsonReporter
from gtaa_validator.reporters.html_reporter import HtmlReporter

__all__ = ["JsonReporter", "HtmlReporter"]
