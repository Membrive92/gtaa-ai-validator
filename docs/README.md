# Documentación del Proyecto gTAA AI Validator

Este directorio contiene documentación técnica detallada sobre el proyecto.

## Documentos Disponibles

### [PHASE1_FLOW_DIAGRAMS.md](PHASE1_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 1: Fundación del Proyecto y CLI.

**Contenido**:
- Estructura del proyecto y paquete Python
- Flujo del CLI con Click (`__main__.py`)
- Descubrimiento recursivo de archivos con exclusiones
- Diagrama de interacción entre componentes
- Decisiones de diseño de la Fase 1 (Click, estructura anticipada)

**Conceptos explicados**:
- Click como framework CLI declarativo
- Descubrimiento de archivos con `rglob` y filtrado
- Estructura de paquete Python ejecutable (`__main__.py`)

### [PHASE2_FLOW_DIAGRAMS.md](PHASE2_FLOW_DIAGRAMS.md)

Diagramas de flujo completos que explican el funcionamiento de la Fase 2: Motor de Análisis Estático.

**Contenido**:
- Diagrama de flujo principal (vista general)
- Subdiagrama: DefinitionChecker.check() - El corazón del análisis
- Subdiagrama: BrowserAPICallVisitor - Recorrido del AST
- Subdiagrama: _get_object_name() - Extraer nombre del objeto
- Subdiagrama: Creación de Violation
- Subdiagrama: Cálculo de Score
- Diagrama de datos - Transformación de estructuras
- Diagrama de interacción entre clases
- Ejemplo concreto paso a paso

**Para quién**:
- Desarrolladores que quieran entender el código
- Evaluadores del TFM
- Estudiantes aprendiendo sobre AST y análisis estático
- Colaboradores del proyecto

**Conceptos explicados**:
- AST (Abstract Syntax Tree)
- Visitor Pattern
- Strategy Pattern
- Facade Pattern
- Dataclasses en Python

### [PHASE3_FLOW_DIAGRAMS.md](PHASE3_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 3: Cobertura Completa de Análisis Estático (9 tipos de violaciones).

**Contenido**:
- Visión general de la arquitectura con 4 checkers (5 desde Fase 8)
- Flujo principal actualizado con project-level checks
- Check a dos niveles: proyecto vs archivo
- StructureChecker — validación de estructura de directorios
- AdaptationChecker — 4 sub-checks con AST visitors
- QualityChecker — datos hardcoded, funciones largas, naming
- Mapa completo de AST Visitors (4 visitors)
- Flujo de detección de locators duplicados (estado cross-file)
- Mapa de las 9 violaciones con técnicas de detección
- Diagrama de interacción/secuencia entre componentes

**Conceptos nuevos explicados**:
- check_project() — checks a nivel de proyecto
- Cross-file state (locator registry)
- Regex + AST combinados para detección de datos
- Múltiples visitors especializados por tipo de violación

### [PHASE4_FLOW_DIAGRAMS.md](PHASE4_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 4: Reportes HTML/JSON Profesionales.

**Contenido**:
- Arquitectura del módulo de reportes (`reporters/`)
- Flujo de generación de reportes (JSON y HTML)
- JsonReporter — serialización con `to_dict()` + `json.dumps()`
- HtmlReporter — dashboard visual autocontenido
- Estructura del dashboard HTML (secciones, tarjetas, tablas)
- SVG inline: gauge circular de score y gráfico de barras
- Agrupación de violaciones por checker
- Integración con el CLI (`--json`, `--html`)
- Mapa completo de tests (21 unitarios + 4 integración)

**Conceptos nuevos explicados**:
- SVG programático (stroke-dasharray para gauges)
- HTML autocontenido sin dependencias externas
- Prevención XSS con `html.escape()`
- CSS Grid responsive para dashboard

### [PHASE5_FLOW_DIAGRAMS.md](PHASE5_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 5: Análisis Semántico con Inteligencia Artificial.

**Contenido**:
- Arquitectura del módulo LLM (`llm/`)
- Flujo de selección de cliente LLM (Gemini vs Mock)
- GeminiLLMClient — comunicación con Gemini Flash API
- MockLLMClient — heurísticas deterministas (AST + regex)
- Prompt engineering: system prompt, analyze prompt, enrich prompt
- SemanticAnalyzer — orquestación de las dos fases
- Fase 1: detección de violaciones semánticas
- Fase 2: enriquecimiento con sugerencias AI contextuales
- Parsing robusto de respuestas LLM (JSON, markdown, errores)
- Mapa de 13 violaciones de Fase 5 (9 estáticas + 4 semánticas)
- Configuración de API key con .env y python-dotenv
- Mapa de tests (12 tests unitarios para GeminiLLMClient)

**Conceptos nuevos explicados**:
- LLM como herramienta de análisis de código
- Prompt engineering para detección de violaciones
- Duck typing como alternativa a ABC
- Manejo silencioso de errores de API (degradación elegante)
- google-genai SDK nativo
- Configuración por variable de entorno con .env

### [PHASE6_FLOW_DIAGRAMS.md](PHASE6_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 6: Ampliación de Cobertura de Violaciones (13 → 18).

**Contenido**:
- 5 nuevas violaciones basadas en catálogo ISTQB CT-TAE
- 3 violaciones estáticas nuevas en QualityChecker (AST + regex)
- 2 violaciones semánticas nuevas (LLM + MockLLM)
- Ampliación del MockLLMClient con 2 heurísticas
- Ampliación del GeminiLLMClient (VALID_TYPES) y prompts
- Mapa completo de 18 violaciones por capa gTAA
- Mapa de 25 tests nuevos (234 total)
- Consideraciones sobre falsos positivos (Playwright, API testing)

**Conceptos nuevos explicados**:
- Detección de excepciones genéricas con ast.ExceptHandler
- Regex compiladas como constantes de clase
- Detección de estado mutable a dos niveles (módulo + global)
- Ampliación de prompts LLM vs prompts separados
- Análisis de falsos positivos por framework

### [PHASE7_FLOW_DIAGRAMS.md](PHASE7_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 7: Soporte para proyectos mixtos (API + UI testing).

**Contenido**:
- FileClassifier: clasificación de archivos por scoring (imports AST, código regex, path)
- ClassificationResult y detección automática de frameworks (Playwright auto-wait)
- ProjectConfig y configuración .gtaa.yaml por proyecto
- Integración en StaticAnalyzer (file_type en checkers)
- Integración en SemanticAnalyzer (has_auto_wait en LLM)
- Auto-wait de Playwright: detección automática vs YAML manual
- CLI: opción --config
- Mapa de violaciones filtradas por file_type
- Mapa de 40 tests nuevos (234 → 274)
- 6 decisiones arquitectónicas (ADR 22-27)

**Conceptos nuevos explicados**:
- Clasificación per-file vs per-project
- Scoring ponderado con tres señales (imports, código, path)
- Regla conservadora: UI siempre gana en archivos mixtos
- Detección automática de auto-wait vs configuración manual
- Degradación elegante de configuración YAML
- .gtaa.yaml vs .env para configuración de reglas

### [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md)

Registro de decisiones arquitectónicas (ADR) que explica **por qué** se eligió cada enfoque técnico.

**Contenido**:
1. Análisis de código: AST frente a alternativas (mapas anidados, regex)
2. Recorrido del AST: Patrón Visitor
3. Organización de checkers: Patrón Strategy (interfaz uniforme, justificación)
4. Orquestación: Patrón Facade (StaticAnalyzer)
5. Modelos de datos: Dataclasses y Enums
6. Verificación a dos niveles (proyecto + archivo)
7. Optimización: parseo único del AST por archivo
8. Paradigmas de programación utilizados (POO + Declarativo)
9. Reportes: HTML autocontenido frente a alternativas (Jinja2, Chart.js, PDF)
10. Reportes: JSON con serialización propia frente a librerías (Pydantic, marshmallow)
11. CLI: flags separados frente a formato único
12. LLM: Evaluación de APIs y modelos LLM (Claude, GPT-4o, DeepSeek, Gemini, Llama)
13. LLM: SDK google-genai frente a alternativas (openai, REST)
14. LLM: Duck typing frente a clase base abstracta
15. LLM: Manejo silencioso de errores de API
16. LLM: Configuración por variable de entorno frente a alternativas
17. Detección de excepciones genéricas: AST frente a regex
18. Detección de configuración hardcodeada: regex compiladas como constantes de clase
19. Detección de estado mutable compartido: dos fases complementarias
20. Ampliación de violaciones semánticas: prompts ampliados frente a prompts separados
21. Heurísticas mock: búsqueda textual frente a visitor AST para detección de asserts
22. Clasificación a nivel de archivo vs proyecto
23. Scoring ponderado para clasificación
24. UI siempre gana en archivos mixtos
25. Auto-wait automático vs solo YAML
26. .gtaa.yaml vs .env para configuración de reglas
27. PyYAML con degradación elegante
28. Parser Gherkin: regex frente a dependencia externa
29. Herencia de keywords And/But para detección de Then
30. Detección de step definitions: path frente a AST
31. Detección de step patterns duplicados: check_project cross-file
32. Patrones de detalle de implementación en Gherkin
33. Multilenguaje: tree-sitter-language-pack frente a parsers separados
34. Checkers language-agnostic frente a checkers por lenguaje (refactor clave)
35. ParseResult como interfaz unificada frente a AST nativo
36. Factory function frente a dispatcher manual para parsers
37. Python AST nativo frente a tree-sitter para Python
38. Factory pattern para creación de clientes LLM
39. RateLimitError como excepción específica
40. Fallback automático ante rate limit (Gemini → Mock)
41. --max-llm-calls para limitación proactiva de llamadas API
42. Provider tracking en reportes (inicial, actual, fallback)
43. Sistema de logging profesional con logging stdlib
44. --verbose auto-crea log file por defecto
45. Version bump con single source of truth (__init__.__version__)
46. pyproject.toml (PEP 621) con dependencias opcionales
47. Eliminación de código muerto (159 líneas)
48. Eliminación de ast.Str deprecado (Python 3.14 compatibility)
49. Alineación LSP: BaseChecker.check() acepta Union[ast.Module, ParseResult]
50. PEP 8 E402: logger después de imports
51. Consistencia de docstrings en español
52. Dockerfile multistage (builder + runtime)
53. GitHub Actions CI con matrix Python 3.10/3.11/3.12
54. GitHub Action reutilizable (action.yml) composite action
55. Eliminación de código muerto segunda pasada (body_node, _analyze_imports)
56. BaseChecker: métodos compartidos (_is_test_file, _is_test_function)
57. LLMClientProtocol con typing.Protocol
58. TokenUsage unificado entre Mock y API clients
59. _call_with_fallback() como helper compartido
60. Decomposición CLI: main() de 200 a 40 líneas

**Para quién**:
- Evaluadores del TFM que quieran entender las decisiones de diseño
- Desarrolladores que consideren alternativas
- Estudiantes aprendiendo sobre patrones de diseño aplicados

---

## Flujo End-to-End (E2E) del Validador

Este diagrama muestra el flujo completo desde la invocación del CLI hasta la generación del reporte.

### Diagrama de Flujo Principal (Estilo Secuencia)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              gtaa-validator proyecto/ --ai                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 1   __main__.py → CLI (click)                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│     @click.command()                                                                │
│     def main(project_path, verbose, json_path, html_path, ai,                     │
│              provider, config_path, max_llm_calls, log_file, ...):                 │
│         config = load_config(...)                                                  │
│         analyzer = StaticAnalyzer(project_path, verbose, config) ────────────┐    │
│         report = analyzer.analyze() ──────────────────────────────────────┐   │    │
│                                                                           │   │    │
│         if ai:  # --ai flag                                               │   │    │
│             llm_client = create_llm_client(provider) ───────────────┐    │   │    │
│             semantic = SemanticAnalyzer(path, llm_client, verbose,  │    │   │    │
│                                        max_llm_calls)              │    │   │    │
│             report = semantic.analyze(report) ───────────────────┐   │    │   │    │
│                                                                  │   │    │   │    │
│         reporter.generate(report) ──────────────────────────┐    │   │    │   │    │
│                                                             │    │   │    │   │    │
└─────────────────────────────────────────────────────────────│────│───│────│───│────┘
                                                              │    │   │    │   │
                          ┌───────────────────────────────────┘    │   │    │   │
                          │    ┌───────────────────────────────────┘   │    │   │
                          │    │    ┌──────────────────────────────────┘    │   │
                          │    │    │    ┌──────────────────────────────────┘   │
                          │    │    │    │                                      │
                          ▼    │    │    │                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 2   StaticAnalyzer.analyze()                                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│     def analyze(self):                                                              │
│         │                                                                           │
│         │  # 2a. Verificaciones a nivel proyecto                             │     │
│         │  for checker in self.checkers:                                     │     │
│         │      violations += checker.check_project(path) ─────────────┐      │     │
│         │  # StructureChecker: ¿existe /tests y /pages?               │      │     │
│         │                                                             │      │     │
│         │  # 2b. Descubrir archivos                                   │      │     │
│         │  files = self._discover_python_files() ────────────────────────────┐     │
│         │  # Busca: *.py, *.java, *.js/ts/jsx/tsx/mjs/cjs, *.cs, *.feature   │     │
│         │                                                             │      │     │
│         │  # 2c. Verificar cada archivo                               │      │     │
│         │  for file in files:                                         │      │     │
│         │      violations += self._check_file(file) ─────────────┐    │      │     │
│         │                                                        │    │      │     │
│         │  # 2d. Calcular score                                  │    │      │     │
│         │  report.calculate_score() ────────────────────────┐    │    │      │     │
│         │  return report                                    │    │    │      │     │
│         │                                                   │    │    │      │     │
└─────────│───────────────────────────────────────────────────│────│────│──────│─────┘
          │                                                   │    │    │      │
          │                          ┌────────────────────────┘    │    │      │
          │                          │    ┌────────────────────────┘    │      │
          │                          │    │                             │      │
          │                          ▼    ▼                             │      │
          │   ┌───────────────────────────────────────────────────┐    │      │
          │   │ Report.calculate_score()                          │    │      │
          │   │   score = 100 - Σ(penalties)                      │    │      │
          │   │   CRITICAL=-10, HIGH=-5, MEDIUM=-2, LOW=-1         │    │      │
          │   └───────────────────────────────────────────────────┘    │      │
          │                                                            │      │
          ▼                                                            ▼      │
┌─────────────────────────────────────────────────────────────────────────────│─────┐
│ 2c  _check_file(file_path)                                                  │     │
├─────────────────────────────────────────────────────────────────────────────│─────┤
│                                                                             │     │
│     # Seleccionar checker por extensión                                     │     │
│     applicable = [c for c in checkers if c.can_check(file)] ───────────┐    │     │
│                                                                        │    │     │
│     ┌──────────────────────────────────────────────────────────────────│────│─────┤
│     │  .py/.java/.js/.ts/.cs → DefinitionChecker, AdaptationChecker,  │    │     │
│     │                          QualityChecker (language-agnostic)      │    │     │
│     │  .py      → + StructureChecker (proyecto)                        │    │     │
│     │  .feature → BDDChecker                                           │    │     │
│     └──────────────────────────────────────────────────────────────────│────│─────┤
│                                                                        │    │     │
│     # Parsear con el parser apropiado al lenguaje                      │    │     │
│     parser = get_parser_for_file(file_path) ──────────────────────┐    │    │     │
│     parse_result = parser.parse(source) ──────────────────────┐   │    │    │     │
│     # ParseResult unificado para todos los lenguajes          │   │    │    │     │
│                                                               │   │    │    │     │
│     # Clasificar archivo                                      │   │    │    │     │
│     file_type = classifier.classify_detailed(file,            │   │    │    │     │
│                     source, parse_result) ─────────────────┐  │   │    │    │     │
│     # file_type = "ui" | "api" | "page_object" | "unknown"  │  │   │    │    │     │
│                                                            │  │   │    │    │     │
│     # Ejecutar checkers aplicables                         │  │   │    │    │     │
│     for checker in applicable:                             │  │   │    │    │     │
│         violations += checker.check(file, parse_result,    │  │   │    │    │     │
│                                     file_type) ────────────│──│───│────│──┐ │     │
│                                                            │  │   │    │  │ │     │
└────────────────────────────────────────────────────────────│──│───│────│──│─│─────┘
                                                             │  │   │    │  │ │
                 ┌───────────────────────────────────────────┘  │   │    │  │ │
                 │           ┌───────────────────────────────────┘   │    │  │ │
                 │           │                                       │    │  │ │
                 ▼           ▼                                       │    │  │ │
┌─────────────────────────────────────────────────────────────────┐  │    │  │ │
│  FileClassifier.classify_detailed()                             │  │    │  │ │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │    │  │ │
│    │ Análisis    │  │ Análisis    │  │ Análisis    │          │  │    │  │ │
│    │ de imports  │ +│ de código   │ +│ de path     │          │  │    │  │ │
│    │ (ParseResult│  │ (regex)     │  │ (heurístico)│          │  │    │  │ │
│    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │  │    │  │ │
│           └────────────────┼────────────────┘                  │  │    │  │ │
│                            ▼                                   │  │    │  │ │
│           file_type = "ui" | "api" | "page_object" | "unknown" │  │    │  │ │
└─────────────────────────────────────────────────────────────────┘  │    │  │ │
                                                                         │    │  │
                                                                         │    │  │
                 ┌───────────────────────────────────────────────────────┘    │  │
                 │                                                            │  │
                 ▼                                                            ▼  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  checker.check(file_path, parse_result, file_type) → Violation[]                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌───────────────────────────────────────────────────┐  ┌──────────────────────────┐ │
│  │ Checkers LANGUAGE-AGNOSTIC                        │  │ BDD Checker              │ │
│  │ (DefinitionChecker, AdaptationChecker, Quality)   │  │                          │ │
│  │                                                   │  │ Valida .feature + steps: │ │
│  │ Reciben ParseResult unificado de cualquier parser │  │                          │ │
│  │                                                   │  │ - GHERKIN_IMPL_DETAIL    │ │
│  │ Detectan por extensión:                           │  │ - STEP_BROWSER_CALL      │ │
│  │   .py    → BROWSER_METHODS_PYTHON                 │  │ - STEP_TOO_COMPLEX       │ │
│  │   .java  → BROWSER_METHODS_JAVA                   │  │ - MISSING_THEN_STEP      │ │
│  │   .js/.ts → BROWSER_METHODS_JS                    │  │ - DUPLICATE_STEP_PAT     │ │
│  │   .cs    → BROWSER_METHODS_CSHARP                 │  │                          │ │
│  │                                                   │  │                          │ │
│  │ Mismas violaciones para todos los lenguajes       │  │                          │ │
│  └───────────────────────────────────────────────────┘  └──────────────────────────┘ │
│                                                                                     │
└──────────────────────────────────────────────────────────────────────────────│──────┘
                                                                               │
                                         ┌─────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 3   SemanticAnalyzer.analyze(report) — Solo si --ai                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│     # Análisis SELECTIVO (Fase 10): solo archivos con violaciones o sospechosos    │
│     candidates = _filter_candidate_files(all_files, files_with_violations)          │
│                                                                                     │
│     for file in candidates:  # Solo candidatos, no todos                           │
│         │                                                                           │
│         │  # Fase 1: Detectar violaciones semánticas                               │
│         │  _check_call_limit()  # Fallback a Mock si se excede --max-llm-calls     │
│         │  new_violations = _call_with_fallback(                                   │
│         │      "analyze_file", content, file_str) ─────────────────────────┐      │
│         │  # UNCLEAR_TEST_PURPOSE, MISSING_WAIT_STRATEGY...                │      │
│         │                                                                  │      │
│     # Fase 2: Enriquecer violaciones existentes con sugerencias AI         │      │
│     for violation in report.violations:                                    │      │
│         │  _check_call_limit()                                             │      │
│         │  suggestion = _call_with_fallback(                               │      │
│         │      "enrich_violation", v.to_dict(), content) ────────────┐     │      │
│         │  violation.ai_suggestion = suggestion                      │     │      │
│                                                                      │     │      │
└──────────────────────────────────────────────────────────────────────│─────│──────┘
                                                                          │    │
                          ┌───────────────────────────────────────────────┘    │
                          │    ┌───────────────────────────────────────────────┘
                          │    │
                          ▼    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LLMClient (APILLMClient | MockLLMClient) — creado por create_llm_client()         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────────────┐│
│  │ APILLMClient                    │    │ MockLLMClient                           ││
│  │                                 │    │                                         ││
│  │ API: Gemini 2.5 Flash Lite      │    │ Heurísticas deterministas               ││
│  │ Prompt engineering para         │    │ (regex + AST patterns)                  ││
│  │ detección de violaciones        │    │                                         ││
│  │                                 │    │ Para testing sin API key               ││
│  │ Fallback automático a Mock      │    │                                         ││
│  │ si rate limit (429)             │    │                                         ││
│  └─────────────────────────────────┘    └─────────────────────────────────────────┘│
│                                                                                     │
└──────────────────────────────────────────────────────────────────────────────│──────┘
                                                                               │
                                         ┌─────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 4   Reporter.generate(report)                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│     │ CLI (stdout)    │    │ JsonReporter    │    │ HtmlReporter    │              │
│     │ (siempre)       │    │ --json file.json│    │ --html file.html│              │
│     │                 │    │                 │    │                 │              │
│     │ click.echo()    │    │ → file.json     │    │ → file.html     │              │
│     │ _display_results│    │                 │    │   (dashboard    │              │
│     │                 │    │ {               │    │    con gauge    │              │
│     │ Score: 75/100   │    │   "score": 75,  │    │    SVG)         │              │
│     │ Violations: 12  │    │   "violations": │    │                 │              │
│     │ - ADAPTATION... │    │     [...]       │    │                 │              │
│     │ - HARDCODED...  │    │ }               │    │                 │              │
│     └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Selección de Parser por Lenguaje (Arquitectura Refactorizada)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SELECCIÓN DE PARSER POR EXTENSIÓN                      │
│                    (Factory Function: get_parser_for_file)                │
└───────────────────────────────────────────────────────────────────────────┘

  archivo.ext
       │
       ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    ¿Cuál es la extensión?                              │
  └────────────────────────────────────────────────────────────────────────┘
       │
       ├── .py ──────────────► PythonParser (ast nativo)
       │                              │
       ├── .java ────────────► JavaParser (tree-sitter)
       │                              │
       ├── .js/.ts/.tsx/.jsx/.mjs/.cjs ► JSParser (tree-sitter)
       │                              │
       ├── .cs ──────────────► CSharpParser (tree-sitter)
       │                              │
       └── .feature ─────────► GherkinParser (regex propio)
                                      │   (usado directamente por BDDChecker,
                                      │    no pasa por get_parser_for_file)
                                      │
       Todos los parsers producen:    │
                                      ▼
                              ┌────────────────┐
                              │  ParseResult   │ ◄── Interfaz unificada
                              │  - imports     │
                              │  - classes     │
                              │  - functions   │
                              │  - calls       │
                              │  - strings     │
                              │  - language    │
                              │  - parse_errors│
                              └───────┬────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │   CHECKERS LANGUAGE-AGNOSTIC        │
                    │   (mismos checkers para TODOS)      │
                    ├─────────────────────────────────────┤
                    │ • DefinitionChecker                 │
                    │     ADAPTATION_IN_DEFINITION        │
                    │                                     │
                    │ • AdaptationChecker                 │
                    │     ASSERTION_IN_POM                │
                    │     FORBIDDEN_IMPORT                │
                    │     BUSINESS_LOGIC_IN_POM           │
                    │                                     │
                    │ • QualityChecker                    │
                    │     HARDCODED_TEST_DATA             │
                    │     LONG_TEST_FUNCTION              │
                    │     POOR_TEST_NAMING                │
                    │                                     │
                    │ • StructureChecker (solo proyecto)  │
                    │                                     │
                    │ • BDDChecker (solo .feature)        │
                    └─────────────────────────────────────┘

  Ventajas de esta arquitectura:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ ✓ DRY: lógica de detección en UN lugar, patrones por extensión         │
  │ ✓ Consistencia: mismos algoritmos para todos los lenguajes             │
  │ ✓ Mantenibilidad: añadir violación = modificar 1 archivo               │
  │ ✓ Extensibilidad: añadir lenguaje = nuevo parser + entradas en dicts   │
  └─────────────────────────────────────────────────────────────────────────┘
```

### Ejemplo Concreto: Proyecto Java

```
┌───────────────────────────────────────────────────────────────────────────┐
│          EJEMPLO: ANÁLISIS DE LoginTest.java                              │
└───────────────────────────────────────────────────────────────────────────┘

  Archivo: LoginTest.java
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  @Test                                                                  │
  │  public void test1() {                    ◄── POOR_TEST_NAMING          │
  │      driver.get("https://example.com");   ◄── HARDCODED_TEST_DATA       │
  │      driver.findElement(By.id("user"))    ◄── ADAPTATION_IN_DEFINITION  │
  │          .sendKeys("admin@test.com");     ◄── HARDCODED_TEST_DATA       │
  │  }                                                                      │
  └─────────────────────────────────────────────────────────────────────────┘

  Flujo de análisis (ARQUITECTURA LANGUAGE-AGNOSTIC):
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  1. StaticAnalyzer._discover_python_files()                              │
  │     └── Encuentra LoginTest.java (extensión .java soportada)            │
  │                                                                         │
  │  2. StaticAnalyzer._check_file(LoginTest.java)                          │
  │     │                                                                   │
  │     ├── 2a. get_parser_for_file(".java") → JavaParser                   │
  │     │                                                                   │
  │     ├── 2b. JavaParser.parse(source) → ParseResult                      │
  │     │       └── tree-sitter parsea a AST                                │
  │     │       └── Extrae: imports, classes, functions, calls, strings     │
  │     │                                                                   │
  │     ├── 2c. Selección de checkers aplicables                            │
  │     │       └── DefinitionChecker.can_check(".java") → True             │
  │     │       └── AdaptationChecker.can_check(".java") → True             │
  │     │       └── QualityChecker.can_check(".java") → True                │
  │     │                                                                   │
  │     └── 2d. Cada checker recibe ParseResult y extensión:                │
  │             │                                                           │
  │             ├── DefinitionChecker.check(file_path, parse_result,        │
  │             │                           file_type="unknown")           │
  │             │   └── Usa BROWSER_METHODS_JAVA = {"findElement", "get"..} │
  │             │   └── Encuentra driver.get(), driver.findElement()        │
  │             │   └── Dentro de método @Test → ADAPTATION_IN_DEFINITION   │
  │             │                                                           │
  │             ├── QualityChecker.check(file_path, parse_result,           │
  │             │                        file_type="unknown")              │
  │             │   └── _check_hardcoded_data() con patrones universales    │
  │             │   └── Detecta "https://..." y "admin@test.com"            │
  │             │   └── → 2× HARDCODED_TEST_DATA                            │
  │             │   │                                                       │
  │             │   └── _check_poor_naming() con GENERIC_NAME_PATTERNS_JAVA │
  │             │   └── Método "test1" coincide con patrón genérico         │
  │             │   └── → POOR_TEST_NAMING                                  │
  │             │                                                           │
  │             └── AdaptationChecker.check(file_path, parse_result,        │
  │                                         file_type="unknown")           │
  │                 └── No detecta violaciones adicionales en este archivo  │
  │                                                                         │
  │  3. Resultado: 4 violaciones detectadas                                 │
  └─────────────────────────────────────────────────────────────────────────┘
```

**Ventaja de la arquitectura language-agnostic**: Los mismos 3 checkers
(DefinitionChecker, AdaptationChecker, QualityChecker) funcionan para Python,
Java, JavaScript/TypeScript y C#. La única diferencia son los patrones específicos
por lenguaje almacenados en diccionarios (BROWSER_METHODS_JAVA, BROWSER_METHODS_JS, etc.).

### Tecnologías de Parsing por Lenguaje

| Lenguaje | Librería de Parsing | Versión Python |
|----------|---------------------|----------------|
| Python | `ast` (stdlib) | 3.10+ |
| Java | `tree-sitter-language-pack` | 3.10+ |
| JavaScript/TypeScript | `tree-sitter-language-pack` | 3.10+ |
| C# | `tree-sitter-c-sharp` | 3.10+ |
| Gherkin | regex propio (sin dependencias) | 3.10+ |

---

### [PHASE8_FLOW_DIAGRAMS.md](PHASE8_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 8: Soporte Gherkin/BDD (Behave + pytest-bdd).

**Contenido**:
- BDDChecker — validación de archivos .feature y step definitions
- Detección de detalles de implementación en Gherkin
- Validación de estructura Given-When-Then
- Integración con step definitions Python (Behave/pytest-bdd)
- 5 tipos de violaciones BDD

**Conceptos nuevos explicados**:
- Gherkin parser (regex propio, sin dependencias externas)
- Validación de estructura Given-When-Then
- Tags para categorización de escenarios

### [PHASE9_FLOW_DIAGRAMS.md](PHASE9_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 9: Soporte Multilenguaje (Java + JavaScript/TypeScript + C#).

**Contenido**:
- tree-sitter como parser unificado para Java, JS/TS y C#
- Parsers específicos: JavaParser, JSParser, CSharpParser, PythonParser
- ParseResult como interfaz unificada entre parsers y checkers
- Checkers language-agnostic que trabajan con ParseResult
- Factory function `get_parser_for_file()` para selección automática
- Ejemplos multilenguaje

**Conceptos nuevos explicados**:
- tree-sitter-language-pack para parsing multi-lenguaje
- ParseResult como abstracción que desacopla parsers de checkers
- Principio DRY aplicado: mismos checkers para todos los lenguajes
- Patrones específicos por extensión (.py, .java, .js, .cs) en diccionarios
- Dependency Inversion: checkers dependen de ParseResult, no de parsers concretos

### [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md)

Auditoría de seguridad del código fuente del proyecto (Fase 10.4).

**Contenido**:
- 9 hallazgos de seguridad clasificados por severidad (2 críticos, 4 altos, 3 medios)
- Análisis detallado por hallazgo: código afectado, vector de ataque, riesgo, recomendación
- Clasificación OWASP Top 10 y estándares de seguridad
- Buenas prácticas de seguridad ya implementadas (XSS prevention, safe YAML, env vars)
- Matriz de riesgo (probabilidad vs impacto)
- Tabla resumen y prioridad de remediación

**Categorías auditadas**:
- Inyección de comandos (shell, code injection)
- Path traversal y divulgación de información
- Gestión de secretos y API keys
- Denegación de servicio (DoS, ReDoS)
- Cross-Site Scripting (XSS) en reportes HTML
- Seguridad de contenedores Docker
- Supply chain en GitHub Actions

### [TEST_AUDIT_REPORT.md](TEST_AUDIT_REPORT.md)

Auditoría QA white-box de la suite de tests (Fase 10.9).

**Contenido**:
- Inventario completo de 670 tests pre-auditoría
- 11 tests redundantes/muertos identificados y eliminados
- 8 funciones con zero cobertura (críticas para el negocio)
- Plan de corrección priorizado: ~86 tests nuevos
- 40+ aserciones débiles documentadas para reforzar
- Resultados post-implementación: 761 tests, 0 fallos

### [DOC_AUDIT_REPORT.md](DOC_AUDIT_REPORT.md)

Auditoría de documentación del proyecto (Fase 10.10).

**Contenido**:
- 51 hallazgos: 16 críticos, 15 altos, 16 medios, 4 bajos
- 6 pasadas de auditoría (primera a sexta) con verificación cruzada contra código fuente
- Errores factuales: fórmula de scoring, tipos BDD inexistentes, parser mal identificado
- Datos desactualizados post Fase 10.9: test count, ADR count, badges
- Inconsistencias menores: naming, conteos, fechas
- Sexta pasada: auditoría cruzada de los propios informes de auditoría/UAT

### [UAT_TESTING_REPORT.md](UAT_TESTING_REPORT.md)

Informe de pruebas de aceptación (UAT) del proyecto.

**Contenido**:
- 5 métodos de despliegue verificados (pip editable, pip clean venv, pip remoto, Docker, GitHub Action)
- Validación con 6 proyectos sintéticos + 2 open-source Java + 3 empresariales reales
- 7 hallazgos funcionales: UAT-01 a UAT-04, UAT-06, UAT-07 (resueltos) + UAT-05 (limitación conocida)
- Detalle de violaciones por tipo de proyecto (bad_project: 58 violaciones, 12 tipos)
- Resumen de auditoría de documentación (51 hallazgos, todos corregidos)
- Validación empresarial: Selenium multi-módulo Java, Playwright JS/TS, Appium Java desktop

---

---

## Cómo Usar Esta Documentación

### Para Aprender
1. Lee [PHASE1_FLOW_DIAGRAMS.md](PHASE1_FLOW_DIAGRAMS.md) para entender la estructura base y el CLI
2. Lee [PHASE2_FLOW_DIAGRAMS.md](PHASE2_FLOW_DIAGRAMS.md) para entender el motor de análisis estático
3. Lee [PHASE3_FLOW_DIAGRAMS.md](PHASE3_FLOW_DIAGRAMS.md) para la cobertura completa de 9 violaciones
4. Lee [PHASE4_FLOW_DIAGRAMS.md](PHASE4_FLOW_DIAGRAMS.md) para los reportes HTML/JSON
5. Lee [PHASE5_FLOW_DIAGRAMS.md](PHASE5_FLOW_DIAGRAMS.md) para el análisis semántico con AI
6. Lee [PHASE6_FLOW_DIAGRAMS.md](PHASE6_FLOW_DIAGRAMS.md) para la ampliación a 18 violaciones
7. Lee [PHASE7_FLOW_DIAGRAMS.md](PHASE7_FLOW_DIAGRAMS.md) para el soporte de proyectos mixtos API + UI
8. Lee [PHASE8_FLOW_DIAGRAMS.md](PHASE8_FLOW_DIAGRAMS.md) para el soporte Gherkin/BDD
9. Lee [PHASE9_FLOW_DIAGRAMS.md](PHASE9_FLOW_DIAGRAMS.md) para el soporte multilenguaje (Java, JS/TS, C#)
10. Lee [PHASE10_FLOW_DIAGRAMS.md](PHASE10_FLOW_DIAGRAMS.md) para optimización LLM, logging, packaging y despliegue
11. Lee [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) para la auditoría de seguridad del código
12. Lee [TEST_AUDIT_REPORT.md](TEST_AUDIT_REPORT.md) para la auditoría QA de tests
13. Lee [DOC_AUDIT_REPORT.md](DOC_AUDIT_REPORT.md) para la auditoría de documentación
14. Lee [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) para las justificaciones técnicas (60 ADRs)
15. Ejecuta el código mientras lees:
    - Python: `python -m gtaa_validator examples/bad_project --ai --verbose`
    - Java: `python -m gtaa_validator examples/java_project --verbose`
    - JS/TS: `python -m gtaa_validator examples/js_project --verbose`
    - C#: `python -m gtaa_validator examples/csharp_project --verbose`

### Para Desarrollar
1. Consulta [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) para entender los patrones (Strategy, Visitor, Facade)
2. Consulta los diagramas de interacción entre clases en los documentos de flujo
3. Sigue la misma estructura de `BaseChecker` para añadir nuevos checkers

### Para Evaluar (TFM)
1. Los diagramas demuestran comprensión técnica profunda
2. [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) documenta las decisiones de diseño y sus alternativas evaluadas
3. Muestran aplicación correcta de patrones de diseño y paradigmas
4. Facilitan la reproducibilidad de resultados

---

## Convenciones de Documentación

### Diagramas ASCII
- Usamos diagramas ASCII para compatibilidad universal
- Pueden visualizarse en cualquier editor de texto
- Fáciles de versionar con Git
- No requieren software especializado

### Formato Markdown
- Todo está en Markdown para fácil lectura
- Compatible con GitHub, GitLab, VSCode
- Puede convertirse a PDF/HTML si es necesario

### Enlaces Internos
- Los enlaces apuntan a líneas específicas del código
- Formato: `archivo.py:línea_inicial-línea_final`
- Facilita navegar entre documentación y código

---

## Actualizaciones

Este directorio se actualizará con:
- Diagramas de nuevas fases
- Documentación de nuevas características
- Guías de uso avanzadas
- Ejemplos adicionales

**Última actualización**: 10 Febrero 2026 (Desarrollo y UAT Completos — Pendiente: slides y memoria TFM)
