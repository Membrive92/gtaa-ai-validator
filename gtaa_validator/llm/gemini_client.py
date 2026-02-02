"""
Cliente LLM real usando Gemini Flash API.

Usa el SDK google-genai para enviar código a Gemini y obtener
análisis semántico de violaciones gTAA.
"""

import json
import re
from typing import List

from google import genai

from gtaa_validator.llm.prompts import (
    SYSTEM_PROMPT,
    ANALYZE_FILE_PROMPT,
    ENRICH_VIOLATION_PROMPT,
)


class GeminiLLMClient:
    """
    Cliente que usa Gemini Flash para análisis semántico real.

    Misma interfaz que MockLLMClient: analyze_file() y enrich_violation().
    Requiere API key de Gemini (GEMINI_API_KEY).
    """

    VALID_TYPES = {
        "UNCLEAR_TEST_PURPOSE",
        "PAGE_OBJECT_DOES_TOO_MUCH",
        "IMPLICIT_TEST_DEPENDENCY",
        "MISSING_WAIT_STRATEGY",
        "MISSING_AAA_STRUCTURE",
        "MIXED_ABSTRACTION_LEVEL",
    }

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        if not api_key:
            raise ValueError("Se requiere una API key de Gemini. Configura GEMINI_API_KEY.")
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def analyze_file(self, file_content: str, file_path: str,
                     file_type: str = "unknown",
                     has_auto_wait: bool = False) -> List[dict]:
        """Envía código a Gemini para detectar violaciones semánticas."""
        prompt = ANALYZE_FILE_PROMPT.format(
            file_path=file_path,
            file_content=file_content,
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
            return self._parse_violations(response.text)
        except Exception:
            return []

    def enrich_violation(self, violation: dict, file_content: str) -> str:
        """Envía violación a Gemini para obtener sugerencia contextual."""
        prompt = ENRICH_VIOLATION_PROMPT.format(
            violation_type=violation.get("type", ""),
            violation_message=violation.get("message", ""),
            file_path=violation.get("file", ""),
            line_number=violation.get("line", ""),
            code_snippet=violation.get("code_snippet", ""),
            file_content=file_content,
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
            text = response.text.strip()
            return text if text else ""
        except Exception:
            return ""

    def _parse_violations(self, text: str) -> List[dict]:
        """Parsea la respuesta JSON de Gemini, con fallback robusto."""
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
