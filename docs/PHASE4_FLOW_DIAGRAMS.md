# Fase 4 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Fase 4](#1-visión-general-de-la-fase-4)
2. [Arquitectura del Módulo de Reportes](#2-arquitectura-del-módulo-de-reportes)
3. [Flujo Principal: Generación de Reportes](#3-flujo-principal-generación-de-reportes)
4. [JsonReporter — Exportación JSON](#4-jsonreporter--exportación-json)
5. [HtmlReporter — Dashboard Visual](#5-htmlreporter--dashboard-visual)
6. [Estructura del Dashboard HTML](#6-estructura-del-dashboard-html)
7. [SVG Inline: Gauge de Score y Gráfico de Barras](#7-svg-inline-gauge-de-score-y-gráfico-de-barras)
8. [Agrupación de Violaciones por Checker](#8-agrupación-de-violaciones-por-checker)
9. [Integración con el CLI](#9-integración-con-el-cli)
10. [Mapa de Tests](#10-mapa-de-tests)

---

## 1. Visión General de la Fase 4

La Fase 4 añade generación de reportes profesionales al validador. Los reportes se exportan bajo demanda desde el CLI mediante flags `--json` y `--html`, sin alterar la salida de texto existente.

```
┌─────────────────────────────────────────────────────────────┐
│                      __main__.py (CLI)                       │
│                                                             │
│  python -m gtaa_validator /path --json r.json --html r.html │
│                                                             │
│  1. StaticAnalyzer.analyze() ──────────► Report             │
│                                            │                │
│  2. Salida de texto (siempre)              │                │
│                                            │                │
│  3. Si --json:                             │                │
│     JsonReporter().generate(report, path) ─┘                │
│                                                             │
│  4. Si --html:                                              │
│     HtmlReporter().generate(report, path) ─┘                │
└─────────────────────────────────────────────────────────────┘
```

Los dos flags son **independientes y compatibles**: se pueden usar juntos, por separado, o no usar ninguno.

---

## 2. Arquitectura del Módulo de Reportes

```
gtaa_validator/reporters/
├── __init__.py          ← Re-exporta JsonReporter y HtmlReporter
├── json_reporter.py     ← Serialización a JSON
└── html_reporter.py     ← Dashboard HTML autocontenido

Dependencias:

  __main__.py ─────► JsonReporter  ─────► Report.to_dict()
       │                                     │
       └──────────► HtmlReporter  ─────► Report (acceso directo)
                         │
                         ├── html.escape()     (XSS prevention)
                         ├── collections.defaultdict
                         └── f-strings         (template engine)
```

Ambos reporters implementan la misma interfaz:

```python
class Reporter:
    def generate(self, report: Report, output_path: Path) -> None: ...
```

No existe una clase base abstracta porque solo hay dos implementaciones y no se prevé un número elevado de formatos adicionales. Si en el futuro se añaden más (PDF, CSV), se formalizaría con una `BaseReporter`.

---

## 3. Flujo Principal: Generación de Reportes

```
┌─────────────────┐
│ CLI recibe flags │
│ --json / --html  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ StaticAnalyzer       │
│ .analyze()           │──────► Report (ya existía en Fase 2)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Salida texto (click) │  ← Siempre se muestra
└────────┬────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 --json?   --html?
    │         │
    ▼         ▼
┌────────┐  ┌────────┐
│ Json   │  │ Html   │
│Reporter│  │Reporter│
│.gen()  │  │.gen()  │
└───┬────┘  └───┬────┘
    │           │
    ▼           ▼
 report.json  report.html
```

---

## 4. JsonReporter — Exportación JSON

El `JsonReporter` es el reporter más simple: delega toda la serialización a `Report.to_dict()`.

```
┌───────────────────────────────────┐
│         JsonReporter.generate()   │
│                                   │
│  1. report.to_dict()              │
│     └── Devuelve dict con:        │
│         ├── metadata              │
│         │   ├── project_path      │
│         │   ├── timestamp         │
│         │   ├── validator_version │
│         │   └── execution_time    │
│         ├── summary               │
│         │   ├── files_analyzed    │
│         │   ├── total_violations  │
│         │   ├── score             │
│         │   └── violations_by_sev │
│         └── violations[]          │
│             ├── type              │
│             ├── severity          │
│             ├── file              │
│             ├── line              │
│             ├── message           │
│             ├── recommendation    │
│             └── code_snippet      │
│                                   │
│  2. json.dumps(data,              │
│       indent=2,                   │
│       ensure_ascii=False)         │
│                                   │
│  3. output_path.write_text(       │
│       encoding="utf-8")           │
└───────────────────────────────────┘
```

**Puntos clave:**
- `indent=2`: JSON legible para revisión humana
- `ensure_ascii=False`: Preserva caracteres UTF-8 (español: `á`, `é`, `ñ`)
- `to_dict()` ya existía en el modelo `Report` desde la Fase 2

---

## 5. HtmlReporter — Dashboard Visual

El `HtmlReporter` genera un fichero HTML autocontenido con CSS y SVG inline.

```
┌──────────────────────────────────────────────────────┐
│              HtmlReporter.generate()                  │
│                                                      │
│  _build_html(report)                                 │
│     │                                                │
│     ├── _get_css()              → CSS completo       │
│     ├── _build_score_svg()      → Gauge circular SVG │
│     ├── _build_score_context()  → Texto explicativo  │
│     ├── _build_severity_cards() → Tarjetas por sev.  │
│     ├── _build_chart_section()  → Gráfico barras SVG │
│     ├── _build_actionable_summary() → Resumen        │
│     └── _build_violations_by_checker() → Tablas      │
│                                                      │
│  output_path.write_text(html, encoding="utf-8")      │
└──────────────────────────────────────────────────────┘
```

**Métodos privados auxiliares:**

| Método | Responsabilidad |
|--------|----------------|
| `_get_css()` | CSS completo inline (responsive, grid, SVG) |
| `_get_score_color(score)` | Color del gauge según rango |
| `_get_score_label(score)` | Etiqueta textual (EXCELENTE, BUENO, etc.) |
| `_build_score_svg(score, color)` | SVG circular con stroke-dasharray |
| `_build_score_context(score)` | Texto explicativo del cálculo del score |
| `_build_severity_cards(counts)` | 4 tarjetas con conteo por severidad |
| `_build_chart_section(counts)` | Gráfico de barras SVG |
| `_build_actionable_summary(report)` | Resumen con conteo por tipo de violación |
| `_group_violations_by_checker(violations)` | Agrupa violaciones por checker |
| `_build_violations_by_checker(report)` | Secciones con tabla por checker |

---

## 6. Estructura del Dashboard HTML

```
┌─────────────────────────────────────────────┐
│               CABECERA                       │
│  gTAA AI Validator — Reporte de Análisis     │
│  Proyecto | Fecha | Versión | Tiempo         │
├─────────────────────────────────────────────┤
│           GAUGE DE SCORE (SVG)               │
│              ┌─────┐                         │
│              │ 65  │  NECESITA MEJORAS        │
│              │/100 │                          │
│              └─────┘                         │
│  Penalizaciones: Crítica −10, Alta −5, ...   │
├─────────────────────────────────────────────┤
│         TARJETAS DE RESUMEN                  │
│  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐   │
│  │  35  ││  5   ││ 12   ││  8   ││  10  │   │
│  │Total ││Files ││CRIT  ││HIGH  ││LOW   │   │
│  └──────┘└──────┘└──────┘└──────┘└──────┘   │
├─────────────────────────────────────────────┤
│      GRÁFICO DE BARRAS (SVG)                 │
│  Distribución por Severidad                  │
│  ████                                        │
│  ████  ███                                   │
│  ████  ███  ██                               │
│  ████  ███  ██  █                            │
│  CRIT  HIGH MED LOW                          │
├─────────────────────────────────────────────┤
│      RESUMEN DE HALLAZGOS                    │
│  12  Llamada directa al navegador en tests   │
│   8  Datos de test escritos en el código      │
│   5  Nombre de test genérico                  │
├─────────────────────────────────────────────┤
│  DefinitionChecker — Separación de capas (12)│
│  ┌─────────┬──────────┬────────┬────────────┐│
│  │Severidad│ Tipo     │Ubicac. │ Detalle    ││
│  ├─────────┼──────────┼────────┼────────────┤│
│  │CRITICAL │ADAPTA... │test:10 │ driver...  ││
│  └─────────┴──────────┴────────┴────────────┘│
├─────────────────────────────────────────────┤
│  QualityChecker — Calidad de tests (8)       │
│  ┌─────────┬──────────┬────────┬────────────┐│
│  │...      │...       │...     │...         ││
│  └─────────┴──────────┴────────┴────────────┘│
├─────────────────────────────────────────────┤
│  FOOTER                                      │
│  Generado por gTAA AI Validator v0.4.0       │
└─────────────────────────────────────────────┘
```

Cuando no hay violaciones, el dashboard muestra:
- Score 100 con etiqueta "EXCELENTE"
- Sin gráfico de barras
- Sin resumen de hallazgos
- Mensaje "Sin violaciones detectadas"

---

## 7. SVG Inline: Gauge de Score y Gráfico de Barras

### Gauge Circular

El gauge usa dos `<circle>` SVG superpuestos:

```
Círculo de fondo (gris):
  <circle cx="100" cy="100" r="70"
          stroke="#e2e8f0" stroke-width="14"/>

Círculo de progreso (color según score):
  <circle cx="100" cy="100" r="70"
          stroke="{color}" stroke-width="14"
          stroke-dasharray="{filled} {empty}"
          stroke-dashoffset="{circumference * 0.25}"
          transform="rotate(-90 100 100)"/>
```

El `stroke-dasharray` controla cuánto del círculo se rellena:
- `filled = circumference × (score / 100)`
- `empty = circumference - filled`
- `stroke-dashoffset` rota el inicio al punto superior (12 en un reloj)

**Colores por rango:**

| Score | Color | Etiqueta |
|-------|-------|----------|
| ≥ 90 | `#16a34a` (verde) | EXCELENTE |
| ≥ 75 | `#65a30d` (lima) | BUENO |
| ≥ 50 | `#ca8a04` (ámbar) | NECESITA MEJORAS |
| < 50 | `#dc2626` (rojo) | PROBLEMAS CRÍTICOS |

### Gráfico de Barras

El gráfico usa `<rect>` SVG con altura proporcional al valor máximo:

```
bar_height = (value / max_value) × 150px

Para cada severidad:
  <rect x="{x}" y="{180 - height}"
        width="60" height="{height}"
        fill="{color}" rx="4"/>
```

El gráfico no se genera si no hay violaciones (`total == 0`).

---

## 8. Agrupación de Violaciones por Checker

Las violaciones se agrupan por checker de origen usando un mapeo estático:

```
_CHECKER_NAMES (ViolationType → nombre de checker):

  ADAPTATION_IN_DEFINITION  ──► DefinitionChecker — Separación de capas
  MISSING_LAYER_STRUCTURE   ──► StructureChecker — Estructura del proyecto
  ASSERTION_IN_POM          ──► AdaptationChecker — Page Objects
  FORBIDDEN_IMPORT          ──► AdaptationChecker — Page Objects
  BUSINESS_LOGIC_IN_POM     ──► AdaptationChecker — Page Objects
  DUPLICATE_LOCATOR         ──► AdaptationChecker — Page Objects
  HARDCODED_TEST_DATA       ──► QualityChecker — Calidad de tests
  LONG_TEST_FUNCTION        ──► QualityChecker — Calidad de tests
  POOR_TEST_NAMING          ──► QualityChecker — Calidad de tests
```

El orden de presentación sigue `_CHECKER_ORDER`:

```
1. StructureChecker — Estructura del proyecto
2. DefinitionChecker — Separación de capas
3. AdaptationChecker — Page Objects
4. QualityChecker — Calidad de tests
```

Dentro de cada grupo, las violaciones se ordenan por severidad (CRITICAL primero) y luego por fichero.

### Tabla de Violaciones (5 columnas)

| Columna | Ancho | Contenido |
|---------|-------|-----------|
| Severidad | 90px | Badge con color |
| Tipo | 240px | Nombre + descripción legible |
| Ubicación | 160px | Ruta relativa:línea |
| Detalle | auto | Mensaje + snippet de código |
| Recomendación | 280px | Sugerencia de corrección |

---

## 9. Integración con el CLI

Los flags se añadieron al CLI existente sin modificar la salida de texto:

```python
@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True)
@click.option('--json', 'json_path', type=click.Path(), default=None)
@click.option('--html', 'html_path', type=click.Path(), default=None)
def main(project_path, verbose, json_path, html_path):
    ...
    report = analyzer.analyze()

    # Salida de texto (siempre)
    ...

    # Exportación condicional
    if json_path:
        JsonReporter().generate(report, Path(json_path))
    if html_path:
        HtmlReporter().generate(report, Path(html_path))
```

**Decisión:** `--json` y `--html` aceptan una ruta como argumento (no son flags booleanos). Esto permite al usuario elegir el nombre y ubicación del fichero de salida.

---

## 10. Mapa de Tests

### Tests Unitarios (21 tests)

```
tests/unit/
├── test_json_reporter.py    ← 7 tests
│   ├── test_genera_fichero_json_valido
│   ├── test_estructura_metadata
│   ├── test_estructura_summary
│   ├── test_estructura_violations
│   ├── test_report_sin_violaciones
│   ├── test_encoding_utf8
│   └── test_json_indentado
│
└── test_html_reporter.py    ← 14 tests
    ├── test_genera_fichero_html
    ├── test_contiene_nombre_proyecto
    ├── test_contiene_score
    ├── test_contiene_svg_gauge
    ├── test_contiene_conteo_severidades
    ├── test_contiene_tabla_violaciones
    ├── test_contiene_grafico_barras
    ├── test_report_sin_violaciones
    ├── test_sin_violaciones_no_chart
    ├── test_score_excelente_label
    ├── test_score_problemas_criticos_label
    ├── test_contiene_footer
    ├── test_html_responsive
    └── test_escapa_html_en_contenido      ← XSS prevention
```

### Tests de Integración (4 tests)

```
tests/integration/
└── test_reporters.py        ← 4 tests
    ├── TestJsonReporterIntegration
    │   ├── test_bad_project_json    ← Pipeline: análisis → JSON
    │   └── test_good_project_json
    └── TestHtmlReporterIntegration
        ├── test_bad_project_html    ← Pipeline: análisis → HTML
        └── test_good_project_html
```

### Cobertura de seguridad

El test `test_escapa_html_en_contenido` verifica que el reporter escapa caracteres HTML para prevenir XSS:

```python
# Input malicioso
report.project_path = "test<script>alert(1)</script>"
violation.message = '<script>alert("xss")</script>'

# Verificación
assert "<script>" not in content         # No se inyecta HTML
assert "&lt;script&gt;" in content       # Se escapa correctamente
```

Todos los campos de usuario se procesan con `html.escape()` antes de insertarlos en el HTML.

---

*Última actualización: 29 de enero de 2026*
