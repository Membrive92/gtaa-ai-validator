# 🤖 gTAA AI Validator

**Sistema Híbrido de IA para Validación Automática de Arquitectura de Test Automation: Análisis Estático y Semántico con LLMs**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)](https://github.com/Membrive92/gtaa-ai-validator)
[![Fase](https://img.shields.io/badge/fase-10.6%2F10-blue)](https://github.com/Membrive92/gtaa-ai-validator)
[![Progreso](https://img.shields.io/badge/progreso-99%25-green)](https://github.com/Membrive92/gtaa-ai-validator)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](https://github.com/Membrive92/gtaa-ai-validator)
[![Tests](https://img.shields.io/badge/tests-667-brightgreen)](https://github.com/Membrive92/gtaa-ai-validator)
[![CI](https://github.com/Membrive92/gtaa-ai-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/Membrive92/gtaa-ai-validator/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/Membrive92/gtaa-ai-validator/blob/main/Dockerfile)

> **📌 TRABAJO DE FIN DE MÁSTER - EN DESARROLLO INCREMENTAL**
>
> Autor: Jose Antonio Membrive Guillen
> Año: 2025-2026
> **Estado:** Fase 10.6/10 Completa | Última actualización: 6 Febrero 2026

---

## ⚠️ ESTADO DEL PROYECTO

> **IMPORTANTE:** Este README describe la **visión completa** del proyecto TFM.
> El desarrollo sigue una metodología incremental con 10 fases.
> Funcionalidades marcadas con ⏳ están pendientes de implementación.

### 🚀 Estado de Implementación por Fases

| Fase | Componente | Estado | Fecha Completada |
|------|-----------|--------|------------------|
| **✅ Fase 1** | **CLI básico y descubrimiento de archivos** | **COMPLETO** | **26/01/2026** |
| **✅ Fase 2** | **Análisis estático con AST (1 violación)** | **COMPLETO** | **26/01/2026** |
| **✅ Fase 3** | **Cobertura completa (9 tipos de violaciones) + Tests** | **COMPLETO** | **28/01/2026** |
| **✅ Fase 4** | **Reportes HTML/JSON profesionales** | **COMPLETO** | **31/01/2026** |
| **✅ Fase 5** | **Análisis semántico AI (Gemini Flash + Mock)** | **COMPLETO** | **01/02/2026** |
| **✅ Fase 6** | **Ampliación cobertura (18 violaciones) + Documentación** | **COMPLETO** | **01/02/2026** |
| **✅ Fase 7** | **Soporte para proyectos mixtos (API + UI) + auto-wait Playwright** | **COMPLETO** | **02/02/2026** |
| **✅ Fase 8** | **Soporte Gherkin/BDD (Behave + pytest-bdd)** | **COMPLETO** | **03/02/2026** |
| **✅ Fase 9** | **Soporte Multilenguaje (Java + JS/TS + C#) + Refactor language-agnostic** | **COMPLETO** | **04/02/2026** |
| **🔄 Fase 10** | **Optimización y documentación final** | **EN PROGRESO** | — |
| ↳ **✅ 10.1** | Optimización capa LLM (factory, fallback, rate limit, --max-llm-calls) | **COMPLETO** | **05/02/2026** |
| ↳ **✅ 10.2** | Sistema de logging profesional + métricas de rendimiento | **COMPLETO** | **06/02/2026** |
| ↳ **✅ 10.3** | Optimizaciones de proyecto (packaging, dead code, tests, LSP) | **COMPLETO** | **06/02/2026** |
| ↳ **✅ 10.4** | Despliegue: Docker + GitHub Actions CI + reusable action | **COMPLETO** | **06/02/2026** |
| ↳ **✅ 10.5** | Cobertura de código: 84% a 93% (633 tests) | **COMPLETO** | **06/02/2026** |
| ↳ **✅ 10.6** | Tests de regresión de seguridad (34 tests, SEC-01 a SEC-09) | **COMPLETO** | **06/02/2026** |

### 📊 Funcionalidades Implementadas vs Planeadas

| Funcionalidad | Estado | Notas |
|--------------|--------|-------|
| ✅ CLI con Click | Implementado | Acepta ruta de proyecto y opción --verbose |
| ✅ Descubrimiento de archivos test | Implementado | Soporta patrones test_*.py y *_test.py |
| ✅ Validación de entrada | Implementado | Verifica existencia de directorio |
| ✅ Análisis AST de código Python | Implementado | Visitor Pattern + ast.walk |
| ✅ Detección de 23 tipos de violaciones gTAA | Implementado | Fase 2-8 — 5 checkers + LLM |
| ✅ Sistema de scoring (0-100) | Implementado | Penalización por severidad |
| ✅ Proyectos de ejemplo (bueno/malo) | Implementado | En directorio examples/ |
| ✅ Tests unitarios + integración + seguridad (667 tests, 93% coverage) | Implementado | pytest + pytest-cov con unit/ e integration/ |
| ✅ Documentación técnica con diagramas | Implementado | docs/ con flujos Fase 1-10, 55 ADRs |
| ✅ Reportes HTML dashboard | Implementado | Fase 4 — SVG inline, autocontenido |
| ✅ Reportes JSON para CI/CD | Implementado | Fase 4 — `--json` / `--html` |
| ✅ Análisis semántico con LLM | Implementado | Fase 5 — Gemini Flash API + MockLLM fallback |
| ✅ Soporte proyectos mixtos (API + UI) | Implementado | Fase 7 — FileClassifier, .gtaa.yaml, auto-wait Playwright |
| ✅ Soporte Gherkin/BDD (Behave + pytest-bdd) | Implementado | Fase 8 — GherkinParser, BDDChecker, 5 violaciones BDD |
| ✅ Soporte Multilenguaje (Java + JS/TS + C#) | Implementado | Fase 9 — tree-sitter, checkers language-agnostic, ParseResult |
| ✅ Optimización capa LLM | Implementado | Fase 10.1 — Factory, fallback automático, --max-llm-calls |
| ✅ Logging profesional + métricas | Implementado | Fase 10.2 — logging stdlib, AnalysisMetrics, --log-file |
| ✅ Optimizaciones de proyecto | Implementado | Fase 10.3 — pyproject.toml, dead code, tests CLI, LSP |
| ⏳ Documentación TFM final | En progreso | Fase 10 — CI/CD, docs TFM |

**Leyenda:** ✅ Implementado | ⏳ Pendiente

---

## 📖 Descripción General del Proyecto

**gTAA AI Validator** es una herramienta de análisis automático que valida el cumplimiento de la arquitectura **gTAA (Generic Test Automation Architecture)** definida en el estándar **ISTQB CT-TAE (Certified Tester Advanced Level - Test Automation Engineer)**.

### 🎯 Problema que resuelve

En la práctica profesional del aseguramiento de calidad, es habitual encontrar proyectos de test automation que carecen de una arquitectura definida. A lo largo de la experiencia del autor en distintos departamentos de Quality Assurance de diferentes compañías, el denominador común ha sido la ausencia de estructura arquitectónica en los proyectos de automatización: código de test sin separación de capas, localizadores duplicados, lógica de negocio mezclada con interacciones de UI, y datos de prueba hardcodeados directamente en los scripts.

Esta desorganización produce proyectos que se vuelven inmantenibles a medida que crecen en volumen de tests y en áreas de la aplicación bajo prueba, generando una deuda técnica que obliga a refactorizaciones costosas sobre la marcha.

La mayoría de equipos de automatización adoptan patrones de diseño conocidos como **Page Object Model (POM)**, **Page Factory** o **Screenplay**, que proporcionan una estructura inicial para organizar el código. Sin embargo, conforme el proyecto crece en número de tests y en cobertura funcional, es frecuente que el patrón se degrade: los Page Objects acumulan aserciones, los tests acceden directamente al driver, la lógica de negocio se filtra en capas que no le corresponden, y los datos de prueba quedan dispersos en los scripts.

El estándar **ISTQB CT-TAE** define la **gTAA (Generic Test Automation Architecture)**, que constituye precisamente el marco de referencia arquitectónico sobre el que se sustentan estos patrones. La gTAA no reemplaza a POM ni a Screenplay, sino que establece la separación en capas que estos patrones implementan parcialmente. Validar el cumplimiento de la gTAA es, en esencia, verificar que el patrón adoptado se mantiene íntegro a lo largo de la vida del proyecto.

La gTAA organiza el framework de automatización en capas con responsabilidades claramente delimitadas:

```
┌─────────────────────────────────────────────────────────────────┐
│                    gTAA — Arquitectura Genérica                  │
│              (ISTQB CT-TAE, Capítulo 3)                          │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Test Generation Layer                         │  │
│  │  Diseño de casos de test (manual o automatizado)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Test Definition Layer                         │  │
│  │                                                           │  │
│  │  • Definición de test suites y test cases                 │  │
│  │  • Test data, test procedures, test library               │  │
│  │  • Tests de alto y bajo nivel                             │  │
│  │                                                           │  │
│  │  Ejemplo: test_login(), test_checkout()                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Test Execution Layer                          │  │
│  │                                                           │  │
│  │  • Ejecución automática de tests seleccionados            │  │
│  │  • Setup/teardown del SUT y test suites                   │  │
│  │  • Logging, reporting, validación de respuestas           │  │
│  │                                                           │  │
│  │  Ejemplo: pytest runner, fixtures, conftest               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Test Adaptation Layer                         │  │
│  │                                                           │  │
│  │  • Adaptadores para conectar con el SUT                   │  │
│  │  • Interacción vía APIs, protocolos, interfaces UI        │  │
│  │  • Control del test harness                               │  │
│  │                                                           │  │
│  │  Ejemplo: Page Objects (LoginPage, CheckoutPage)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                           │
│                    │   SUT (System   │                           │
│                    │  Under Test)    │                           │
│                    └─────────────────┘                           │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Componentes transversales:                                │  │
│  │  • Project Management                                      │  │
│  │  • Configuration Management                                │  │
│  │  • Test Management                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**El principio fundamental**: cada capa tiene una responsabilidad única. Los tests (Definition) no deben interactuar directamente con el navegador; los Page Objects (Adaptation) no deben contener aserciones ni lógica de negocio. Cuando estas fronteras se violan, el proyecto pierde mantenibilidad.

**El problema concreto**: no existe ninguna herramienta que valide automáticamente si un proyecto de test automation cumple con esta separación de capas. La revisión se realiza manualmente, es subjetiva y no escalable.

**Consecuencias de la falta de arquitectura:**
- Código de test acoplado directamente a Selenium/Playwright (frágil ante cambios de UI)
- Page Objects con aserciones, lógica de negocio e imports de frameworks de test
- Datos de prueba hardcodeados en los scripts (difíciles de parametrizar)
- Tests con nombres genéricos y funciones de cientos de líneas
- Localizadores duplicados entre múltiples Page Objects

### ✨ Solución propuesta

Sistema híbrido que combina **3 técnicas de IA** para detectar automáticamente violaciones arquitectónicas:

1. **🔍 Análisis Estático**: Pattern matching con AST y regex (17 violaciones)
2. **🧠 Análisis Semántico (LLM)**: Gemini Flash para detección profunda (6 violaciones)

### 🏆 Contribuciones Planificadas (TFM)

- 🎯 **Primera herramienta** que valida automáticamente gTAA (objetivo del TFM)
- ✅ **Sistema híbrido** que combina reglas estáticas + IA semántica (implementado Fase 5)
- ✅ **Detecta 23 tipos** de violaciones arquitectónicas (17 estáticas + 6 semánticas)
- ✅ **Reportes visuales** en HTML y JSON para CI/CD (implementado Fase 4)
- ✅ **Cobertura ampliada** con 5 nuevas violaciones basadas en catálogo CT-TAE (Fase 6)

---

## 🛠️ Stack Tecnológico

### Lenguajes y Frameworks
- **Python 3.10+** - Lenguaje principal (requisito tree-sitter)
- **AST (Abstract Syntax Tree)** - Análisis sintáctico de código Python
- **tree-sitter** - Parsing multilenguaje (Java, JS/TS, C#) (✅ Fase 9)
- **Google Gemini Flash API** - LLM para análisis semántico (✅ Fase 5)
- **PyYAML** - Configuración por proyecto .gtaa.yaml (✅ Fase 7)

### Librerías principales
```python
click>=8.0                        # Interfaz CLI
google-genai>=1.0.0               # SDK Gemini Flash API (Fase 5)
python-dotenv>=1.0.0              # Carga de .env para API key
tree-sitter-language-pack>=0.4.0  # Parsing Java, JS/TS (Fase 9)
tree-sitter-c-sharp>=0.23.0       # Parsing C# (Fase 9)
pytest>=7.0                       # Framework de testing
```

### Arquitectura del sistema
```
┌─────────────────────────────────────────┐
│         INPUT: Proyecto a analizar       │
└─────────────────┬───────────────────────┘
                  ↓
      ┌───────────┴──────────┐
      ↓                      ↓
┌──────────────┐    ┌──────────────────┐
│   ESTÁTICO   │    │   SEMÁNTICO      │
│  AST + Regex │    │  LLM (Gemini)    │
│  4 Checkers  │    │  ✅ Fase 5       │
└──────┬───────┘    └────────┬─────────┘
       └──────────┬───────────┘
                  ↓
         ┌────────────────┐
         │    SCORING     │
         │   + REPORTS    │
         └────────────────┘
```

---

## 📦 Instalación y Ejecución

### Requisitos previos
- Python 3.10 o superior (requerido por tree-sitter)
- pip (gestor de paquetes de Python)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Membrive92/gtaa-ai-validator.git
cd gtaa-ai-validator

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar con todas las dependencias (recomendado)
pip install -e ".[all]"

# O instalar solo core (sin LLM ni multi-lang parsing)
pip install -e .

# O instalar por grupos opcionales
pip install -e ".[ai]"       # Añade google-genai + python-dotenv
pip install -e ".[parsers]"  # Añade tree-sitter (Java, JS/TS, C#)
```

### Docker

```bash
# Construir imagen
docker build -t gtaa-validator .

# Analizar un proyecto local
docker run -v ./mi-proyecto:/project gtaa-validator

# Con opciones
docker run -v ./mi-proyecto:/project gtaa-validator . --verbose

# Con análisis AI (pasar API key)
docker run -e GEMINI_API_KEY=tu_key -v ./mi-proyecto:/project gtaa-validator . --ai

# Generar reportes (se escriben en el volumen montado)
docker run -v ./mi-proyecto:/project gtaa-validator . --json /project/report.json --html /project/report.html
```

### GitHub Action

Otros proyectos pueden usar el validador directamente en su pipeline CI/CD:

```yaml
# En .github/workflows/validate.yml de tu proyecto
name: Validate Test Architecture
on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run gTAA Validator
        id: gtaa
        uses: Membrive92/gtaa-ai-validator@main
        with:
          project_path: ./tests
          verbose: true

      - name: Check score threshold
        if: steps.gtaa.outputs.score < 75
        run: |
          echo "::error::gTAA score (${{ steps.gtaa.outputs.score }}) is below threshold (75)"
          exit 1
```

---

### ✅ Funcionalidad ACTUAL (Fase 10.4)

**Funcionalidad disponible en la versión actual:**

```bash
# Análisis estático multilenguaje (Python, Java, JS/TS, C#)
python -m gtaa_validator /path/to/your/test-project

# Modo verbose para ver detalles de cada violación
python -m gtaa_validator /path/to/project --verbose

# Análisis semántico AI (requiere GEMINI_API_KEY en .env)
python -m gtaa_validator /path/to/project --ai --verbose

# Análisis AI con límite de llamadas (fallback automático a mock)
python -m gtaa_validator /path/to/project --ai --max-llm-calls 5

# Configuración por proyecto (.gtaa.yaml)
python -m gtaa_validator /path/to/project --config /path/.gtaa.yaml

# Exportar reportes
python -m gtaa_validator examples/bad_project --html report.html
python -m gtaa_validator examples/bad_project --json report.json
python -m gtaa_validator examples/bad_project --ai --html report.html --json report.json --verbose

# Probar con ejemplos incluidos (Python, Java, JS, C#)
python -m gtaa_validator examples/bad_project --verbose
python -m gtaa_validator examples/good_project
python -m gtaa_validator examples/java_project --verbose
python -m gtaa_validator examples/js_project --verbose
python -m gtaa_validator examples/csharp_project --verbose

# Ejecutar tests
pytest tests/                                        # Todos (667 tests)
pytest tests/unit/                                   # Solo unitarios
pytest tests/integration/                            # Solo integración
pytest tests/ --cov=gtaa_validator --cov-report=term  # Con cobertura
```

**Capacidades implementadas:**
- ✅ Soporte multilenguaje: Python, Java, JavaScript/TypeScript, C#
- ✅ Arquitectura language-agnostic: mismos checkers para todos los lenguajes (Fase 9 refactor)
- ✅ 5 checkers detectando 17 tipos de violaciones estáticas (incluye BDDChecker)
- ✅ Análisis AST con Visitor Pattern (Python) y tree-sitter (Java, JS/TS, C#)
- ✅ Análisis de estructura de proyecto (directorios requeridos)
- ✅ Detección por regex (emails, URLs, teléfonos, passwords, locators duplicados, configuración hardcodeada)
- ✅ Análisis semántico AI con Gemini Flash API (6 tipos de violación semántica)
- ✅ Sugerencias AI contextuales para cada violación (enriquecimiento)
- ✅ Fallback automático a MockLLMClient cuando no hay API key o rate limit (429)
- ✅ Factory pattern para creación de clientes LLM (create_llm_client)
- ✅ Limitación de llamadas API con --max-llm-calls (fallback proactivo)
- ✅ Tracking de proveedor LLM en reportes (inicial, actual, fallback)
- ✅ Clasificador de archivos API/UI con scoring ponderado (imports AST + código regex + path)
- ✅ Detección automática de Playwright auto-wait (salta MISSING_WAIT_STRATEGY)
- ✅ Configuración por proyecto .gtaa.yaml (exclude_checks, ignore_paths, api_test_patterns)
- ✅ Sistema de scoring 0-100 basado en severidad de violaciones
- ✅ Modo verbose con detalles: archivo, línea, código, mensaje, sugerencias AI
- ✅ Exit code 1 si hay violaciones críticas (útil para CI/CD)
- ✅ Reporte HTML dashboard autocontenido con SVG inline (score gauge, gráficos, tablas)
- ✅ Reporte JSON estructurado para integración CI/CD
- ✅ Flags `--json`, `--html`, `--ai` y `--config` compatibles entre sí
- ✅ Soporte BDD: analiza archivos .feature y step definitions (Behave, pytest-bdd)
- ✅ GherkinParser regex-based sin dependencias externas
- ✅ 5 violaciones BDD: detalles técnicos en Gherkin, browser calls en steps, complejidad, falta de Then, duplicados
- ✅ 667 tests automatizados (93% cobertura de código)

**Ejemplo de salida (con --ai):**
```
=== gTAA AI Validator - Fase 5 ===
Analizando proyecto: examples/bad_project

Ejecutando análisis estático...
Usando Gemini Flash API para análisis semántico...

============================================================
RESULTADOS DEL ANÁLISIS
============================================================

Archivos analizados: 6
Violaciones totales: 59

Violaciones por severidad:
  CRÍTICA: 16
  ALTA:    19
  MEDIA:   22
  BAJA:    2

Puntuación de cumplimiento: 0.0/100
Estado: PROBLEMAS CRÍTICOS

============================================================
Análisis completado en 12.34s
============================================================
```

---

## 📚 Proyectos de Ejemplo

El proyecto incluye ejemplos completamente documentados en el directorio [examples/](examples/).

### Estructura

```
examples/
├── README.md                  # Documentación detallada de cada ejemplo
├── bad_project/               # Proyecto con ~45 violaciones (todos los tipos)
│   ├── test_login.py          # 8 violaciones (Selenium directo)
│   ├── test_search.py         # 7 violaciones (Playwright directo)
│   ├── test_data_issues.py    # Datos hardcoded, nombres genéricos, función larga
│   ├── features/              # Archivos .feature con violaciones BDD
│   │   └── login.feature      # XPath en Gherkin, scenarios sin Then
│   ├── steps/                 # Step definitions con violaciones
│   │   ├── login_steps.py     # Browser calls directos
│   │   └── search_steps.py    # Step pattern duplicado
│   └── pages/
│       └── checkout_page.py   # POM con asserts, imports prohibidos, lógica
└── good_project/              # Proyecto con arquitectura gTAA correcta
    ├── tests/
    │   └── test_login.py      # Tests usando Page Objects
    └── pages/
        └── login_page.py      # Page Object que encapsula Selenium
```

### Uso rápido

```bash
# Analizar proyecto con violaciones (score esperado: 0/100)
python -m gtaa_validator examples/bad_project --verbose

# Analizar proyecto correcto (score esperado: 100/100)
python -m gtaa_validator examples/good_project
```

### Documentación detallada

El archivo [examples/README.md](examples/README.md) incluye:

- ✅ **Tabla de violaciones esperadas**: Cada violación con línea exacta y razón
- ✅ **Comparación lado a lado**: Código MAL vs código BIEN estructurado
- ✅ **Checklist de validación**: Para evaluadores del proyecto
- ✅ **Ground truth etiquetado**: Dataset para validación empírica del TFM

---

### ✅ Funcionalidad Implementada — Fase 7: Soporte Proyectos Mixtos

**Problema resuelto**: Proyectos mixtos con tests de API y front-end generaban falsos positivos. Tests de API no necesitan Page Objects ni wait strategies.

#### Clasificador de archivos (API vs UI)
```python
# Detección automática por archivo usando 3 señales:
# 1. Imports AST (requests, selenium, playwright) — peso 5
# 2. Patrones de código regex (response.status_code) — peso 2
# 3. Patrones de ruta (/api/, test_api_) — peso 3
# Regla conservadora: UI siempre gana en archivos mixtos
```

#### Detección automática de auto-wait (Playwright)
```python
# Playwright tiene auto-wait nativo → MISSING_WAIT_STRATEGY se salta
# automáticamente sin necesidad de configuración YAML.
# Selenium sigue requiriendo waits explícitos → se analiza normalmente.
```

#### Configuración por proyecto (.gtaa.yaml)
```yaml
# Personalización de reglas para frameworks custom
exclude_checks:
  - MISSING_WAIT_STRATEGY  # Para frameworks custom con auto-waits
ignore_paths:
  - "tests/legacy/**"      # Excluir tests legacy del análisis
api_test_patterns:
  - "**/test_api_*.py"     # Patrones adicionales para API tests
```

#### Reglas condicionales por tipo de test
```
# Violaciones filtradas automáticamente:
# ADAPTATION_IN_DEFINITION → se salta en archivos API (no usan POM)
# MISSING_WAIT_STRATEGY    → se salta en archivos API y en Playwright
# Las 16 violaciones restantes aplican a todos los archivos
```

---

### ✅ Funcionalidad Implementada — Fase 8: Soporte Gherkin/BDD

**Problema resuelto**: Proyectos BDD con Behave o pytest-bdd no tenían validación arquitectónica. Los archivos .feature y step definitions quedaban fuera del análisis.

#### GherkinParser (regex-based)
```python
# Parser ligero sin dependencias externas (Gherkin tiene sintaxis regular)
# Extrae: Feature, Scenario, Background, Scenario Outline
# Steps con keywords: Given/When/Then/And/But
# And/But heredan el keyword anterior para has_given/has_when/has_then
```

#### BDDChecker (5 tipos de violación)
```python
# 1. GHERKIN_IMPLEMENTATION_DETAIL: XPath, CSS, URLs, SQL en .feature
# 2. STEP_DEF_DIRECT_BROWSER_CALL: page.locator(), driver.find_element() en steps
# 3. STEP_DEF_TOO_COMPLEX: step definition > 15 líneas
# 4. MISSING_THEN_STEP: scenario sin verificación
# 5. DUPLICATE_STEP_PATTERN: misma regex en múltiples step files (check_project)
```

#### Detección automática de step definitions
```python
# Por ruta: steps/, step_defs/, step_definitions/
# Por nombre: step_*.py, *_steps.py
# Por AST: decoradores @given/@when/@then
```

---

### ✅ Funcionalidad Implementada — Fase 9: Soporte Multilenguaje

**Problema resuelto**: Solo se analizaban proyectos Python. Proyectos Java, JavaScript/TypeScript y C# no tenían validación arquitectónica.

#### Parsers multilenguaje
```python
# Python: ast nativo (stdlib) → PythonParser
# Java: tree-sitter-language-pack → JavaParser
# JavaScript/TypeScript: tree-sitter-language-pack → JSParser
# C#: tree-sitter-c-sharp → CSharpParser
```

#### Arquitectura language-agnostic (refactor clave)
```python
# ANTES: Cada lenguaje tendría su propio checker (JavaChecker, JSChecker...)
# DESPUÉS: Checkers unificados que trabajan con ParseResult

# ParseResult es la interfaz común que producen todos los parsers:
# - imports: List[ParsedImport]
# - classes: List[ParsedClass]
# - functions: List[ParsedFunction]
# - calls: List[ParsedCall]
# - strings: List[ParsedString]

# Los checkers detectan por extensión:
BROWSER_METHODS_PYTHON = {"find_element", "locator", ...}
BROWSER_METHODS_JAVA = {"findElement", "locator", ...}
BROWSER_METHODS_JS = {"locator", "getByRole", "$", ...}
BROWSER_METHODS_CSHARP = {"FindElement", "Navigate", ...}
```

#### Frameworks soportados
```
# Python: Selenium, Playwright, pytest, unittest
# Java: Selenium, Playwright, TestNG, JUnit
# JavaScript/TypeScript: Playwright, Cypress, WebdriverIO, Jest, Mocha
# C#: Selenium, Playwright, NUnit, xUnit, MSTest
```

---

### ✅ Funcionalidad Implementada — Fase 10.1: Optimización Capa LLM

**Problema resuelto**: El free tier de Gemini (10 req/min) provocaba errores 429 que abortaban el análisis. No había control sobre el consumo de API ni visibilidad del proveedor usado.

#### Factory Pattern para clientes LLM
```python
# Creación centralizada y testeable de clientes LLM
# Auto-detecta proveedor según API key disponible
from gtaa_validator.llm.factory import create_llm_client

client = create_llm_client()           # Auto-detect
client = create_llm_client("mock")     # Forzar mock
client = create_llm_client("gemini")   # Forzar Gemini
```

#### Fallback automático ante rate limit
```python
# Si Gemini retorna 429 (rate limit) o quota exceeded:
# 1. SemanticAnalyzer captura RateLimitError
# 2. Cambia a MockLLMClient automáticamente
# 3. Reintenta la operación con heurísticas
# 4. Continúa el análisis sin interrumpir
```

#### Limitación de llamadas con --max-llm-calls
```bash
# Limitar a 5 llamadas API, luego fallback proactivo a mock
python -m gtaa_validator ./proyecto --ai --max-llm-calls 5

# Sin límite (por defecto)
python -m gtaa_validator ./proyecto --ai
```

#### Tracking de proveedor en reportes
```
# CLI muestra: [!] Fallback activado: gemini -> mock
# HTML muestra: badge con proveedor (Gemini -> Mock si fallback)
# JSON incluye: llm_provider_info con initial/current/fallback
```

---

### ⏳ Funcionalidad FUTURA — Fase 10 (pendiente)

```
# ⏳ Integración CI/CD (--min-score)
# ⏳ Documentación TFM final
```

---

## 📁 Estructura del Proyecto

```
gtaa-ai-validator/
│
├── README.md                           # Este archivo
├── LICENSE                             # Licencia MIT
├── requirements.txt                    # Dependencias Python
├── setup.py                            # Shim de compatibilidad
├── Dockerfile                          # Imagen Docker multistage
├── .dockerignore                       # Exclusiones del contexto Docker
├── action.yml                          # GitHub Action reutilizable
├── .github/workflows/ci.yml            # Pipeline CI (tests + build)
├── .gitignore                          # Archivos ignorados por Git
│
├── gtaa_validator/                     # 📦 Código fuente principal
│   ├── __init__.py                     # Inicialización del paquete
│   ├── __main__.py                     # Entry point CLI
│   ├── models.py                       # Modelos de datos (Violation, Report)
│   ├── file_classifier.py             # Clasificador API/UI (Fase 7)
│   ├── config.py                      # ProjectConfig + .gtaa.yaml (Fase 7)
│   │
│   ├── parsers/                        # 📝 Parsers multilenguaje (Fase 8-9)
│   │   ├── __init__.py                 # Exporta parsers y get_parser_for_file()
│   │   ├── gherkin_parser.py           # Parser regex-based para .feature
│   │   ├── treesitter_base.py          # Parser base tree-sitter + ParseResult
│   │   ├── python_parser.py            # Parser Python (ast nativo)
│   │   ├── java_parser.py              # Parser Java (tree-sitter)
│   │   ├── js_parser.py                # Parser JavaScript/TypeScript (tree-sitter)
│   │   └── csharp_parser.py            # Parser C# (tree-sitter)
│   │
│   ├── analyzers/                      # 🔍 Motores de análisis
│   │   ├── static_analyzer.py          # Orquestador estático (Facade Pattern)
│   │   └── semantic_analyzer.py        # Orquestador semántico AI (Fase 5)
│   │
│   ├── llm/                            # 🧠 Clientes LLM (Fase 5 + 10.1)
│   │   ├── client.py                   # MockLLMClient (heurísticas deterministas)
│   │   ├── api_client.py              # APILLMClient + RateLimitError (Fase 10.1)
│   │   ├── factory.py                 # create_llm_client() factory (Fase 10.1)
│   │   └── prompts.py                  # Templates de prompts optimizados
│   │
│   ├── reporters/                      # 📊 Generadores de reportes
│   │   ├── json_reporter.py            # Reporte JSON estructurado
│   │   └── html_reporter.py            # Dashboard HTML autocontenido (SVG)
│   │
│   └── checkers/                       # ✅ Detectores de violaciones
│       ├── base.py                     # Clase base abstracta (Strategy Pattern)
│       ├── definition_checker.py       # Test Definition Layer (AST Visitor)
│       ├── structure_checker.py        # Estructura del proyecto (Filesystem)
│       ├── adaptation_checker.py       # Test Adaptation Layer (AST + Regex)
│       ├── quality_checker.py          # Calidad de tests (AST + Regex)
│       └── bdd_checker.py              # BDD/Gherkin (Fase 8)
│
├── tests/                              # 🧪 Tests automatizados (667 tests, 93% coverage)
│   ├── conftest.py                     # Fixtures compartidas
│   ├── unit/                           # Tests unitarios
│   │   ├── test_models.py             # Modelos de datos
│   │   ├── test_definition_checker.py # DefinitionChecker
│   │   ├── test_structure_checker.py  # StructureChecker
│   │   ├── test_adaptation_checker.py # AdaptationChecker
│   │   ├── test_quality_checker.py    # QualityChecker
│   │   ├── test_bdd_checker.py        # BDDChecker (Fase 8)
│   │   ├── test_gherkin_parser.py     # GherkinParser (Fase 8)
│   │   ├── test_treesitter_base.py    # ParseResult y base (Fase 9)
│   │   ├── test_python_parser.py      # PythonParser (Fase 9+10.5)
│   │   ├── test_java_checker.py       # JavaParser + checkers (Fase 9+10.5)
│   │   ├── test_js_checker.py         # JSParser + checkers (Fase 9+10.5)
│   │   ├── test_csharp_checker.py     # CSharpParser + checkers (Fase 9+10.5)
│   │   ├── test_base_checker.py       # BaseChecker (Fase 10.5)
│   │   ├── test_file_utils.py         # read_file_safe (Fase 10.5)
│   │   ├── test_json_reporter.py      # JsonReporter
│   │   ├── test_html_reporter.py      # HtmlReporter
│   │   ├── test_llm_client.py         # MockLLMClient
│   │   ├── test_api_client.py         # APILLMClient + RateLimitError (Fase 10.1)
│   │   ├── test_llm_factory.py        # Factory LLM (Fase 10.1)
│   │   ├── test_semantic_analyzer.py  # SemanticAnalyzer + fallback + tracking
│   │   ├── test_classifier.py        # FileClassifier (Fase 7)
│   │   └── test_config.py            # ProjectConfig (Fase 7)
│   └── integration/                    # Tests de integración
│       ├── test_static_analyzer.py    # Pipeline completo
│       └── test_reporters.py          # Análisis → JSON/HTML
│
├── examples/                           # 📝 Proyectos de ejemplo
│   ├── README.md                       # Documentación de violaciones
│   ├── bad_project/                    # Proyecto Python con ~35 violaciones
│   ├── good_project/                   # Proyecto Python gTAA correcto (score 100)
│   ├── java_project/                   # Proyecto Java con violaciones (Fase 9)
│   ├── js_project/                     # Proyecto JS/TS con violaciones (Fase 9)
│   └── csharp_project/                 # Proyecto C# con violaciones (Fase 9)
│
├── .env.example                        # 🔑 Template para API key de Gemini
│
└── docs/                               # 📚 Documentación técnica
    ├── README.md                       # Índice de documentación
    ├── ARCHITECTURE_DECISIONS.md       # Decisiones arquitectónicas (55 ADR)
    ├── PHASE1_FLOW_DIAGRAMS.md         # Diagramas Fase 1 (CLI y fundación)
    ├── PHASE2_FLOW_DIAGRAMS.md         # Diagramas Fase 2 (análisis estático)
    ├── PHASE3_FLOW_DIAGRAMS.md         # Diagramas Fase 3 (9 violaciones)
    ├── PHASE4_FLOW_DIAGRAMS.md         # Diagramas Fase 4 (reportes)
    ├── PHASE5_FLOW_DIAGRAMS.md         # Diagramas Fase 5 (análisis semántico AI)
    ├── PHASE6_FLOW_DIAGRAMS.md         # Diagramas Fase 6 (18 violaciones)
    ├── PHASE7_FLOW_DIAGRAMS.md         # Diagramas Fase 7 (proyectos mixtos)
    ├── PHASE8_FLOW_DIAGRAMS.md         # Diagramas Fase 8 (BDD/Gherkin)
    ├── PHASE9_FLOW_DIAGRAMS.md         # Diagramas Fase 9 (multilenguaje + refactor)
    ├── PHASE10_FLOW_DIAGRAMS.md        # Diagramas Fase 10 (optimización LLM)
    └── PHASE10_SECURITY_AUDIT.md       # Auditoría de seguridad (9 hallazgos)
```

> **Nota sobre `docs/`**: La documentación técnica se distribuye en múltiples documentos independientes, uno por cada fase del proyecto y uno para las decisiones arquitectónicas. Esta separación responde a un criterio de **transparencia y trazabilidad**: cada documento refleja el estado del proyecto en el momento de su elaboración, permitiendo seguir la evolución del diseño y las decisiones técnicas a lo largo del desarrollo. El índice general se encuentra en [`docs/README.md`](docs/README.md).

---

## ⚙️ Funcionalidades Principales

### 1. 🔍 Detección de Violaciones Arquitectónicas

#### 5 Checkers — 17 tipos de violaciones estáticas

| Severidad | Tipo | Checker | Técnica |
|-----------|------|---------|---------|
| 🔴 CRÍTICA | `ADAPTATION_IN_DEFINITION` | DefinitionChecker | AST Visitor (BrowserAPICallVisitor) |
| 🔴 CRÍTICA | `MISSING_LAYER_STRUCTURE` | StructureChecker | Sistema de archivos (iterdir) |
| 🔴 CRÍTICA | `STEP_DEF_DIRECT_BROWSER_CALL` | BDDChecker | AST (browser APIs en step defs) |
| 🟡 ALTA | `HARDCODED_TEST_DATA` | QualityChecker | AST Visitor + Regex |
| 🟡 ALTA | `ASSERTION_IN_POM` | AdaptationChecker | AST Visitor |
| 🟡 ALTA | `FORBIDDEN_IMPORT` | AdaptationChecker | ast.walk |
| 🟡 ALTA | `HARDCODED_CONFIGURATION` | QualityChecker | Regex (localhost, sleep, paths) |
| 🟡 ALTA | `SHARED_MUTABLE_STATE` | QualityChecker | AST (Assign + Global) |
| 🟡 ALTA | `GHERKIN_IMPLEMENTATION_DETAIL` | BDDChecker | Regex (XPath, CSS, URLs en .feature) |
| 🟠 MEDIA | `BUSINESS_LOGIC_IN_POM` | AdaptationChecker | AST Visitor |
| 🟠 MEDIA | `DUPLICATE_LOCATOR` | AdaptationChecker | Regex + Registro cross-file |
| 🟠 MEDIA | `LONG_TEST_FUNCTION` | QualityChecker | ast.walk + lineno |
| 🟠 MEDIA | `BROAD_EXCEPTION_HANDLING` | QualityChecker | AST (ExceptHandler) |
| 🟠 MEDIA | `STEP_DEF_TOO_COMPLEX` | BDDChecker | AST (líneas > 15 en step def) |
| 🟠 MEDIA | `MISSING_THEN_STEP` | BDDChecker | GherkinParser (scenario sin Then) |
| 🟢 BAJA | `POOR_TEST_NAMING` | QualityChecker | ast.walk + Regex |
| 🟢 BAJA | `DUPLICATE_STEP_PATTERN` | BDDChecker | Regex cross-file (check_project) |

### 2. 📊 Sistema de Puntuación (0-100)

| Severidad | Penalización por violación |
|-----------|---------------------------|
| CRITICAL | -10 puntos |
| HIGH | -5 puntos |
| MEDIUM | -2 puntos |
| LOW | -1 punto |

Puntuación = max(0, 100 - suma de penalizaciones)

### 3. 📈 Reportes Visuales (✅ Fase 4)

#### Reporte HTML (`--html report.html`)
- Dashboard autocontenido (HTML + CSS + SVG inline, sin dependencias externas)
- Score gauge circular SVG con color según rango
- Tarjetas de conteo por severidad (CRÍTICA, ALTA, MEDIA, BAJA)
- Gráfico de barras SVG con distribución de violaciones
- Tabla de violaciones agrupadas por checker con badges de severidad
- Protección XSS con `html.escape()` en todo contenido dinámico
- Responsive (viewport meta)

#### Reporte JSON (`--json report.json`)
- Formato estructurado con metadata, summary y violations
- Compatible con pipelines CI/CD
- Generado desde `Report.to_dict()` sin dependencias externas

### 4. 🧠 Análisis Semántico con IA (✅ Fase 5-6, optimizado Fase 10.1)

**Activado con `--ai`:**
- Detección de 6 tipos de violaciones semánticas que AST no puede capturar
- Sugerencias AI contextuales en español para cada violación
- Gemini Flash API (free tier) con fallback automático a MockLLMClient
- Factory pattern para creación de clientes (`create_llm_client()`)
- Fallback automático ante rate limit (429) o quota exceeded
- `--max-llm-calls N` para limitar llamadas API antes de fallback proactivo
- Tracking de proveedor (inicial, actual, si hubo fallback) visible en reportes
- Configuración via `GEMINI_API_KEY` en `.env`

| Severidad | Tipo Semántico | Detección |
|-----------|---------------|-----------|
| 🟡 ALTA | `IMPLICIT_TEST_DEPENDENCY` | LLM: tests comparten estado mutable |
| 🟡 ALTA | `PAGE_OBJECT_DOES_TOO_MUCH` | LLM: POM con exceso de responsabilidades |
| 🟠 MEDIA | `UNCLEAR_TEST_PURPOSE` | LLM: nombre/docstring no descriptivo |
| 🟠 MEDIA | `MISSING_WAIT_STRATEGY` | LLM: interacción UI sin espera |
| 🟠 MEDIA | `MISSING_AAA_STRUCTURE` | LLM: test sin estructura Arrange-Act-Assert |
| 🟠 MEDIA | `MIXED_ABSTRACTION_LEVEL` | LLM: selectores UI en métodos de negocio |

---

## 🎓 Contexto Académico (TFM)

### Objetivos del TFM
1. ✅ Desarrollar sistema de IA para validación arquitectónica (Fase 8/10 completa)
2. ✅ Integrar LLM real para análisis semántico (Gemini Flash - Fase 5)
3. ✅ Ampliar cobertura a 23 tipos de violación basados en catálogo CT-TAE (Fase 6-8)
4. ✅ Crear dataset etiquetado para la comunidad (ejemplos con ground truth)
5. ✅ Soporte BDD/Gherkin para validación de capa Gherkin (Fase 8)

### Tecnologías de IA a Utilizar
- **Abstract Syntax Tree (AST)** para análisis estático (✅ Implementado)
- **Regex patterns** para detección de datos y locators (✅ Implementado)
- **Large Language Models** (Gemini Flash - ✅ Fase 5)
- **Clasificador de archivos** (heurísticas API vs UI - ✅ Fase 7)

### Metodología
**Desarrollo Incremental:**
- ✅ Fase 1: Fundación (CLI básico) - **COMPLETA**
- ✅ Fase 2: Motor de análisis estático con AST (1 violación) - **COMPLETA**
- ✅ Fase 3: Cobertura completa (9 violaciones) + Tests (140) - **COMPLETA**
- ✅ Fase 4: Reportes HTML/JSON profesionales - **COMPLETA**
- ✅ Fase 5: Análisis semántico AI (Gemini Flash + Mock) - **COMPLETA**
- ✅ Fase 6: Ampliación cobertura (18 violaciones) + Documentación - **COMPLETA**
- ✅ Fase 7: Soporte para proyectos mixtos (API + UI) + auto-wait Playwright - **COMPLETA**
- ✅ Fase 8: Soporte Gherkin/BDD (Behave + pytest-bdd) - **COMPLETA**
- ✅ Fase 9: Soporte Multilenguaje (Java + JS/TS + C#) - **COMPLETA**
- 🔄 Fase 10: Optimización y documentación final - **EN PROGRESO**
  - ✅ 10.1: Optimización capa LLM (factory, fallback, rate limit, --max-llm-calls)
  - ✅ 10.5: Cobertura de código 84% a 93% (633 tests)
  - ✅ 10.6: Tests de regresión de seguridad (34 tests para SEC-01 a SEC-09)

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.

---

## 📧 Contacto

**Autor**: Jose Antonio Membrive Guillen
**Email**: membri_2@hotmail.com

---

## 📚 Referencias

### Estándares y Normativa
- [ISTQB CT-TAE Syllabus v2016](https://www.istqb.org/)

### Documentación Técnica del Proyecto
- **[Decisiones Arquitectónicas (ADR)](docs/ARCHITECTURE_DECISIONS.md)** ✅ — 55 ADRs: patrones de diseño, paradigmas, justificaciones técnicas
- **[Diagramas de Flujo - Fase 1](docs/PHASE1_FLOW_DIAGRAMS.md)** ✅ — Fundación del proyecto, CLI con Click, descubrimiento de archivos
- **[Diagramas de Flujo - Fase 2](docs/PHASE2_FLOW_DIAGRAMS.md)** ✅ — Motor de análisis estático, BrowserAPICallVisitor, scoring
- **[Diagramas de Flujo - Fase 3](docs/PHASE3_FLOW_DIAGRAMS.md)** ✅ — 4 checkers, 9 violaciones, AST visitors, cross-file state
- **[Diagramas de Flujo - Fase 4](docs/PHASE4_FLOW_DIAGRAMS.md)** ✅ — Reportes JSON/HTML, SVG inline, agrupación por checker
- **[Diagramas de Flujo - Fase 5](docs/PHASE5_FLOW_DIAGRAMS.md)** ✅ — Análisis semántico AI, Gemini Flash, prompt engineering, parsing LLM
- **[Diagramas de Flujo - Fase 6](docs/PHASE6_FLOW_DIAGRAMS.md)** ✅ — Ampliación a 18 violaciones, nuevos checkers, heurísticas mock
- **[Diagramas de Flujo - Fase 7](docs/PHASE7_FLOW_DIAGRAMS.md)** ✅ — Proyectos mixtos API+UI, FileClassifier, .gtaa.yaml, auto-wait Playwright
- **[Diagramas de Flujo - Fase 8](docs/PHASE8_FLOW_DIAGRAMS.md)** ✅ — Soporte BDD/Gherkin, GherkinParser, BDDChecker, 5 violaciones BDD
- **[Diagramas de Flujo - Fase 9](docs/PHASE9_FLOW_DIAGRAMS.md)** ✅ — Multilenguaje, ParseResult, checkers language-agnostic, refactor DRY
- **[Diagramas de Flujo - Fase 10](docs/PHASE10_FLOW_DIAGRAMS.md)** ✅ — Optimización LLM, factory, fallback, rate limit, tracking
- **[Auditoría de Seguridad](docs/PHASE10_SECURITY_AUDIT.md)** ✅ — 9 hallazgos (OWASP), buenas prácticas, matriz de riesgo
- **[Índice de documentación](docs/README.md)** ✅

---

## 📝 Historial de Desarrollo

### Versión 0.1.0 - Fase 1 (26 Enero 2026) ✅

**Implementado:**
- ✅ Estructura básica del proyecto (setup.py, requirements.txt, etc.)
- ✅ CLI funcional con Click framework
- ✅ Descubrimiento recursivo de archivos de test
- ✅ Modo verbose para output detallado

---

### Versión 0.2.0 - Fase 2 (26 Enero 2026) ✅

**Implementado:**
- ✅ Modelos de datos (Violation, Report, Severity, ViolationType)
- ✅ Sistema de checkers con Strategy Pattern
- ✅ DefinitionChecker con BrowserAPICallVisitor (AST Visitor Pattern)
- ✅ Detecta Selenium (find_element, find_elements, legacy methods) y Playwright (locator, click, fill, wait_for_selector)
- ✅ StaticAnalyzer: Orquesta checkers (Facade Pattern)
- ✅ Sistema de scoring 0-100 con penalización por severidad
- ✅ Proyectos de ejemplo documentados (bad_project, good_project)

---

### Versión 0.3.0 - Fase 3 (28 Enero 2026) ✅

**Implementado:**
- ✅ StructureChecker: Valida estructura de directorios (tests/ + pages/)
- ✅ AdaptationChecker: 4 violaciones en Page Objects (assertions, forbidden imports, business logic, duplicate locators)
- ✅ QualityChecker: 3 violaciones de calidad (hardcoded data, long functions, poor naming)
- ✅ check_project() en BaseChecker para checks a nivel de proyecto
- ✅ StaticAnalyzer actualizado: 4 checkers, project-level + file-level checks
- ✅ 140 tests automatizados (122 unitarios + 18 integración) en Fase 3
- ✅ Tests separados en tests/unit/ y tests/integration/
- ✅ Documentación técnica con diagramas de flujo (Fase 2 y 3)
- ✅ Ejemplos ampliados: bad_project con ~35 violaciones de todos los tipos

**Checkers y violaciones:**

| Checker | Violaciones | Técnica |
|---------|-------------|---------|
| DefinitionChecker | ADAPTATION_IN_DEFINITION | BrowserAPICallVisitor (AST) |
| StructureChecker | MISSING_LAYER_STRUCTURE | Verificación de sistema de archivos |
| AdaptationChecker | ASSERTION_IN_POM, FORBIDDEN_IMPORT, BUSINESS_LOGIC_IN_POM, DUPLICATE_LOCATOR | AST Visitors + Regex + Estado cross-file |
| QualityChecker | HARDCODED_TEST_DATA, LONG_TEST_FUNCTION, POOR_TEST_NAMING, BROAD_EXCEPTION_HANDLING, HARDCODED_CONFIGURATION, SHARED_MUTABLE_STATE | AST Visitor + Regex |

**Próximos pasos:** Fase 4 - Reportes HTML/JSON

---

### Versión 0.4.0 - Fase 4 (31 Enero 2026) ✅

**Implementado:**
- ✅ JsonReporter: exportación JSON estructurada (`--json report.json`)
- ✅ HtmlReporter: dashboard HTML autocontenido con SVG inline (`--html report.html`)
- ✅ Score gauge circular SVG con colores según rango
- ✅ Gráfico de barras SVG de distribución por severidad
- ✅ Tabla de violaciones agrupada por checker con badges
- ✅ Protección XSS con `html.escape()` en todo contenido dinámico
- ✅ Etiquetas de severidad y tipos de violación en español
- ✅ Flags CLI `--json` y `--html` compatibles entre sí
- ✅ 25 tests nuevos (14 unitarios HtmlReporter + 7 unitarios JsonReporter + 4 integración)
- ✅ Documentación: PHASE4_FLOW_DIAGRAMS.md + ADR 9-11

**Próximos pasos:** Fase 5 - Análisis semántico AI

---

### Versión 0.5.0 - Fase 5 (1 Febrero 2026) ✅

**Implementado:**
- ✅ GeminiLLMClient: análisis semántico real con Gemini 2.5 Flash Lite API
- ✅ MockLLMClient: heurísticas deterministas (AST + regex) como fallback
- ✅ Prompt engineering: 3 templates (system, analyze, enrich) optimizados para gTAA
- ✅ SemanticAnalyzer: orquestación en 2 fases (detección + enriquecimiento)
- ✅ 4 nuevos tipos de violación semántica (UNCLEAR_TEST_PURPOSE, PAGE_OBJECT_DOES_TOO_MUCH, IMPLICIT_TEST_DEPENDENCY, MISSING_WAIT_STRATEGY)
- ✅ Sugerencias AI contextuales en español para cada violación
- ✅ Parsing robusto de respuestas LLM (JSON, markdown, errores)
- ✅ Configuración via .env con python-dotenv (GEMINI_API_KEY)
- ✅ Fallback automático: sin API key → MockLLMClient sin error
- ✅ Flag CLI `--ai` para activar análisis semántico
- ✅ 12 tests unitarios nuevos para GeminiLLMClient (mockeados)
- ✅ Documentación: PHASE5_FLOW_DIAGRAMS.md + ADR 12-16

**Próximos pasos:** Fase 6 - Ampliación de cobertura

---

### Versión 0.6.0 - Fase 6 (1 Febrero 2026) ✅

**Implementado:**
- ✅ 5 nuevas violaciones basadas en catálogo ISTQB CT-TAE (13 → 18 tipos)
- ✅ BROAD_EXCEPTION_HANDLING: detección AST de `except:` y `except Exception:`
- ✅ HARDCODED_CONFIGURATION: detección regex de localhost URLs, `time.sleep()`, paths absolutos
- ✅ SHARED_MUTABLE_STATE: detección AST de variables mutables a nivel de módulo + `global` en tests
- ✅ MISSING_AAA_STRUCTURE: detección LLM de tests sin estructura Arrange-Act-Assert
- ✅ MIXED_ABSTRACTION_LEVEL: detección LLM de selectores UI en métodos de negocio
- ✅ MockLLMClient ampliado con 2 nuevas heurísticas deterministas
- ✅ GeminiLLMClient VALID_TYPES ampliado (4 → 6 tipos)
- ✅ ANALYZE_FILE_PROMPT ampliado con 2 nuevos tipos de violación
- ✅ 25 tests nuevos (15 QualityChecker + 7 MockLLMClient + 3 GeminiLLMClient)
- ✅ Documentación: PHASE6_FLOW_DIAGRAMS.md + ADR 17-21

**Próximos pasos:** Fase 7 - Soporte API testing

---

### Versión 0.7.0 - Fase 7 (2 Febrero 2026) ✅

**Implementado:**
- ✅ FileClassifier: clasificación automática API/UI/unknown por archivo (scoring ponderado)
- ✅ ClassificationResult con detección de frameworks (Playwright, Selenium)
- ✅ Detección automática de auto-wait (Playwright): salta MISSING_WAIT_STRATEGY sin YAML
- ✅ ProjectConfig: configuración por proyecto via .gtaa.yaml (exclude_checks, ignore_paths, api_test_patterns)
- ✅ Degradación elegante: funciona sin .gtaa.yaml, YAML inválido → defaults
- ✅ DefinitionChecker salta ADAPTATION_IN_DEFINITION en archivos API
- ✅ MockLLMClient y GeminiLLMClient: has_auto_wait para skip MISSING_WAIT_STRATEGY
- ✅ Prompts LLM ampliados con contexto de clasificación y auto-wait
- ✅ CLI: opción --config para especificar .gtaa.yaml manualmente
- ✅ PyYAML>=6.0 como dependencia
- ✅ Ejemplo API test en examples/bad_project/tests/api/
- ✅ 40 tests nuevos (23 classifier + 8 config + 4 definition_checker + 5 otros)
- ✅ Documentación: PHASE7_FLOW_DIAGRAMS.md + ADR 22-27

**Próximos pasos:** Fase 8 - Optimización y documentación final

---

### Versión 0.8.0 - Fase 8 (3 Febrero 2026) ✅

**Implementado:**
- ✅ GherkinParser: parser regex-based para archivos .feature (sin dependencias externas)
- ✅ Soporte para Feature, Scenario, Scenario Outline, Background
- ✅ Herencia de keywords And/But para detección precisa de has_then
- ✅ BDDChecker: 5 nuevos tipos de violación BDD
- ✅ GHERKIN_IMPLEMENTATION_DETAIL: XPath, CSS selectors, URLs, SQL en .feature
- ✅ STEP_DEF_DIRECT_BROWSER_CALL: browser APIs directamente en step definitions
- ✅ STEP_DEF_TOO_COMPLEX: step definition > 15 líneas
- ✅ MISSING_THEN_STEP: scenario sin step Then (sin verificación)
- ✅ DUPLICATE_STEP_PATTERN: misma regex en múltiples step files (check_project cross-file)
- ✅ Detección automática de step definitions (por ruta y AST)
- ✅ Extensión de StaticAnalyzer para incluir .feature en file discovery
- ✅ LLM layer actualizado con 5 nuevos tipos de violación
- ✅ Ejemplos BDD en bad_project (features/ y steps/)
- ✅ 43 tests nuevos (27 GherkinParser + 16 BDDChecker)
- ✅ Documentación: PHASE8_FLOW_DIAGRAMS.md + ADR 28-32

---

### Versión 0.9.0 - Fase 9 (4 Febrero 2026) ✅

**Implementado:**
- ✅ **Arquitectura language-agnostic**: Checkers únicos que trabajan con ParseResult abstracto
- ✅ TreeSitterBaseParser: wrapper base sobre tree-sitter con dataclasses comunes
- ✅ JavaParser: parser completo para Java con tree-sitter-language-pack
- ✅ JSParser: parser para JavaScript/TypeScript con tree-sitter-language-pack
- ✅ CSharpParser: parser para C# con tree-sitter-c-sharp
- ✅ ParseResult: interfaz unificada (imports, classes, functions, calls, strings)
- ✅ Factory function `get_parser_for_file()` para selección automática de parser
- ✅ Refactor de checkers existentes: DefinitionChecker, AdaptationChecker, QualityChecker
- ✅ Detección multilenguaje de violaciones gTAA en Java, JS/TS, C#
- ✅ Python 3.10+ requerido (requisito de tree-sitter 0.25.x)
- ✅ 3 ejemplos multilenguaje: java_project/, js_project/, csharp_project/
- ✅ Tests unitarios para todos los parsers y checkers multilenguaje
- ✅ Documentación: PHASE9_FLOW_DIAGRAMS.md + ADR 33-37

**Decisión arquitectónica clave:**
- Checkers NO son language-specific (no JavaChecker, JSChecker separados)
- Un solo DefinitionChecker detecta `driver.findElement()` (Java), `cy.get()` (JS), `driver.FindElement()` (C#)
- ParseResult como contrato común elimina duplicación de código (DRY)
- Python usa AST nativo (stdlib) por pragmatismo; Java/JS/C# usan tree-sitter

**Lenguajes soportados:**
| Lenguaje | Parser | Dependencia |
|----------|--------|-------------|
| Python | `ast` (stdlib) | — |
| Java | TreeSitterBaseParser | tree-sitter-language-pack |
| JavaScript/TypeScript | TreeSitterBaseParser | tree-sitter-language-pack |
| C# | TreeSitterBaseParser | tree-sitter-c-sharp |

**Próximos pasos:** Fase 10 - Optimización y Documentación Final

---

### Versión 0.10.1 - Fase 10.1 (5 Febrero 2026) ✅

**Implementado:**
- ✅ Refactor: GeminiLLMClient renombrado a APILLMClient (naming provider-agnostic)
- ✅ Factory pattern: `create_llm_client()` para creación centralizada de clientes LLM
- ✅ RateLimitError: excepción específica para errores 429/quota de la API
- ✅ Fallback automático: Gemini -> MockLLMClient ante rate limit o quota exceeded
- ✅ `--max-llm-calls`: opción CLI para limitar llamadas API antes de fallback proactivo
- ✅ Provider tracking: registro de proveedor inicial/actual/fallback en `Report.llm_provider_info`
- ✅ Visualización en reportes: badge de proveedor LLM en HTML, info en JSON, mensaje en CLI
- ✅ Prompts optimizados: ~40% menos tokens
- ✅ Fix encoding Windows: caracteres Unicode reemplazados por ASCII/HTML entities
- ✅ Tests para factory, fallback y tracking de proveedor
- ✅ Documentación: PHASE10_FLOW_DIAGRAMS.md + ADR 38-42

---

### Versión 0.10.2 - Fase 10.2 (6 Febrero 2026) ✅

**Implementado:**
- ✅ Sistema de logging profesional con `logging` stdlib (reemplaza 15 `print()`)
- ✅ `--log-file`: opción CLI para escribir logs a fichero (siempre DEBUG)
- ✅ `--verbose` auto-crea `logs/gtaa_debug.log` por defecto
- ✅ Dataclass `AnalysisMetrics`: timing por fase, tokens LLM, archivos/segundo
- ✅ Métricas en reportes HTML (tarjetas de rendimiento) y JSON
- ✅ Documentación: ADR 43-44, diagramas Fase 10.2

---

### Versión 0.10.3 - Fase 10.3 (6 Febrero 2026) ✅

**Implementado:**
- ✅ Version bump a 0.10.3 con single source of truth (`__init__.__version__`)
- ✅ `pyproject.toml` (PEP 621): dependencias opcionales `[ai]`, `[parsers]`, `[all]`
- ✅ Eliminación de 159 líneas de código muerto (3 clases/métodos legacy)
- ✅ Actualización `checkers/__init__.py`: exporta 6 checkers (era 2)
- ✅ Logging en 10 bloques `except Exception: pass` silenciosos
- ✅ Eliminación de `ast.Str` deprecado (Python 3.14 compatibility)
- ✅ Alineación LSP: `BaseChecker.check()` acepta `Union[ast.Module, ParseResult]`
- ✅ 14 tests nuevos: CLI (CliRunner) + prompts (funciones puras)
- ✅ PEP 8 E402: logger después de imports en 4 ficheros
- ✅ Consistencia de docstrings: español, sin refs a fases obsoletas
- ✅ Total: 416 tests (base) | Documentación: ADR 45-51, diagramas Fase 10.3

---

### Versión 0.10.4 - Fase 10.4 (6 Febrero 2026) ✅

**Implementado:**
- ✅ Dockerfile multistage (builder + runtime, ~150MB) con todas las dependencias
- ✅ `.dockerignore` para contexto de build limpio
- ✅ Fix `build-backend`: `setuptools.build_meta` (era API privada `_legacy`)
- ✅ GitHub Actions CI: matrix Python 3.10/3.11/3.12, tests + build
- ✅ GitHub Action reutilizable (`action.yml`): composite action con inputs/outputs
- ✅ Outputs: score, violations, reportes JSON/HTML como artefactos
- ✅ Documentación: ADR 52-54, diagramas Fase 10.4

---

### Versión 0.10.5 - Fase 10.5 (6 Febrero 2026) ✅

**Implementado:**
- ✅ Cobertura de código: 84% a 93% global (objetivo 90%+ superado)
- ✅ 251 tests nuevos (416 a 667 tests totales)
- ✅ `pytest-cov` como dependencia de desarrollo
- ✅ Nuevos test files: test_file_utils.py, test_base_checker.py, test_python_parser.py
- ✅ Tests CLI extendidos: score labels, --config, --ai, exit codes, verbose
- ✅ Tests de parsers tree-sitter: JavaParser, CSharpParser, JSParser (utility methods, extraction)
- ✅ Tests de clasificador: multilanguage detection, ParseResult classification
- ✅ Cobertura por modulo: __main__.py 100%, file_utils.py 100%, file_classifier.py 99%, python_parser.py 95%, js_parser.py 94%, java_parser.py 90%

---

### Versión 1.0.0 - Fase 10 Final (Pendiente) ⏳

**Planificado:**
- ⏳ CLI: `--min-score` threshold mínimo para exit code
- ⏳ CLI: `--lang` forzar lenguaje si auto-detección falla
- ⏳ Documentación TFM final

---

<div align="center">

**Estado del proyecto:** Fase 10.6/10 | 23 violaciones | 4 lenguajes (Python, Java, JS/TS, C#) | 667 tests | 93% cobertura

</div>
