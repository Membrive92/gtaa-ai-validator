"""
Interfaz de línea de comandos para gTAA Validator.

Punto de entrada al ejecutar: python -m gtaa_validator

Análisis estático con AST:
- Detectar violaciones arquitectónicas gTAA
- Calcular puntuación de cumplimiento (0-100)
- Mostrar violaciones por severidad
- Soporte de flag --verbose para información detallada
- Exportación a JSON y HTML (--json, --html)
- Análisis semántico AI con --ai (Fase 5)
"""

import os
import click
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer
from gtaa_validator.reporters.json_reporter import JsonReporter
from gtaa_validator.reporters.html_reporter import HtmlReporter
from gtaa_validator.analyzers.semantic_analyzer import SemanticAnalyzer
from gtaa_validator.llm.client import MockLLMClient
from gtaa_validator.llm.gemini_client import GeminiLLMClient
from gtaa_validator.config import load_config


@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Activar salida detallada')
@click.option('--json', 'json_path', type=click.Path(), default=None, help='Exportar reporte JSON al fichero indicado')
@click.option('--html', 'html_path', type=click.Path(), default=None, help='Exportar reporte HTML al fichero indicado')
@click.option('--ai', is_flag=True, help='Activar análisis semántico AI')
@click.option('--config', 'config_path', type=click.Path(exists=True), default=None,
              help='Ruta al archivo de configuración .gtaa.yaml')
def main(project_path: str, verbose: bool, json_path: str, html_path: str, ai: bool, config_path: str):
    """
    Valida el cumplimiento de la arquitectura gTAA en un proyecto de test automation.

    PROJECT_PATH: Ruta al directorio raíz del proyecto de test a analizar.

    Ejemplo:
        python -m gtaa_validator ./mi-proyecto-selenium
        python -m gtaa_validator ./mi-proyecto-selenium --verbose
    """
    # Mostrar cabecera
    click.echo("=== gTAA AI Validator - Fase 5 ===")
    click.echo(f"Analizando proyecto: {project_path}\n")

    # Convertir a objeto Path y resolver a ruta absoluta
    project_path = Path(project_path).resolve()

    # Validar que la ruta es un directorio
    if not project_path.is_dir():
        click.echo(f"ERROR: {project_path} no es un directorio", err=True)
        sys.exit(1)

    # Cargar configuración del proyecto
    config = None
    if config_path:
        config = load_config(Path(config_path).parent)

    # Crear analizador y ejecutar análisis
    analyzer = StaticAnalyzer(project_path, verbose=verbose, config=config)

    if not verbose:
        click.echo("Ejecutando análisis estático...")

    report = analyzer.analyze()

    # Análisis semántico AI (opcional)
    if ai:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            click.echo("Usando Gemini Flash API para análisis semántico...")
            llm_client = GeminiLLMClient(api_key)
        else:
            click.echo("GEMINI_API_KEY no configurada, usando análisis mock...")
            llm_client = MockLLMClient()
        semantic = SemanticAnalyzer(project_path, llm_client, verbose=verbose)
        report = semantic.analyze(report)

    # Mostrar resultados
    if not verbose:
        click.echo()

    click.echo("="*60)
    click.echo("RESULTADOS DEL ANÁLISIS")
    click.echo("="*60)

    # Estadísticas de archivos
    click.echo(f"\nArchivos analizados: {report.files_analyzed}")
    click.echo(f"Violaciones totales: {len(report.violations)}")

    # Violaciones por severidad
    severity_counts = report.get_violation_count_by_severity()
    click.echo("\nViolaciones por severidad:")
    click.echo(f"  CRÍTICA: {severity_counts['CRITICAL']}")
    click.echo(f"  ALTA:    {severity_counts['HIGH']}")
    click.echo(f"  MEDIA:   {severity_counts['MEDIUM']}")
    click.echo(f"  BAJA:    {severity_counts['LOW']}")

    # Puntuación de cumplimiento
    click.echo(f"\nPuntuación de cumplimiento: {report.score:.1f}/100")

    # Interpretación del score
    if report.score >= 90:
        score_label = "EXCELENTE"
    elif report.score >= 75:
        score_label = "BUENO"
    elif report.score >= 50:
        score_label = "NECESITA MEJORAS"
    else:
        score_label = "PROBLEMAS CRÍTICOS"

    click.echo(f"Estado: {score_label}")

    # En modo verbose, mostrar información detallada de violaciones
    if verbose and report.violations:
        click.echo("\n" + "="*60)
        click.echo("VIOLACIONES DETALLADAS")
        click.echo("="*60)

        for i, violation in enumerate(report.violations, 1):
            click.echo(f"\n[{i}] {violation.severity.value} - {violation.violation_type.name}")

            # Mostrar archivo y número de línea
            try:
                relative_path = violation.file_path.relative_to(project_path)
            except ValueError:
                relative_path = violation.file_path

            location = f"{relative_path}"
            if violation.line_number:
                location += f":{violation.line_number}"
            click.echo(f"    Ubicación: {location}")

            # Mostrar mensaje
            click.echo(f"    Mensaje: {violation.message}")

            # Mostrar fragmento de código si está disponible
            if violation.code_snippet:
                click.echo(f"    Código: {violation.code_snippet}")

            # Mostrar sugerencia AI si existe
            if violation.ai_suggestion:
                click.echo(f"    [AI] {violation.ai_suggestion}")

    # Exportar reportes si se solicitaron
    if json_path:
        JsonReporter().generate(report, Path(json_path))
        click.echo(f"\nReporte JSON exportado: {json_path}")

    if html_path:
        HtmlReporter().generate(report, Path(html_path))
        click.echo(f"Reporte HTML exportado: {html_path}")

    # Resumen final
    click.echo("\n" + "="*60)
    click.echo(f"Análisis completado en {report.execution_time_seconds:.2f}s")
    click.echo("="*60)

    # Código de salida 1 si hay violaciones críticas
    if severity_counts['CRITICAL'] > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
