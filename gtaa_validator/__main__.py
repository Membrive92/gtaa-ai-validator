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
from datetime import datetime
from pathlib import Path
try:
    from dotenv import load_dotenv
    # Cargar .env desde el directorio del paquete, NO desde CWD del proyecto analizado (SEC-08)
    _package_dir = Path(__file__).resolve().parent.parent
    load_dotenv(_package_dir / ".env")
    # Tambien cargar desde home del usuario como fallback
    load_dotenv(Path.home() / ".env")
except ImportError:
    pass  # python-dotenv es opcional (incluido en extras [ai])

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer
from gtaa_validator.reporters.json_reporter import JsonReporter
from gtaa_validator.reporters.html_reporter import HtmlReporter
from gtaa_validator.config import load_config
from gtaa_validator.logging_config import setup_logging
from gtaa_validator.models import AnalysisMetrics, get_score_label
from gtaa_validator.file_utils import safe_relative_path


def _run_static_analysis(project_path: Path, verbose: bool, config) -> tuple:
    """Ejecuta análisis estático y retorna (report, elapsed_seconds)."""
    analyzer = StaticAnalyzer(project_path, verbose=verbose, config=config)
    if not verbose:
        click.echo("Ejecutando análisis estático...")
    t0 = time.time()
    report = analyzer.analyze()
    return report, time.time() - t0


def _run_semantic_analysis(
    project_path: Path, report, provider: str, verbose: bool, max_llm_calls: int
) -> tuple:
    """Ejecuta análisis semántico AI y retorna (report, semantic_analyzer, elapsed_seconds)."""
    from gtaa_validator.analyzers.semantic_analyzer import SemanticAnalyzer
    from gtaa_validator.llm.factory import create_llm_client

    llm_client = create_llm_client(provider=provider)
    provider_name = type(llm_client).__name__
    click.echo(f"Iniciando análisis semántico con {provider_name}...")

    semantic = SemanticAnalyzer(
        project_path, llm_client, verbose=verbose, max_llm_calls=max_llm_calls
    )
    t0 = time.time()
    report = semantic.analyze(report)
    elapsed = time.time() - t0

    # Mostrar info del proveedor usado
    if report.llm_provider_info:
        info = report.llm_provider_info
        if info.get("fallback_occurred"):
            click.echo(f"[!] Fallback activado: {info['initial_provider']} -> {info['current_provider']}")
        else:
            click.echo(f"Análisis completado con: {info['current_provider']}")

    return report, semantic, elapsed


def _display_results(report, project_path: Path, verbose: bool) -> dict:
    """Muestra resultados del análisis y retorna severity_counts."""
    if not verbose:
        click.echo()

    click.echo("=" * 60)
    click.echo("RESULTADOS DEL ANÁLISIS")
    click.echo("=" * 60)

    click.echo(f"\nArchivos analizados: {report.files_analyzed}")
    click.echo(f"Violaciones totales: {len(report.violations)}")

    severity_counts = report.get_violation_count_by_severity()
    click.echo("\nViolaciones por severidad:")
    click.echo(f"  CRÍTICA: {severity_counts['CRITICAL']}")
    click.echo(f"  ALTA:    {severity_counts['HIGH']}")
    click.echo(f"  MEDIA:   {severity_counts['MEDIUM']}")
    click.echo(f"  BAJA:    {severity_counts['LOW']}")

    click.echo(f"\nPuntuación de cumplimiento: {report.score:.1f}/100")
    click.echo(f"Estado: {get_score_label(report.score)}")

    if verbose and report.violations:
        click.echo("\n" + "=" * 60)
        click.echo("VIOLACIONES DETALLADAS")
        click.echo("=" * 60)

        for i, violation in enumerate(report.violations, 1):
            click.echo(f"\n[{i}] {violation.severity.value} - {violation.violation_type.name}")
            relative_path = safe_relative_path(violation.file_path, project_path)
            location = f"{relative_path}"
            if violation.line_number:
                location += f":{violation.line_number}"
            click.echo(f"    Ubicación: {location}")
            click.echo(f"    Mensaje: {violation.message}")
            if violation.code_snippet:
                click.echo(f"    Código: {violation.code_snippet}")
            if violation.ai_suggestion:
                click.echo(f"    [AI] {violation.ai_suggestion}")

    return severity_counts


def _build_metrics(report, semantic, static_secs: float, semantic_secs: float, total_start: float) -> AnalysisMetrics:
    """Construye métricas de rendimiento del análisis."""
    metrics = AnalysisMetrics(
        static_analysis_seconds=static_secs,
        semantic_analysis_seconds=semantic_secs,
        total_seconds=time.time() - total_start,
        files_per_second=report.files_analyzed / static_secs if static_secs > 0 else 0.0,
    )

    if semantic:
        token_usage = semantic.get_token_usage()
        if token_usage:
            metrics.llm_api_calls = token_usage.get('total_calls', 0)
            metrics.llm_input_tokens = token_usage.get('input_tokens', 0)
            metrics.llm_output_tokens = token_usage.get('output_tokens', 0)
            metrics.llm_total_tokens = token_usage.get('total_tokens', 0)
            metrics.llm_estimated_cost_usd = token_usage.get('estimated_cost_usd', 0.0)

    return metrics


def _generate_reports(
    report, metrics: AnalysisMetrics,
    json_path: str, html_path: str, output_dir: str, no_report: bool, project_path: Path,
) -> tuple:
    """Genera reportes JSON/HTML. Retorna (json_path, html_path) usados."""
    # Auto-generación de reportes con fecha y nombre de proyecto
    if not json_path and not html_path and not no_report:
        date_stamp = datetime.now().strftime("%Y-%m-%d")
        project_name = project_path.name
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = str(out_dir / f"gtaa_report_{project_name}_{date_stamp}.json")
        html_path = str(out_dir / f"gtaa_report_{project_name}_{date_stamp}.html")

    report.metrics = metrics

    if json_path:
        json_out = Path(json_path)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        JsonReporter().generate(report, json_out)
        click.echo(f"\nReporte JSON exportado: {json_path}")

    if html_path:
        html_out = Path(html_path)
        html_out.parent.mkdir(parents=True, exist_ok=True)
        HtmlReporter().generate(report, html_out)
        click.echo(f"Reporte HTML exportado: {html_path}")

    return json_path, html_path


def _display_llm_summary(report, semantic) -> None:
    """Muestra resumen de uso del proveedor LLM y tokens."""
    if report.llm_provider_info:
        info = report.llm_provider_info
        click.echo("\n[Análisis Semántico AI]")
        click.echo(f"  Proveedor: {info['current_provider']}")
        if info.get("fallback_occurred"):
            click.echo(f"  Fallback: Si ({info['initial_provider']} -> {info['current_provider']})")

    if semantic and hasattr(semantic, 'get_token_usage'):
        token_usage = semantic.get_token_usage()
        if token_usage.get('total_tokens', 0) > 0:
            click.echo("\n[LLM API - Consumo de Tokens]")
            click.echo(f"  Tokens entrada: {token_usage['input_tokens']:,}")
            click.echo(f"  Tokens salida:  {token_usage['output_tokens']:,}")
            click.echo(f"  Total tokens:   {token_usage['total_tokens']:,}")
            click.echo(f"  Llamadas API:   {token_usage['total_calls']}")
            click.echo(f"  Costo estimado: ${token_usage['estimated_cost_usd']:.4f} USD")


@click.command()
@click.argument('project_path', nargs=-1, required=False)
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
@click.option('--output-dir', type=click.Path(), default='gtaa-reports',
              help='Directorio de salida para reportes (default: gtaa-reports/)')
@click.option('--no-report', is_flag=True,
              help='Desactivar generación automática de reportes')
@click.option('--examples-path', 'show_examples', is_flag=True,
              help='Mostrar la ruta a los proyectos de ejemplo incluidos y salir')
def main(project_path: tuple, verbose: bool, json_path: str, html_path: str, ai: bool, provider: str, config_path: str, max_llm_calls: int, log_file: str, output_dir: str, no_report: bool, show_examples: bool):
    """
    Valida el cumplimiento de la arquitectura gTAA en un proyecto de test automation.

    PROJECT_PATH: Ruta al directorio raíz del proyecto de test a analizar.

    Ejemplo:
        python -m gtaa_validator ./mi-proyecto-selenium
        python -m gtaa_validator ./mi-proyecto-selenium --verbose
    """
    # --examples-path: mostrar ruta a ejemplos y salir
    if show_examples:
        from gtaa_validator.examples import get_examples_path
        examples_dir = get_examples_path()
        click.echo(f"Proyectos de ejemplo incluidos en: {examples_dir}")
        click.echo()
        for d in sorted(examples_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                click.echo(f"  {d.name}/")
        click.echo()
        click.echo("Uso:")
        click.echo(f"  python -m gtaa_validator {examples_dir / 'bad_project'} --verbose")
        return

    # Validar que se proporcionó un path
    if not project_path:
        click.echo("ERROR: Se requiere PROJECT_PATH. Usa --help para ver opciones.", err=True)
        click.echo("       Usa --examples-path para ver los proyectos de ejemplo incluidos.", err=True)
        sys.exit(1)

    # Setup
    if verbose and not log_file:
        log_file = "logs/gtaa_debug.log"
    setup_logging(verbose=verbose, log_file=log_file)

    # Unir partes del path (soporta rutas con espacios sin comillas)
    project_path = Path(" ".join(project_path)).resolve()

    click.echo("=== gTAA AI Validator ===")
    click.echo(f"Analizando proyecto: {project_path}\n")

    if not project_path.is_dir():
        click.echo(f"ERROR: {project_path} no es un directorio válido", err=True)
        sys.exit(1)

    config = load_config(Path(config_path).parent) if config_path else None
    total_start = time.time()

    # Análisis estático
    report, static_secs = _run_static_analysis(project_path, verbose, config)

    # Análisis semántico AI (opcional)
    semantic = None
    semantic_secs = 0.0
    if ai:
        report, semantic, semantic_secs = _run_semantic_analysis(
            project_path, report, provider, verbose, max_llm_calls
        )

    # Resultados
    severity_counts = _display_results(report, project_path, verbose)

    # Métricas
    metrics = _build_metrics(report, semantic, static_secs, semantic_secs, total_start)

    # Reportes
    _generate_reports(report, metrics, json_path, html_path, output_dir, no_report, project_path)

    # Actualizar métricas con tiempo de generación de reportes
    metrics.report_generation_seconds = time.time() - total_start - static_secs - semantic_secs
    metrics.total_seconds = time.time() - total_start
    report.metrics = metrics

    # Resumen LLM
    _display_llm_summary(report, semantic)

    # Resumen final
    click.echo("\n" + "=" * 60)
    click.echo(f"Análisis completado en {metrics.total_seconds:.2f}s")
    click.echo("=" * 60)

    # Código de salida 1 si hay violaciones críticas
    return 1 if severity_counts['CRITICAL'] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
