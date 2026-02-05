"""
Paquete LLM para análisis semántico con inteligencia artificial.

Proveedores soportados:
- MockLLMClient: Heurísticas deterministas (sin LLM real, para tests/fallback)
- APILLMClient: APIs cloud (Gemini Flash, requiere API key)

Factory:
- create_llm_client(): Crea cliente según configuración (auto-detecta)
- get_available_providers(): Lista proveedores disponibles
"""

from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.api_client import APILLMClient, RateLimitError
from gtaa_validator.llm.factory import create_llm_client, get_available_providers

# Alias para compatibilidad hacia atrás
GeminiLLMClient = APILLMClient

__all__ = [
    "MockLLMClient",
    "APILLMClient",
    "GeminiLLMClient",
    "RateLimitError",
    "create_llm_client",
    "get_available_providers",
]
