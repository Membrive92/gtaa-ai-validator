"""
Analizador Semántico para gTAA Validator (Fase 5).

Complementa el análisis estático con detección semántica via LLM.
Funciones principales:
1. Detectar nuevas violaciones semánticas que AST no puede captar
2. Enriquecer violaciones estáticas existentes con sugerencias AI

El SemanticAnalyzer recibe un Report ya generado por StaticAnalyzer
y lo enriquece con análisis semántico.
"""

from pathlib import Path
from typing import List

from gtaa_validator.models import Report, Violation, ViolationType, Severity
from gtaa_validator.llm.client import MockLLMClient


# Directorios excluidos del análisis (mismos que StaticAnalyzer)
EXCLUDED_DIRS = {
    "venv", "env", ".venv", ".env", ".git", "__pycache__",
    "node_modules", ".pytest_cache", "build", "dist",
}


class SemanticAnalyzer:
    """
    Analizador semántico que usa MockLLMClient para detectar y enriquecer violaciones.

    Uso:
        client = MockLLMClient()
        semantic = SemanticAnalyzer(project_path, client)
        enriched_report = semantic.analyze(static_report)
    """

    def __init__(self, project_path: Path, llm_client: MockLLMClient, verbose: bool = False):
        self.project_path = project_path
        self.llm_client = llm_client
        self.verbose = verbose

    def analyze(self, report: Report) -> Report:
        """
        Enriquece un Report existente con análisis semántico.

        1. Descubre ficheros Python del proyecto
        2. Para cada fichero: detecta violaciones semánticas
        3. Para cada violación existente: genera sugerencia AI
        4. Recalcula el score

        Returns:
            El mismo Report, modificado con violaciones semánticas y sugerencias AI.
        """
        python_files = self._discover_python_files()

        # Fase 1: Detectar nuevas violaciones semánticas
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            file_str = str(file_path)
            raw_violations = self.llm_client.analyze_file(content, file_str)

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

            suggestion = self.llm_client.enrich_violation(
                violation.to_dict(), content
            )
            if suggestion:
                violation.ai_suggestion = suggestion

        # Recalcular score con las nuevas violaciones
        report.calculate_score()

        return report

    def _discover_python_files(self) -> List[Path]:
        """Descubre archivos Python excluyendo directorios irrelevantes."""
        files = []
        for py_file in self.project_path.rglob("*.py"):
            if any(excluded in py_file.parts for excluded in EXCLUDED_DIRS):
                continue
            files.append(py_file)
        return sorted(files)
