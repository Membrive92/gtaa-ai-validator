"""
Factory para creación de clientes LLM.

Estrategia de selección (Fase 10 - TFM optimizado):
1. Si hay API key (GEMINI_API_KEY): usa Gemini
2. Si Gemini falla (rate limit, error): fallback automático a Mock
3. Si no hay API key: usa Mock directamente

Variables de entorno:
- LLM_PROVIDER: "gemini", "mock" (auto-detectado si no se especifica)
- GEMINI_API_KEY o LLM_API_KEY: API key para Gemini
- GEMINI_MODEL: modelo a usar (default: "gemini-2.5-flash-lite")

Ejemplo de uso:
    from gtaa_validator.llm.factory import create_llm_client

    # Auto-detecta: Gemini si hay API key, Mock si no
    client = create_llm_client()

    # Forzar proveedor específico
    client = create_llm_client(provider="mock")
"""

import os
from typing import Optional, Union

from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.api_client import APILLMClient


# Type alias para cualquier cliente LLM
LLMClient = Union[MockLLMClient, APILLMClient]

# Proveedores soportados
SUPPORTED_PROVIDERS = {"gemini", "mock"}


def create_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """
    Crea un cliente LLM basado en el proveedor especificado.

    Estrategia de selección (optimizada para TFM):
    1. Si se especifica provider explícitamente, usarlo
    2. Si hay LLM_PROVIDER en entorno, usarlo
    3. Auto-detectar: Gemini si hay API key, Mock si no

    Args:
        provider: Proveedor a usar ("gemini", "mock")
        api_key: API key para Gemini
        model: Modelo específico a usar

    Returns:
        Instancia del cliente LLM apropiado

    Raises:
        ValueError: Si el proveedor no está soportado
    """
    # Obtener API key del entorno si no se proporciona
    if api_key is None:
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")

    # Determinar proveedor con auto-detección
    if provider is None:
        env_provider = os.environ.get("LLM_PROVIDER", "").lower()
        if env_provider and env_provider in SUPPORTED_PROVIDERS:
            provider = env_provider
        elif api_key:
            # Auto-detectar: si hay API key, usar Gemini
            provider = "gemini"
        else:
            # Sin API key: usar Mock (heurísticas deterministas)
            provider = "mock"

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Proveedor '{provider}' no soportado. "
            f"Usa: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    # Mock client (para tests o cuando no hay LLM disponible)
    if provider == "mock":
        return MockLLMClient()

    # Gemini (cloud, requiere API key)
    if provider == "gemini":
        if not api_key:
            # Sin API key, fallback silencioso a Mock
            import sys
            print(
                "[INFO] No se encontró GEMINI_API_KEY. Usando MockLLMClient (heurísticas).",
                file=sys.stderr,
            )
            return MockLLMClient()

        gemini_model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
        try:
            return APILLMClient(api_key=api_key, model=gemini_model)
        except Exception as e:
            # Si falla la inicialización, fallback a Mock
            import sys
            print(
                f"[ADVERTENCIA] Error inicializando Gemini: {e}\n"
                f"  Usando MockLLMClient como fallback...",
                file=sys.stderr,
            )
            return MockLLMClient()

    # Fallback (no debería llegar aquí)
    return MockLLMClient()


def get_available_providers() -> dict:
    """
    Retorna información sobre proveedores disponibles.

    Returns:
        Dict con estado de cada proveedor
    """
    providers = {}

    # Mock siempre disponible
    providers["mock"] = {
        "available": True,
        "description": "Heurísticas deterministas (sin LLM real)",
    }

    # Gemini
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
    providers["gemini"] = {
        "available": bool(api_key),
        "description": "Google Gemini Flash API (cloud, requiere API key)",
        "configured": bool(api_key),
    }

    return providers
