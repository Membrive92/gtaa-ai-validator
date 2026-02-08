"""
Generador de reportes en formato HTML.

Produce un dashboard visual autocontenido (HTML + CSS + SVG inline)
con gráficos de distribución de violaciones, gauge de score y tabla detallada.
Sin dependencias externas — todo generado con f-strings de Python.
"""

import html
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from gtaa_validator.models import Report, Severity, Violation, ViolationType, get_score_label


class HtmlReporter:
    """Genera reportes de análisis como dashboard HTML autocontenido."""

    # Colores por severidad
    _COLORS: Dict[str, str] = {
        "CRITICAL": "#dc2626",
        "HIGH": "#ea580c",
        "MEDIUM": "#ca8a04",
        "LOW": "#2563eb",
    }

    # Mapeo de ViolationType a nombre de checker legible
    _CHECKER_NAMES: Dict[str, str] = {
        "ADAPTATION_IN_DEFINITION": "DefinitionChecker — Separación de capas",
        "MISSING_LAYER_STRUCTURE": "StructureChecker — Estructura del proyecto",
        "HARDCODED_TEST_DATA": "QualityChecker — Calidad de tests",
        "ASSERTION_IN_POM": "AdaptationChecker — Page Objects",
        "FORBIDDEN_IMPORT": "AdaptationChecker — Page Objects",
        "BUSINESS_LOGIC_IN_POM": "AdaptationChecker — Page Objects",
        "DUPLICATE_LOCATOR": "AdaptationChecker — Page Objects",
        "LONG_TEST_FUNCTION": "QualityChecker — Calidad de tests",
        "POOR_TEST_NAMING": "QualityChecker — Calidad de tests",
        # Semánticas (Fase 5)
        "UNCLEAR_TEST_PURPOSE": "SemanticAnalyzer — Análisis AI",
        "PAGE_OBJECT_DOES_TOO_MUCH": "SemanticAnalyzer — Análisis AI",
        "IMPLICIT_TEST_DEPENDENCY": "SemanticAnalyzer — Análisis AI",
        "MISSING_WAIT_STRATEGY": "SemanticAnalyzer — Análisis AI",
    }

    # Nombres de severidad en español
    _SEVERITY_LABELS: Dict[str, str] = {
        "CRITICAL": "CRÍTICA",
        "HIGH": "ALTA",
        "MEDIUM": "MEDIA",
        "LOW": "BAJA",
    }

    # Nombres legibles en español para cada tipo de violación
    _VIOLATION_TYPE_LABELS: Dict[str, str] = {
        "ADAPTATION_IN_DEFINITION": "Adaptación en capa de definición",
        "MISSING_LAYER_STRUCTURE": "Estructura de capas ausente",
        "HARDCODED_TEST_DATA": "Datos de test hardcodeados",
        "ASSERTION_IN_POM": "Aserción en Page Object",
        "FORBIDDEN_IMPORT": "Importación prohibida en Page Object",
        "BUSINESS_LOGIC_IN_POM": "Lógica de negocio en Page Object",
        "DUPLICATE_LOCATOR": "Localizador duplicado",
        "LONG_TEST_FUNCTION": "Función de test demasiado larga",
        "POOR_TEST_NAMING": "Nombre de test genérico",
        # Semánticas (Fase 5)
        "UNCLEAR_TEST_PURPOSE": "Propósito de test poco claro",
        "PAGE_OBJECT_DOES_TOO_MUCH": "Page Object con demasiadas responsabilidades",
        "IMPLICIT_TEST_DEPENDENCY": "Dependencia implícita entre tests",
        "MISSING_WAIT_STRATEGY": "Sin estrategia de espera",
    }

    # Orden de los checkers para agrupación
    _CHECKER_ORDER = [
        "StructureChecker — Estructura del proyecto",
        "DefinitionChecker — Separación de capas",
        "AdaptationChecker — Page Objects",
        "QualityChecker — Calidad de tests",
        "SemanticAnalyzer — Análisis AI",
    ]

    def generate(self, report: Report, output_path: Path) -> None:
        """
        Generar reporte HTML y escribirlo al fichero indicado.

        Args:
            report: Resultado del análisis estático
            output_path: Ruta del fichero HTML de salida
        """
        html_content = self._build_html(report)
        output_path = Path(output_path)
        output_path.write_text(html_content, encoding="utf-8")

    def _build_html(self, report: Report) -> str:
        """Construir el documento HTML completo."""
        severity_counts = report.get_violation_count_by_severity()
        score_color = self._get_score_color(report.score)
        score_label = self._get_score_label(report.score)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>gTAA Validator — Reporte de Análisis</title>
    <style>
{self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>gTAA AI Validator</h1>
            <p class="subtitle">Reporte de Análisis Estático</p>
            <div class="meta">
                <span>Proyecto: <strong>{html.escape(str(report.project_path.name))}</strong></span>
                <span>Fecha: <strong>{report.timestamp.strftime('%d/%m/%Y %H:%M')}</strong></span>
                <span>Versión: <strong>{report.validator_version}</strong></span>
                <span>Tiempo: <strong>{report.execution_time_seconds:.2f}s</strong></span>
{self._build_llm_provider_meta(report)}
            </div>
        </header>

        <section class="score-section">
            <div class="score-gauge">
{self._build_score_svg(report.score, score_color)}
                <div class="score-label">{score_label}</div>
            </div>
{self._build_score_context(report.score)}
        </section>

        <section class="summary-cards">
            <div class="card total">
                <div class="card-value">{len(report.violations)}</div>
                <div class="card-label">Violaciones Totales</div>
            </div>
            <div class="card files">
                <div class="card-value">{report.files_analyzed}</div>
                <div class="card-label">Archivos Analizados</div>
            </div>
{self._build_severity_cards(severity_counts)}
        </section>

{self._build_metrics_section(report)}

{self._build_chart_section(severity_counts)}

{self._build_actionable_summary(report)}

{self._build_violations_by_checker(report)}

        <footer>
            <p>Generado por <strong>gTAA AI Validator</strong> v{report.validator_version}</p>
            <div class="footer-links">
                Proyecto: {html.escape(str(report.project_path.name))}
                &middot; {report.timestamp.strftime('%d/%m/%Y %H:%M')}
            </div>
        </footer>
    </div>
</body>
</html>"""

    def _get_css(self) -> str:
        """CSS completo del dashboard."""
        return """        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc; color: #1e293b; line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 1rem 2rem; }

        /* --- Header: dark solid --- */
        header {
            background: #0f172a; color: #fff; text-align: center;
            padding: 2rem 1rem 1.5rem; margin-bottom: 2rem;
        }
        header h1 { font-size: 1.5rem; font-weight: 700; color: #fff; }
        header .subtitle { color: #94a3b8; font-size: 0.9375rem; margin-bottom: 0.75rem; }
        header .meta {
            display: flex; flex-wrap: wrap; justify-content: center; gap: 1.5rem;
            color: #94a3b8; font-size: 0.8125rem;
        }
        header .meta strong { color: #e2e8f0; }

        /* --- Score section: hero gradient (only gradient in page) --- */
        .score-section {
            text-align: center; margin-bottom: 2rem;
            background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
            border-radius: 12px; padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .score-gauge { display: inline-block; }
        .score-label { font-size: 1.125rem; font-weight: 600; margin-top: 0.5rem; color: #334155; }
        .score-context { margin-top: 0.8rem; font-size: 0.8125rem; color: #64748b; max-width: 500px; margin-left: auto; margin-right: auto; }

        /* --- Summary cards: white + shadow --- */
        .summary-cards {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem; margin-bottom: 2rem;
        }
        .card {
            background: #ffffff; border-radius: 10px; padding: 1.2rem;
            text-align: center; border-left: 4px solid #94a3b8;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            transition: transform 0.15s;
        }
        .card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .card-value { font-size: 1.5rem; font-weight: 700; }
        .card-label { font-size: 0.75rem; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }
        .card.total { border-left-color: #334155; }
        .card.total .card-value { color: #0f172a; }
        .card.files { border-left-color: #6366f1; }
        .card.files .card-value { color: #4f46e5; }
        .card.critical { border-left-color: #dc2626; }
        .card.critical .card-value { color: #dc2626; }
        .card.high { border-left-color: #ea580c; }
        .card.high .card-value { color: #ea580c; }
        .card.medium { border-left-color: #ca8a04; }
        .card.medium .card-value { color: #a16207; }
        .card.low { border-left-color: #2563eb; }
        .card.low .card-value { color: #2563eb; }
        .card-zero { opacity: 0.5; }

        /* --- Chart section --- */
        .chart-section {
            background: #ffffff; border-radius: 12px; padding: 1.5rem;
            margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            text-align: center;
        }
        .chart-section h2 { font-size: 1.125rem; margin-bottom: 1rem; color: #334155; }
        .chart-legend { display: flex; justify-content: center; gap: 1.5rem; margin-top: 1rem; font-size: 0.8125rem; }
        .legend-item { display: flex; align-items: center; gap: 0.4rem; }
        .legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }

        /* --- Action summary --- */
        .action-summary {
            background: #ffffff; border-radius: 12px; padding: 1.5rem;
            margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border-left: 4px solid #6366f1;
        }
        .action-summary h2 { font-size: 1.125rem; margin-bottom: 1rem; color: #334155; }
        .action-item {
            padding: 0.7rem 0.8rem; border-bottom: 1px solid #f1f5f9;
            display: flex; gap: 0.8rem; align-items: baseline;
            border-radius: 6px; margin-bottom: 2px;
        }
        .action-item:hover { background: #f8fafc; }
        .action-item:last-child { border-bottom: none; }
        .action-count { font-weight: 700; min-width: 30px; text-align: right; font-size: 1.125rem; }
        .action-text { color: #475569; font-size: 0.9375rem; }

        /* --- Checker groups (violation tables) --- */
        .checker-group {
            background: #ffffff; border-radius: 12px; padding: 1.5rem;
            margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            overflow-x: auto; border-left: 4px solid #94a3b8;
        }
        .checker-group h3 { font-size: 1.125rem; margin-bottom: 0.3rem; color: #0f172a; }
        .checker-subtitle { font-size: 0.8125rem; color: #64748b; margin-bottom: 1rem; }
        .no-violations {
            text-align: center; padding: 2.5rem; color: #16a34a;
            font-size: 1.125rem; font-weight: 600;
            background: #f0fdf4; border-radius: 8px;
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
        th {
            background: #f1f5f9; padding: 0.7rem 0.8rem; text-align: left;
            font-weight: 600; color: #334155; border-bottom: 2px solid #e2e8f0;
            font-size: 0.8125rem;
        }
        td {
            padding: 0.7rem 0.8rem; border-bottom: 1px solid #f1f5f9;
            vertical-align: top; max-width: 300px; overflow: hidden;
            text-overflow: ellipsis;
        }
        tr:nth-child(even) td { background: #f8fafc; }
        tr:nth-child(odd) td { background: #ffffff; }
        tr:hover td { background: #f1f5f9; }
        .severity-badge {
            display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px;
            font-size: 0.75rem; font-weight: 600; color: #fff; white-space: nowrap;
        }
        .badge-critical { background: #dc2626; }
        .badge-high { background: #ea580c; }
        .badge-medium { background: #ca8a04; }
        .badge-low { background: #2563eb; }
        .code-snippet {
            font-family: 'Consolas', 'Monaco', monospace; font-size: 0.8125rem;
            background: #1e293b; color: #e2e8f0; padding: 0.4rem 0.6rem;
            border-radius: 4px; display: block; white-space: pre-wrap;
            word-break: break-word; margin-top: 0.3rem;
        }
        .ai-badge { display: inline-block; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; background: #7c3aed; color: #fff; margin-left: 0.4rem; }
        .ai-suggestion { font-size: 0.8125rem; color: #6d28d9; background: #f5f3ff; padding: 0.4rem 0.6rem; border-radius: 4px; margin-top: 0.3rem; border-left: 3px solid #7c3aed; }
        .violation-type { font-weight: 600; color: #334155; font-size: 0.875rem; }
        .violation-desc { font-size: 0.8125rem; color: #64748b; }

        /* --- Metrics section --- */
        .metrics-section {
            background: #ffffff; border-radius: 12px; padding: 1.5rem;
            margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .metrics-section h2 { font-size: 1.125rem; margin-bottom: 1rem; color: #334155; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
        .metric-card {
            background: #f8fafc; border-radius: 8px; padding: 1rem;
            text-align: center; border: 1px solid #e2e8f0;
        }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #0f172a; }
        .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }
        .metric-card.llm { border-left: 3px solid #7c3aed; }

        /* --- Footer --- */
        footer {
            text-align: center; color: #64748b; font-size: 0.8125rem;
            margin-top: 2rem; padding: 1.5rem 0; border-top: 2px solid #e2e8f0;
        }
        footer strong { color: #334155; }
        footer a { color: #4f46e5; text-decoration: none; }
        footer a:hover { text-decoration: underline; }
        footer .footer-links { margin-top: 0.5rem; }

        @media (max-width: 600px) {
            .summary-cards { grid-template-columns: repeat(2, 1fr); }
            header .meta { flex-direction: column; gap: 0.3rem; }
            table { font-size: 0.8125rem; }
        }"""

    def _build_llm_provider_meta(self, report: Report) -> str:
        """Genera el span de metadatos del proveedor LLM si aplica."""
        if not report.llm_provider_info:
            return ""

        info = report.llm_provider_info
        provider = info.get("current_provider", "unknown")
        provider_display = provider.capitalize()

        if info.get("fallback_occurred"):
            initial = info.get("initial_provider", "unknown").capitalize()
            return f'                <span>LLM: <strong>{initial} &rarr; {provider_display}</strong> (fallback)</span>'
        else:
            return f'                <span>LLM: <strong>{provider_display}</strong></span>'

    def _get_score_color(self, score: float) -> str:
        """Color del gauge según el score."""
        if score >= 90:
            return "#16a34a"
        elif score >= 75:
            return "#65a30d"
        elif score >= 50:
            return "#ca8a04"
        else:
            return "#dc2626"

    def _get_score_label(self, score: float) -> str:
        """Etiqueta textual del score."""
        return get_score_label(score)

    def _build_score_context(self, score: float) -> str:
        """Texto explicativo del cálculo del score."""
        return """            <div class="score-context">
                Puntuación calculada sobre 100. Penalizaciones por violación:
                Crítica &minus;10, Alta &minus;5, Media &minus;2, Baja &minus;1.
            </div>"""

    def _build_score_svg(self, score: float, color: str) -> str:
        """SVG de gauge circular para el score."""
        radius = 70
        circumference = 2 * 3.14159 * radius

        if score <= 0:
            # Score 0: full red ring as visual indicator
            arc_html = (
                f'<circle cx="100" cy="100" r="{radius}" fill="none" stroke="{color}" '
                f'stroke-width="14" opacity="0.3"/>'
            )
        else:
            filled = circumference * (score / 100)
            empty = circumference - filled
            arc_html = (
                f'<circle cx="100" cy="100" r="{radius}" fill="none" stroke="{color}" '
                f'stroke-width="14" stroke-dasharray="{filled:.1f} {empty:.1f}" '
                f'stroke-dashoffset="{circumference * 0.25:.1f}" stroke-linecap="round" '
                f'transform="rotate(-90 100 100)"/>'
            )

        return f"""            <svg width="200" height="200" viewBox="0 0 200 200" role="img" aria-label="Puntuación de cumplimiento: {score:.0f} de 100">
                <title>Puntuación: {score:.0f}/100</title>
                <circle cx="100" cy="100" r="{radius}" fill="none" stroke="#e2e8f0" stroke-width="14"/>
                {arc_html}
                <text x="100" y="92" text-anchor="middle" font-size="36" font-weight="700" fill="{color}">{score:.0f}</text>
                <text x="100" y="116" text-anchor="middle" font-size="14" fill="#64748b">/ 100</text>
            </svg>"""

    def _build_severity_cards(self, counts: dict) -> str:
        """Tarjetas de conteo por severidad."""
        cards = []
        for sev, css_class in [("CRITICAL", "critical"), ("HIGH", "high"), ("MEDIUM", "medium"), ("LOW", "low")]:
            label = self._SEVERITY_LABELS[sev]
            zero_class = " card-zero" if counts[sev] == 0 else ""
            cards.append(f"""            <div class="card {css_class}{zero_class}">
                <div class="card-value">{counts[sev]}</div>
                <div class="card-label">{label}</div>
            </div>""")
        return "\n".join(cards)

    def _build_metrics_section(self, report: Report) -> str:
        """Sección de métricas de rendimiento (timing + LLM)."""
        if not report.metrics:
            return ""

        m = report.metrics
        cards = []

        cards.append(
            f'            <div class="metric-card">'
            f'<div class="metric-value">{m.static_analysis_seconds:.2f}s</div>'
            f'<div class="metric-label">Análisis Estático</div></div>'
        )

        if m.semantic_analysis_seconds > 0:
            cards.append(
                f'            <div class="metric-card">'
                f'<div class="metric-value">{m.semantic_analysis_seconds:.2f}s</div>'
                f'<div class="metric-label">Análisis Semántico</div></div>'
            )

        cards.append(
            f'            <div class="metric-card">'
            f'<div class="metric-value">{m.files_per_second:.1f}</div>'
            f'<div class="metric-label">Archivos/segundo</div></div>'
        )

        if m.llm_api_calls > 0:
            cards.append(
                f'            <div class="metric-card llm">'
                f'<div class="metric-value">{m.llm_api_calls}</div>'
                f'<div class="metric-label">Llamadas API</div></div>'
            )
            cards.append(
                f'            <div class="metric-card llm">'
                f'<div class="metric-value">{m.llm_total_tokens:,}</div>'
                f'<div class="metric-label">Tokens Totales</div></div>'
            )
            cards.append(
                f'            <div class="metric-card llm">'
                f'<div class="metric-value">${m.llm_estimated_cost_usd:.4f}</div>'
                f'<div class="metric-label">Costo Estimado</div></div>'
            )

        cards_html = "\n".join(cards)
        return f"""        <section class="metrics-section">
            <h2>Métricas de Rendimiento</h2>
            <div class="metrics-grid">
{cards_html}
            </div>
        </section>"""

    def _build_chart_section(self, counts: dict) -> str:
        """Sección con gráfico de barras SVG."""
        total = sum(counts.values())
        if total == 0:
            return ""

        bars = []
        labels = []
        x = 30
        bar_width = 60
        gap = 20
        max_height = 150
        min_bar_height = 4
        max_val = max(counts.values()) if max(counts.values()) > 0 else 1

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            val = counts[sev]
            bar_height = (val / max_val) * max_height if max_val > 0 else 0
            if val > 0 and bar_height < min_bar_height:
                bar_height = min_bar_height
            color = self._COLORS[sev]
            y = 180 - bar_height

            bars.append(
                f'<rect x="{x}" y="{y:.0f}" width="{bar_width}" height="{bar_height:.0f}" '
                f'fill="{color}" rx="4"/>'
            )
            if val > 0:
                bars.append(
                    f'<text x="{x + bar_width // 2}" y="{y - 6:.0f}" text-anchor="middle" '
                    f'font-size="13" font-weight="600" fill="{color}">{val}</text>'
                )
            sev_label = self._SEVERITY_LABELS[sev]
            labels.append(
                f'<text x="{x + bar_width // 2}" y="198" text-anchor="middle" '
                f'font-size="11" fill="#64748b">{sev_label}</text>'
            )
            x += bar_width + gap

        chart_width = x + 10
        svg_content = "\n                ".join(bars + labels)

        return f"""        <section class="chart-section">
            <h2>Distribución por Severidad</h2>
            <svg width="{chart_width}" height="210" viewBox="0 0 {chart_width} 210" role="img" aria-label="Gráfico de barras: distribución de violaciones por severidad">
                <title>Distribución de violaciones por severidad</title>
                {svg_content}
            </svg>
        </section>"""

    def _build_actionable_summary(self, report: Report) -> str:
        """Resumen accionable con las principales áreas de mejora."""
        if not report.violations:
            return ""

        # Contar por tipo de violación
        type_counts: Dict[ViolationType, int] = defaultdict(int)
        for v in report.violations:
            type_counts[v.violation_type] += 1

        # Ordenar por severidad y luego por cantidad
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        sorted_types = sorted(
            type_counts.items(),
            key=lambda item: (severity_order.get(item[0].get_severity(), 99), -item[1]),
        )

        items = []
        for vtype, count in sorted_types:
            sev = vtype.get_severity()
            color = self._COLORS[sev.value]
            desc = html.escape(vtype.get_description())
            items.append(
                f'            <div class="action-item">'
                f'<span class="action-count" style="color:{color}">{count}</span>'
                f'<span class="action-text">{desc}</span></div>'
            )

        items_html = "\n".join(items)
        return f"""        <section class="action-summary">
            <h2>Resumen de Hallazgos</h2>
{items_html}
        </section>"""

    def _group_violations_by_checker(self, violations: List[Violation]) -> Dict[str, List[Violation]]:
        """Agrupar violaciones por checker."""
        groups: Dict[str, List[Violation]] = defaultdict(list)
        for v in violations:
            checker_name = self._CHECKER_NAMES.get(v.violation_type.name, "Otro")
            groups[checker_name].append(v)
        return groups

    def _build_violations_by_checker(self, report: Report) -> str:
        """Violaciones agrupadas por checker con subtítulos descriptivos."""
        if not report.violations:
            return """        <section class="checker-group">
            <h3>Violaciones Detectadas</h3>
            <div class="no-violations">Sin violaciones detectadas</div>
        </section>"""

        groups = self._group_violations_by_checker(report.violations)
        sections = []

        for checker_name in self._CHECKER_ORDER:
            if checker_name not in groups:
                continue
            violations = groups[checker_name]
            count = len(violations)

            # Ordenar por severidad dentro del grupo
            severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
            violations.sort(key=lambda v: (severity_order.get(v.severity, 99), str(v.file_path)))

            rows = []
            for v in violations:
                sev_lower = v.severity.value.lower()
                sev_es = self._SEVERITY_LABELS.get(v.severity.value, v.severity.value)
                badge = f'<span class="severity-badge badge-{sev_lower}">{sev_es}</span>'

                try:
                    file_display = str(v.file_path.relative_to(report.project_path))
                except ValueError:
                    file_display = str(v.file_path.name)

                location = html.escape(file_display)
                if v.line_number:
                    location += f":{v.line_number}"

                # Tipo legible con descripción
                type_label = self._VIOLATION_TYPE_LABELS.get(v.violation_type.name, v.violation_type.name)
                type_desc = html.escape(v.violation_type.get_description())
                type_cell = (
                    f'<span class="violation-type">{html.escape(type_label)}</span><br>'
                    f'<span class="violation-desc">{type_desc}</span>'
                )

                snippet = ""
                if v.code_snippet:
                    snippet = f'<span class="code-snippet">{html.escape(v.code_snippet)}</span>'

                ai_html = ""
                if v.ai_suggestion:
                    ai_html = (
                        f'<div class="ai-suggestion">🤖 {html.escape(v.ai_suggestion)}</div>'
                    )

                ai_badge = ""
                if v.ai_suggestion:
                    ai_badge = '<span class="ai-badge">AI</span>'

                rows.append(f"""                <tr>
                    <td>{badge}{ai_badge}</td>
                    <td>{type_cell}</td>
                    <td>{location}</td>
                    <td>{html.escape(v.message)}{snippet}</td>
                    <td>{html.escape(v.recommendation)}{ai_html}</td>
                </tr>""")

            rows_html = "\n".join(rows)
            sections.append(f"""        <section class="checker-group">
            <h3>{html.escape(checker_name)} ({count})</h3>
            <table role="table" aria-label="Violaciones de {html.escape(checker_name)}">
                <thead>
                    <tr>
                        <th style="width:90px">Severidad</th>
                        <th style="width:240px">Tipo</th>
                        <th style="width:160px">Ubicación</th>
                        <th>Detalle</th>
                        <th style="width:280px">Recomendación</th>
                    </tr>
                </thead>
                <tbody>
{rows_html}
                </tbody>
            </table>
        </section>""")

        return "\n\n".join(sections)
