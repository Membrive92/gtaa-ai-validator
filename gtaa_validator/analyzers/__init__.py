"""
Paquete de analizadores para gTAA Validator.

Contiene los analizadores que orquestan el proceso de detección de violaciones.
Coordinan múltiples checkers y agregan resultados en reportes.

Analizadores disponibles:
- StaticAnalyzer: Orquesta checkers de análisis estático (AST, regex, filesystem)
- SemanticAnalyzer: Análisis semántico via LLM (opcional — requiere API key)

Los analizadores implementan el Patrón Facade, proporcionando una interfaz simple
a un subsistema complejo de checkers.
"""

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer

__all__ = [
    "StaticAnalyzer",
]
