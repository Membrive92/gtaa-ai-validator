"""
Cliente LLM para análisis semántico usando APIs de modelos de lenguaje.

Actualmente usa el SDK google-genai para Gemini, pero el nombre genérico
permite cambiar de proveedor sin modificar el código que consume este cliente.

Incluye tracking de consumo de tokens para monitoreo de costos.
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

from google import genai


class RateLimitError(Exception):
    """Error cuando se alcanza el límite de rate/cuota de la API."""
    pass

from gtaa_validator.llm.prompts import (
    SYSTEM_PROMPT,
    ANALYZE_FILE_PROMPT,
    ENRICH_VIOLATION_PROMPT,
    extract_context_snippet,
    extract_functions_from_code,
)


@dataclass
class TokenUsage:
    """Tracking de consumo de tokens del LLM."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_calls: int = 0

    # Pricing Gemini 2.5 Flash Lite (USD por 1M tokens)
    INPUT_PRICE_PER_MILLION: float = 0.075
    OUTPUT_PRICE_PER_MILLION: float = 0.30

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
        input_cost = (self.input_tokens / 1_000_000) * self.INPUT_PRICE_PER_MILLION
        output_cost = (self.output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_MILLION
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
        return (
            f"Tokens: {self.total_tokens:,} "
            f"(input: {self.input_tokens:,}, output: {self.output_tokens:,}) | "
            f"Llamadas: {self.total_calls} | "
            f"Costo estimado: ${self.estimated_cost_usd:.4f} USD"
        )


class APILLMClient:
    """
    Cliente que usa una API LLM para análisis semántico real.

    Misma interfaz que MockLLMClient: analyze_file() y enrich_violation().
    Requiere API key (LLM_API_KEY o GEMINI_API_KEY en .env).

    Incluye tracking de tokens para monitoreo de consumo y costos.
    Accede a usage para ver el consumo acumulado.

    Actualmente implementado con Gemini Flash API, pero el nombre genérico
    permite cambiar de proveedor en el futuro sin afectar consumidores.
    """

    VALID_TYPES = {
        "UNCLEAR_TEST_PURPOSE",
        "PAGE_OBJECT_DOES_TOO_MUCH",
        "IMPLICIT_TEST_DEPENDENCY",
        "MISSING_WAIT_STRATEGY",
        "MISSING_AAA_STRUCTURE",
        "MIXED_ABSTRACTION_LEVEL",
        # BDD (Fase 8)
        "STEP_DEF_DIRECT_BROWSER_CALL",
        "STEP_DEF_TOO_COMPLEX",
    }

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        if not api_key:
            raise ValueError("Se requiere una API key. Configura LLM_API_KEY o GEMINI_API_KEY.")
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.usage = TokenUsage()  # Tracking de consumo

    def analyze_file(self, file_content: str, file_path: str,
                     file_type: str = "unknown",
                     has_auto_wait: bool = False) -> List[dict]:
        """Envía código al LLM para detectar violaciones semánticas."""
        # Optimización: reducir archivos grandes
        optimized_content = extract_functions_from_code(file_content)

        prompt = ANALYZE_FILE_PROMPT.format(
            file_path=file_path,
            file_content=optimized_content,
            file_type=file_type,
            has_auto_wait="sí" if has_auto_wait else "no",
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )
            # Registrar consumo de tokens
            self._track_usage(response)
            return self._parse_violations(response.text)
        except Exception as e:
            # Detectar errores de rate limit (429)
            if self._is_rate_limit_error(e):
                raise RateLimitError(f"Rate limit alcanzado: {e}") from e
            return []

    def enrich_violation(self, violation: dict, file_content: str) -> str:
        """Envía violación al LLM para obtener sugerencia contextual."""
        # Optimización: solo enviar contexto relevante en lugar del archivo completo
        line_number = violation.get("line")
        context_snippet = extract_context_snippet(file_content, line_number)

        prompt = ENRICH_VIOLATION_PROMPT.format(
            violation_type=violation.get("type", ""),
            violation_message=violation.get("message", ""),
            file_path=violation.get("file", ""),
            line_number=line_number or "",
            code_snippet=violation.get("code_snippet", ""),
            context_snippet=context_snippet,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                ),
            )
            # Registrar consumo de tokens
            self._track_usage(response)
            text = response.text.strip()
            return text if text else ""
        except Exception as e:
            # Detectar errores de rate limit (429)
            if self._is_rate_limit_error(e):
                raise RateLimitError(f"Rate limit alcanzado: {e}") from e
            return ""

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Detecta si el error es un rate limit (429) o quota exceeded."""
        error_str = str(error).lower()
        return (
            "429" in error_str
            or "rate limit" in error_str
            or "quota" in error_str
            or "resource exhausted" in error_str
        )

    def _track_usage(self, response) -> None:
        """Extrae y registra el consumo de tokens de una respuesta."""
        try:
            # El SDK google-genai incluye usage_metadata en la respuesta
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                metadata = response.usage_metadata
                input_tokens = getattr(metadata, 'prompt_token_count', 0) or 0
                output_tokens = getattr(metadata, 'candidates_token_count', 0) or 0
                self.usage.add(input_tokens, output_tokens)
        except Exception:
            # Si falla el tracking, no interrumpir la ejecución
            pass

    def get_usage_summary(self) -> str:
        """Retorna un resumen del consumo de tokens."""
        return str(self.usage)

    def get_usage_dict(self) -> dict:
        """Retorna el consumo como diccionario (para JSON reports)."""
        return self.usage.to_dict()

    def reset_usage(self) -> None:
        """Reinicia los contadores de uso."""
        self.usage = TokenUsage()

    def _parse_violations(self, text: str) -> List[dict]:
        """Parsea la respuesta JSON del LLM, con fallback robusto."""
        if not text:
            return []

        # Extraer JSON del texto (puede venir envuelto en ```json ... ```)
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if not json_match:
            return []

        try:
            data = json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            return []

        if not isinstance(data, list):
            return []

        violations = []
        for item in data:
            if not isinstance(item, dict):
                continue
            vtype = item.get("type", "")
            if vtype not in self.VALID_TYPES:
                continue
            violations.append({
                "type": vtype,
                "line": item.get("line"),
                "message": item.get("message", ""),
                "code_snippet": item.get("code_snippet", ""),
            })

        return violations


# Alias para compatibilidad hacia atrás (deprecado, usar APILLMClient)
GeminiLLMClient = APILLMClient
