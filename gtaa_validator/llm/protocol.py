"""
Protocolo e interfaz compartida para clientes LLM.

Define TokenUsage unificado y LLMClientProtocol que todos los clientes
deben implementar (Protocol de typing para duck typing estructural).
"""

from dataclasses import dataclass
from typing import List, Protocol, runtime_checkable


@dataclass
class TokenUsage:
    """Tracking unificado de consumo de tokens LLM.

    Tanto MockLLMClient como APILLMClient usan esta clase.
    Los precios por millón de tokens se configuran en el constructor
    (0.0 para mock, valores reales para API).
    """
    input_tokens: int = 0
    output_tokens: int = 0
    total_calls: int = 0
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0

    def add(self, input_tokens: int, output_tokens: int):
        """Añade tokens de una llamada."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_calls += 1

    @property
    def total_tokens(self) -> int:
        """Total de tokens consumidos."""
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Costo estimado en USD."""
        input_cost = (self.input_tokens / 1_000_000) * self.cost_per_million_input
        output_cost = (self.output_tokens / 1_000_000) * self.cost_per_million_output
        return input_cost + output_cost

    def to_dict(self) -> dict:
        """Convierte a diccionario para reportes."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "total_calls": self.total_calls,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
        }

    def __str__(self) -> str:
        if self.cost_per_million_input == 0.0 and self.cost_per_million_output == 0.0:
            return f"Mock: {self.total_calls} llamadas (sin costo)"
        return (
            f"Tokens: {self.total_tokens:,} "
            f"(input: {self.input_tokens:,}, output: {self.output_tokens:,}) | "
            f"Llamadas: {self.total_calls} | "
            f"Costo estimado: ${self.estimated_cost_usd:.4f} USD"
        )


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Protocolo que define la interfaz de un cliente LLM.

    Tanto MockLLMClient como APILLMClient implementan esta interfaz.
    Usar este protocolo para type hints en lugar de Union[Mock, API].
    """
    usage: TokenUsage

    def analyze_file(
        self, file_content: str, file_path: str,
        file_type: str = "unknown", has_auto_wait: bool = False
    ) -> List[dict]: ...

    def enrich_violation(self, violation: dict, file_content: str) -> str: ...

    def get_usage_summary(self) -> str: ...

    def get_usage_dict(self) -> dict: ...
