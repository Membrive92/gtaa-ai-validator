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

import click
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer
from gtaa_validator.reporters.json_reporter import JsonReporter
from gtaa_validator.reporters.html_reporter import HtmlReporter
from gtaa_validator.analyzers.semantic_analyzer import SemanticAnalyzer
from gtaa_validator.llm.factory import create_llm_client
from gtaa_validator.config import load_config
from gtaa_validator.logging_config import setup_logging
from gtaa_validator.models import AnalysisMetrics


@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Activar salida detallada')
@click.option('--json', 'json_path', type=click.Path(), default=None, help='Exportar reporte JSON al fichero indicado')
@click.option('--html', 'html_path', type=click.Path(), default=None, help='Exportar reporte HTML al fichero indicado')
@click.option('--ai', is_flag=True, help='Activar análisis semántico AI')
@click.option('--provider', type=click.Choice(['gemini', 'mock']), default=None,
              help='Proveedor LLM: gemini (cloud, default si hay API key), mock (heurísticas)')
@click.option('--config', 'config_path', type=click.Path(exists=True), default=None,
              help='Ruta al archivo de configuración .gtaa.yaml')
@click.option('--max-llm-calls', type=int, default=None,
              help='Limite de llamadas al LLM real antes de fallback a mock (default: sin limite)')
@click.option('--log-file', type=click.Path(), default=None,
              help='Escribir log detallado a fichero (siempre nivel DEBUG)')
def main(project_path: str, verbose: bool, json_path: str, html_path: str, ai: bool, provider: str, config_path: str, max_llm_calls: int, log_file: str):
    """
    Valida el cumplimiento de la arquitectura gTAA en un proyecto de test automation.

    PROJECT_PATH: Ruta al directorio raíz del proyecto de test a analizar.

    Ejemplo:
        python -m gtaa_validator ./mi-proyecto-selenium
        python -m gtaa_validator ./mi-proyecto-selenium --verbose
    """
    # Con --verbose y sin --log-file explícito, escribir a logs/gtaa_debug.log
    if verbose and not log_file:
        log_file = "logs/gtaa_debug.log"

    # Configurar sistema de logging
    setup_logging(verbose=verbose, log_file=log_file)

    # Mostrar cabecera
    click.echo("=== gTAA AI Validator ===")
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

    t0 = time.time()
    report = analyzer.analyze()
    t1 = time.time()

    # Análisis semántico AI (opcional)
    semantic = None
    if ai:
        llm_client = create_llm_client(provider=provider)
        provider_name = type(llm_client).__name__
        click.echo(f"Iniciando análisis semántico con {provider_name}...")
        semantic = SemanticAnalyzer(
            project_path, llm_client, verbose=verbose, max_llm_calls=max_llm_calls
        )
        report = semantic.analyze(report)

        # Mostrar info del proveedor usado
        if report.llm_provider_info:
            info = report.llm_provider_info
            if info.get("fallback_occurred"):
                click.echo(f"[!] Fallback activado: {info['initial_provider']} -> {info['current_provider']}")
            else:
                click.echo(f"Análisis completado con: {info['current_provider']}")

    t2 = time.time()

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

    # Construir métricas de rendimiento
    static_secs = t1 - t0
    semantic_secs = t2 - t1 if ai else 0.0

    metrics = AnalysisMetrics(
        static_analysis_seconds=static_secs,
        semantic_analysis_seconds=semantic_secs,
        total_seconds=t2 - t0,
        files_per_second=report.files_analyzed / static_secs if static_secs > 0 else 0.0,
    )

    # Poblar métricas LLM si se usó análisis semántico
    if semantic:
        token_usage = semantic.get_token_usage()
        if token_usage:
            metrics.llm_api_calls = token_usage.get('total_calls', 0)
            metrics.llm_input_tokens = token_usage.get('input_tokens', 0)
            metrics.llm_output_tokens = token_usage.get('output_tokens', 0)
            metrics.llm_total_tokens = token_usage.get('total_tokens', 0)
            metrics.llm_estimated_cost_usd = token_usage.get('estimated_cost_usd', 0.0)

    # Exportar reportes si se solicitaron
    if json_path:
        report.metrics = metrics
        JsonReporter().generate(report, Path(json_path))
        click.echo(f"\nReporte JSON exportado: {json_path}")

    if html_path:
        report.metrics = metrics
        HtmlReporter().generate(report, Path(html_path))
        click.echo(f"Reporte HTML exportado: {html_path}")

    t3 = time.time()
    metrics.report_generation_seconds = t3 - t2
    metrics.total_seconds = t3 - t0
    report.metrics = metrics

    # Mostrar info del proveedor LLM si se usó --ai
    if report.llm_provider_info:
        info = report.llm_provider_info
        click.echo("\n[Análisis Semántico AI]")
        click.echo(f"  Proveedor: {info['current_provider']}")
        if info.get("fallback_occurred"):
            click.echo(f"  Fallback: Si ({info['initial_provider']} -> {info['current_provider']})")

    # Mostrar consumo de tokens si se usó LLM API
    if semantic and hasattr(semantic, 'get_token_usage'):
        token_usage = semantic.get_token_usage()
        if token_usage.get('total_tokens', 0) > 0:
            click.echo("\n[LLM API - Consumo de Tokens]")
            click.echo(f"  Tokens entrada: {token_usage['input_tokens']:,}")
            click.echo(f"  Tokens salida:  {token_usage['output_tokens']:,}")
            click.echo(f"  Total tokens:   {token_usage['total_tokens']:,}")
            click.echo(f"  Llamadas API:   {token_usage['total_calls']}")
            click.echo(f"  Costo estimado: ${token_usage['estimated_cost_usd']:.4f} USD")

    # Resumen final
    click.echo("\n" + "="*60)
    click.echo(f"Análisis completado en {metrics.total_seconds:.2f}s")
    click.echo("="*60)

    # Código de salida 1 si hay violaciones críticas
    if severity_counts['CRITICAL'] > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
