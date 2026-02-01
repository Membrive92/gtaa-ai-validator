"""
Paquete LLM para análisis semántico con inteligencia artificial.

Proporciona un cliente mock con heurísticas deterministas (sin API)
y un cliente real usando Gemini Flash API.
"""

from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.gemini_client import GeminiLLMClient

__all__ = ["MockLLMClient", "GeminiLLMClient"]
