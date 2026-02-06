"""
Analizador Semántico para gTAA Validator (Fase 5).

Complementa el análisis estático con detección semántica via LLM.
Funciones principales:
1. Detectar nuevas violaciones semánticas que AST no puede captar
2. Enriquecer violaciones estáticas existentes con sugerencias AI

El SemanticAnalyzer recibe un Report ya generado por StaticAnalyzer
y lo enriquece con análisis semántico.

Optimizaciones Fase 10:
- Análisis selectivo: solo analiza archivos con violaciones estáticas o patrones sospechosos
- Prompts optimizados: ~40% menos tokens
- Context snippets: solo envía código relevante, no archivos completos
- Fallback automático a MockLLMClient si Gemini da error 429
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Set, Union

from gtaa_validator.models import Report, Violation, ViolationType, Severity

logger = logging.getLogger(__name__)
from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.api_client import APILLMClient, RateLimitError
from gtaa_validator.file_classifier import FileClassifier


# Directorios excluidos del análisis (mismos que StaticAnalyzer)
EXCLUDED_DIRS = {
    "venv", "env", ".venv", ".env", ".git", "__pycache__",
    "node_modules", ".pytest_cache", "build", "dist",
}

# Patrones sospechosos que ameritan análisis semántico
SUSPICIOUS_PATTERNS = [
    r'def\s+test\d+',  # test1, test2, etc. - nombres pobres
    r'def\s+test_?\w{0,3}\(',  # test_x, test_a - muy cortos
    r'class\s+\w+Page.*:',  # Page Objects - revisar responsabilidades
    r'@(given|when|then)',  # Step definitions BDD
    r'time\.sleep\(',  # Sleeps explícitos - posible wait issue
    r'global\s+\w+',  # Variables globales - posible dependencia implícita
]


class SemanticAnalyzer:
    """
    Analizador semántico que usa un cliente LLM para detectar y enriquecer violaciones.

    Acepta MockLLMClient (heurísticas) o APILLMClient (API real).
    Si APILLMClient falla con error 429 (rate limit), hace fallback automático a Mock.

    Uso:
        client = MockLLMClient()  # o APILLMClient(api_key)
        semantic = SemanticAnalyzer(project_path, client)
        enriched_report = semantic.analyze(static_report)
    """

    def __init__(
        self,
        project_path: Path,
        llm_client: Union[MockLLMClient, APILLMClient],
        verbose: bool = False,
        max_llm_calls: int = None,
    ):
        self.project_path = project_path
        self.llm_client = llm_client
        self.verbose = verbose
        self.classifier = FileClassifier()
        self.max_llm_calls = max_llm_calls

        # Tracking de proveedor usado
        self._initial_provider = self._get_provider_name(llm_client)
        self._current_provider = self._initial_provider
        self._fallback_occurred = False
        self._llm_call_count = 0

    def _get_provider_name(self, client) -> str:
        """Obtiene el nombre del proveedor desde el cliente."""
        if isinstance(client, MockLLMClient):
            return "mock"
        elif isinstance(client, APILLMClient):
            return "gemini"
        return "unknown"

    def _fallback_to_mock(self, reason: str) -> None:
        """Cambia a MockLLMClient como fallback."""
        if self._fallback_occurred:
            return  # Ya se hizo fallback

        self._fallback_occurred = True
        self._current_provider = "mock"
        self.llm_client = MockLLMClient()

        logger.warning("[FALLBACK] %s", reason)
        logger.warning("[FALLBACK] Continuando con MockLLMClient (heuristicas)...")

    def _check_call_limit(self) -> None:
        """Verifica si se alcanzó el límite de llamadas y hace fallback si es necesario."""
        if self.max_llm_calls is None:
            return  # Sin límite
        if self._fallback_occurred:
            return  # Ya en fallback

        self._llm_call_count += 1
        if self._llm_call_count > self.max_llm_calls:
            self._fallback_to_mock(
                f"Limite de {self.max_llm_calls} llamadas LLM alcanzado"
            )

    def get_provider_info(self) -> dict:
        """
        Retorna información sobre el proveedor LLM usado.

        Returns:
            Dict con información del proveedor:
            - initial_provider: proveedor configurado inicialmente
            - current_provider: proveedor usado actualmente
            - fallback_occurred: si hubo cambio a Mock por error
            - llm_calls: número de llamadas realizadas al LLM inicial
        """
        info = {
            "initial_provider": self._initial_provider,
            "current_provider": self._current_provider,
            "fallback_occurred": self._fallback_occurred,
        }
        # Añadir conteo de llamadas si hubo límite
        if self.max_llm_calls is not None:
            info["llm_calls"] = min(self._llm_call_count, self.max_llm_calls)
            info["max_llm_calls"] = self.max_llm_calls
        return info

    def analyze(self, report: Report) -> Report:
        """
        Enriquece un Report existente con análisis semántico.

        Optimización Fase 10: Análisis selectivo
        - Solo analiza archivos con violaciones estáticas previas
        - O archivos con patrones sospechosos que el análisis estático no cubre

        1. Identifica archivos candidatos (con violaciones o sospechosos)
        2. Para cada candidato: detecta violaciones semánticas
        3. Para cada violación existente: genera sugerencia AI
        4. Recalcula el score

        Returns:
            El mismo Report, modificado con violaciones semánticas y sugerencias AI.
        """
        # Obtener archivos con violaciones estáticas
        files_with_violations = self._get_files_with_violations(report)

        # Descubrir archivos Python y filtrar candidatos
        all_python_files = self._discover_python_files()
        candidate_files = self._filter_candidate_files(all_python_files, files_with_violations)

        logger.info("[Semantic] Archivos candidatos: %d/%d",
                    len(candidate_files), len(all_python_files))
        logger.info("[Semantic] Proveedor: %s", self._current_provider)

        # Fase 1: Detectar nuevas violaciones semánticas (solo en candidatos)
        for file_path in candidate_files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Clasificar archivo para contextualizar el análisis LLM
            file_type = "unknown"
            has_auto_wait = False
            try:
                tree = ast.parse(content, filename=str(file_path))
                classification = self.classifier.classify_detailed(file_path, content, tree)
                file_type = classification.file_type
                has_auto_wait = classification.has_auto_wait
            except SyntaxError:
                pass

            file_str = str(file_path)

            # Verificar límite de llamadas antes de llamar al LLM
            self._check_call_limit()

            # Intentar análisis con fallback en caso de rate limit
            try:
                raw_violations = self.llm_client.analyze_file(
                    content, file_str, file_type=file_type, has_auto_wait=has_auto_wait
                )
            except RateLimitError as e:
                self._fallback_to_mock(str(e))
                raw_violations = self.llm_client.analyze_file(
                    content, file_str, file_type=file_type, has_auto_wait=has_auto_wait
                )

            for raw in raw_violations:
                vtype_name = raw.get("type", "")
                try:
                    vtype = ViolationType(vtype_name)
                except ValueError:
                    continue

                violation = Violation(
                    violation_type=vtype,
                    severity=vtype.get_severity(),
                    file_path=file_path,
                    line_number=raw.get("line"),
                    message=raw.get("message", ""),
                    code_snippet=raw.get("code_snippet"),
                )
                report.violations.append(violation)

        # Fase 2: Enriquecer violaciones existentes con sugerencias AI
        for violation in report.violations:
            if violation.ai_suggestion:
                continue  # Ya enriquecida

            try:
                content = violation.file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Verificar límite de llamadas antes de llamar al LLM
            self._check_call_limit()

            # Intentar enriquecimiento con fallback en caso de rate limit
            try:
                suggestion = self.llm_client.enrich_violation(
                    violation.to_dict(), content
                )
            except RateLimitError as e:
                self._fallback_to_mock(str(e))
                suggestion = self.llm_client.enrich_violation(
                    violation.to_dict(), content
                )

            if suggestion:
                violation.ai_suggestion = suggestion

        # Recalcular score con las nuevas violaciones
        report.calculate_score()

        # Guardar info del proveedor en el reporte
        report.llm_provider_info = self.get_provider_info()

        # Mostrar consumo de tokens
        if hasattr(self.llm_client, 'usage'):
            logger.info("[LLM] %s", self.llm_client.get_usage_summary())

        return report

    def _get_files_with_violations(self, report: Report) -> Set[Path]:
        """Obtiene el conjunto de archivos que ya tienen violaciones estáticas."""
        return {v.file_path for v in report.violations}

    def _filter_candidate_files(
        self, all_files: List[Path], files_with_violations: Set[Path]
    ) -> List[Path]:
        """
        Filtra archivos candidatos para análisis semántico.

        Un archivo es candidato si:
        1. Ya tiene violaciones estáticas (prioridad alta)
        2. Contiene patrones sospechosos que el análisis estático no cubre

        Returns:
            Lista de archivos candidatos ordenados por prioridad
        """
        candidates = []

        for file_path in all_files:
            # Archivos con violaciones tienen prioridad
            if file_path in files_with_violations:
                candidates.append(file_path)
                continue

            # Verificar patrones sospechosos
            try:
                content = file_path.read_text(encoding="utf-8")
                if self._has_suspicious_patterns(content):
                    candidates.append(file_path)
            except (OSError, UnicodeDecodeError):
                continue

        return candidates

    def _has_suspicious_patterns(self, content: str) -> bool:
        """Verifica si el contenido tiene patrones que ameritan análisis semántico."""
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, content):
                return True
        return False

    def get_token_usage(self) -> dict:
        """
        Obtiene el consumo de tokens si se usa GeminiLLMClient.

        Returns:
            Diccionario con información de tokens o vacío si no aplica.
        """
        if hasattr(self.llm_client, 'get_usage_dict'):
            return self.llm_client.get_usage_dict()
        return {}

    def _discover_python_files(self) -> List[Path]:
        """Descubre archivos Python excluyendo directorios irrelevantes."""
        files = []
        for py_file in self.project_path.rglob("*.py"):
            if any(excluded in py_file.parts for excluded in EXCLUDED_DIRS):
                continue
            files.append(py_file)
        return sorted(files)
