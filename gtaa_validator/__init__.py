"""
gTAA AI Validator - Validador Automático de Cumplimiento Arquitectónico de Test Automation

Este paquete valida el cumplimiento con la Arquitectura Genérica de Test Automation (gTAA)
definida en el syllabus ISTQB CT-TAE.

El validador combina análisis estático y análisis semántico con IA para detectar
violaciones arquitectónicas en proyectos de test automation (Selenium, Playwright, etc.).

Componentes principales:
- analyzers: Analizadores estáticos y con IA
- checkers: Detección de violaciones para las diferentes capas gTAA
- reporters: Generadores de informes HTML y JSON
- models: Estructuras de datos para violaciones e informes
"""

__version__ = "0.10.4"
__author__ = "Jose Antonio Membrive Guillen"
__license__ = "MIT"
__all__ = ["__version__", "__author__", "__license__"]
