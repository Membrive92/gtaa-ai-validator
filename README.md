# 🤖 gTAA AI Validator

**Sistema Híbrido de IA para Validación Automática de Arquitectura de Test Automation: Análisis Estático y Semántico con LLMs**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)](https://github.com/Membrive92/gtaa-ai-validator)
[![Fase](https://img.shields.io/badge/fase-7%2F8-blue)](https://github.com/Membrive92/gtaa-ai-validator)
[![Progreso](https://img.shields.io/badge/progreso-87%25-green)](https://github.com/Membrive92/gtaa-ai-validator)

> **📌 TRABAJO DE FIN DE MÁSTER - EN DESARROLLO INCREMENTAL**
>
> Autor: Jose Antonio Membrive Guillen
> Año: 2025-2026
> **Estado:** Fase 7/8 Completa | Última actualización: 2 Febrero 2026

---

## ⚠️ ESTADO DEL PROYECTO

> **IMPORTANTE:** Este README describe la **visión completa** del proyecto TFM.
> El desarrollo sigue una metodología incremental con 8 fases.
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
| **⏳ Fase 8** | **Optimización y documentación final** | **PENDIENTE** | — |

### 📊 Funcionalidades Implementadas vs Planeadas

| Funcionalidad | Estado | Notas |
|--------------|--------|-------|
| ✅ CLI con Click | Implementado | Acepta ruta de proyecto y opción --verbose |
| ✅ Descubrimiento de archivos test | Implementado | Soporta patrones test_*.py y *_test.py |
| ✅ Validación de entrada | Implementado | Verifica existencia de directorio |
| ✅ Análisis AST de código Python | Implementado | Visitor Pattern + ast.walk |
| ✅ Detección de 18 tipos de violaciones gTAA | Implementado | Fase 2-6 — 4 checkers + LLM |
| ✅ Sistema de scoring (0-100) | Implementado | Penalización por severidad |
| ✅ Proyectos de ejemplo (bueno/malo) | Implementado | En directorio examples/ |
| ✅ Tests unitarios + integración (274 tests) | Implementado | pytest con unit/ e integration/ |
| ✅ Documentación técnica con diagramas | Implementado | docs/ con flujos Fase 1-7 |
| ✅ Reportes HTML dashboard | Implementado | Fase 4 — SVG inline, autocontenido |
| ✅ Reportes JSON para CI/CD | Implementado | Fase 4 — `--json` / `--html` |
| ✅ Análisis semántico con LLM | Implementado | Fase 5 — Gemini Flash API + MockLLM fallback |
| ✅ Soporte proyectos mixtos (API + UI) | Implementado | Fase 7 — FileClassifier, .gtaa.yaml, auto-wait Playwright |
| ⏳ Optimización y documentación final | Pendiente | Fase 8 — prompts, CI/CD, docs TFM |

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

1. **🔍 Análisis Estático**: Pattern matching con AST y regex (12 violaciones)
2. **🧠 Análisis Semántico (LLM)**: Gemini Flash para detección profunda (6 violaciones)

### 🏆 Contribuciones Planificadas (TFM)

- 🎯 **Primera herramienta** que valida automáticamente gTAA (objetivo del TFM)
- ✅ **Sistema híbrido** que combina reglas estáticas + IA semántica (implementado Fase 5)
- ✅ **Detecta 18 tipos** de violaciones arquitectónicas (12 estáticas + 6 semánticas)
- ✅ **Reportes visuales** en HTML y JSON para CI/CD (implementado Fase 4)
- ✅ **Cobertura ampliada** con 5 nuevas violaciones basadas en catálogo CT-TAE (Fase 6)

---

## 🛠️ Stack Tecnológico

### Lenguajes y Frameworks
- **Python 3.8+** - Lenguaje principal
- **AST (Abstract Syntax Tree)** - Análisis sintáctico de código
- **Google Gemini Flash API** - LLM para análisis semántico (Fase 5)
- **PyYAML** - Configuración por proyecto .gtaa.yaml (✅ Fase 7)

### Librerías principales
```python
click>=8.0             # Interfaz CLI
google-genai>=1.0.0    # SDK Gemini Flash API (Fase 5)
python-dotenv>=1.0.0   # Carga de .env para API key
pytest>=7.0            # Framework de testing
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
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Membrive92/gtaa-ai-validator.git
cd gtaa-ai-validator

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo desarrollo
pip install -e .
```

---

### ✅ Funcionalidad ACTUAL (Fase 7)

**Funcionalidad disponible en la versión actual:**

```bash
# Análisis estático con detección de 12 tipos de violaciones estáticas
python -m gtaa_validator /path/to/your/selenium-project

# Modo verbose para ver detalles de cada violación
python -m gtaa_validator /path/to/project --verbose

# Análisis semántico AI (requiere GEMINI_API_KEY en .env)
python -m gtaa_validator /path/to/project --ai --verbose

# Configuración por proyecto (.gtaa.yaml)
python -m gtaa_validator /path/to/project --config /path/.gtaa.yaml

# Exportar reportes
python -m gtaa_validator examples/bad_project --html report.html
python -m gtaa_validator examples/bad_project --json report.json
python -m gtaa_validator examples/bad_project --ai --html report.html --json report.json --verbose

# Probar con ejemplos incluidos
python -m gtaa_validator examples/bad_project --verbose
python -m gtaa_validator examples/good_project

# Ejecutar tests
pytest tests/               # Todos (274 tests)
pytest tests/unit/          # Solo unitarios
pytest tests/integration/   # Solo integración
```

**Capacidades implementadas:**
- ✅ 4 checkers detectando 12 tipos de violaciones estáticas
- ✅ Análisis AST con Visitor Pattern (BrowserAPICallVisitor, AssertionVisitor, BusinessLogicVisitor, HardcodedDataVisitor)
- ✅ Análisis de estructura de proyecto (directorios requeridos)
- ✅ Detección por regex (emails, URLs, teléfonos, passwords, locators duplicados, configuración hardcodeada)
- ✅ Análisis semántico AI con Gemini Flash API (6 tipos de violación semántica)
- ✅ Sugerencias AI contextuales para cada violación (enriquecimiento)
- ✅ Fallback automático a MockLLMClient cuando no hay API key
- ✅ Clasificador de archivos API/UI con scoring ponderado (imports AST + código regex + path)
- ✅ Detección automática de Playwright auto-wait (salta MISSING_WAIT_STRATEGY)
- ✅ Configuración por proyecto .gtaa.yaml (exclude_checks, ignore_paths, api_test_patterns)
- ✅ Sistema de scoring 0-100 basado en severidad de violaciones
- ✅ Modo verbose con detalles: archivo, línea, código, mensaje, sugerencias AI
- ✅ Exit code 1 si hay violaciones críticas (útil para CI/CD)
- ✅ Reporte HTML dashboard autocontenido con SVG inline (score gauge, gráficos, tablas)
- ✅ Reporte JSON estructurado para integración CI/CD
- ✅ Flags `--json`, `--html`, `--ai` y `--config` compatibles entre sí
- ✅ 274 tests automatizados

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
├── bad_project/               # Proyecto con ~35 violaciones (todos los tipos)
│   ├── test_login.py          # 8 violaciones (Selenium directo)
│   ├── test_search.py         # 7 violaciones (Playwright directo)
│   ├── test_data_issues.py    # Datos hardcoded, nombres genéricos, función larga
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

### ⏳ Funcionalidad FUTURA — Fase 8: Optimización y Documentación Final

**Funcionalidades planificadas:**

#### Optimización de prompts LLM
```
# ⏳ Reducir tokens, mejorar precisión, evaluar cost/benefit
```

#### Integración CI/CD
```bash
# ⏳ PRÓXIMAMENTE - Validación en pipelines
python -m gtaa_validator . --min-score 70 --format json
```

#### Documentación TFM final
```
# ⏳ Revisión de estructura, documentación académica, PHASE7/8_FLOW_DIAGRAMS.md
```

---

## 📁 Estructura del Proyecto

```
gtaa-ai-validator/
│
├── README.md                           # Este archivo
├── LICENSE                             # Licencia MIT
├── requirements.txt                    # Dependencias Python
├── setup.py                            # Instalación del paquete
├── .gitignore                          # Archivos ignorados por Git
│
├── gtaa_validator/                     # 📦 Código fuente principal
│   ├── __init__.py                     # Inicialización del paquete
│   ├── __main__.py                     # Entry point CLI
│   ├── models.py                       # Modelos de datos (Violation, Report)
│   ├── file_classifier.py             # Clasificador API/UI (Fase 7)
│   ├── config.py                      # ProjectConfig + .gtaa.yaml (Fase 7)
│   │
│   ├── analyzers/                      # 🔍 Motores de análisis
│   │   ├── static_analyzer.py          # Orquestador estático (Facade Pattern)
│   │   └── semantic_analyzer.py        # Orquestador semántico AI (Fase 5)
│   │
│   ├── llm/                            # 🧠 Clientes LLM (Fase 5)
│   │   ├── client.py                   # MockLLMClient (heurísticas deterministas)
│   │   ├── gemini_client.py            # GeminiLLMClient (Gemini Flash API)
│   │   └── prompts.py                  # Templates de prompts para el modelo
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
│       └── quality_checker.py          # Calidad de tests (AST + Regex)
│
├── tests/                              # 🧪 Tests automatizados (274 tests)
│   ├── conftest.py                     # Fixtures compartidas
│   ├── unit/                           # Tests unitarios
│   │   ├── test_models.py             # Modelos de datos
│   │   ├── test_definition_checker.py # DefinitionChecker
│   │   ├── test_structure_checker.py  # StructureChecker
│   │   ├── test_adaptation_checker.py # AdaptationChecker
│   │   ├── test_quality_checker.py    # QualityChecker
│   │   ├── test_json_reporter.py      # JsonReporter
│   │   ├── test_html_reporter.py      # HtmlReporter
│   │   ├── test_llm_client.py         # MockLLMClient
│   │   ├── test_gemini_client.py      # GeminiLLMClient
│   │   ├── test_semantic_analyzer.py  # SemanticAnalyzer
│   │   ├── test_classifier.py        # FileClassifier (Fase 7)
│   │   └── test_config.py            # ProjectConfig (Fase 7)
│   └── integration/                    # Tests de integración
│       ├── test_static_analyzer.py    # Pipeline completo
│       └── test_reporters.py          # Análisis → JSON/HTML
│
├── examples/                           # 📝 Proyectos de ejemplo
│   ├── README.md                       # Documentación de violaciones
│   ├── bad_project/                    # Proyecto con ~35 violaciones
│   └── good_project/                   # Proyecto gTAA correcto (score 100)
│
├── .env.example                        # 🔑 Template para API key de Gemini
│
└── docs/                               # 📚 Documentación técnica
    ├── README.md                       # Índice de documentación
    ├── ARCHITECTURE_DECISIONS.md       # Decisiones arquitectónicas (27 ADR)
    ├── PHASE1_FLOW_DIAGRAMS.md         # Diagramas Fase 1 (CLI y fundación)
    ├── PHASE2_FLOW_DIAGRAMS.md         # Diagramas Fase 2 (análisis estático)
    ├── PHASE3_FLOW_DIAGRAMS.md         # Diagramas Fase 3 (9 violaciones)
    ├── PHASE4_FLOW_DIAGRAMS.md         # Diagramas Fase 4 (reportes)
    ├── PHASE5_FLOW_DIAGRAMS.md         # Diagramas Fase 5 (análisis semántico AI)
    ├── PHASE6_FLOW_DIAGRAMS.md         # Diagramas Fase 6 (18 violaciones)
    └── PHASE7_FLOW_DIAGRAMS.md         # Diagramas Fase 7 (proyectos mixtos)
```

> **Nota sobre `docs/`**: La documentación técnica se distribuye en múltiples documentos independientes, uno por cada fase del proyecto y uno para las decisiones arquitectónicas. Esta separación responde a un criterio de **transparencia y trazabilidad**: cada documento refleja el estado del proyecto en el momento de su elaboración, permitiendo seguir la evolución del diseño y las decisiones técnicas a lo largo del desarrollo. El índice general se encuentra en [`docs/README.md`](docs/README.md).

---

## ⚙️ Funcionalidades Principales

### 1. 🔍 Detección de Violaciones Arquitectónicas

#### 4 Checkers — 12 tipos de violaciones estáticas

| Severidad | Tipo | Checker | Técnica |
|-----------|------|---------|---------|
| 🔴 CRÍTICA | `ADAPTATION_IN_DEFINITION` | DefinitionChecker | AST Visitor (BrowserAPICallVisitor) |
| 🔴 CRÍTICA | `MISSING_LAYER_STRUCTURE` | StructureChecker | Sistema de archivos (iterdir) |
| 🟡 ALTA | `HARDCODED_TEST_DATA` | QualityChecker | AST Visitor + Regex |
| 🟡 ALTA | `ASSERTION_IN_POM` | AdaptationChecker | AST Visitor |
| 🟡 ALTA | `FORBIDDEN_IMPORT` | AdaptationChecker | ast.walk |
| 🟡 ALTA | `HARDCODED_CONFIGURATION` | QualityChecker | Regex (localhost, sleep, paths) |
| 🟡 ALTA | `SHARED_MUTABLE_STATE` | QualityChecker | AST (Assign + Global) |
| 🟠 MEDIA | `BUSINESS_LOGIC_IN_POM` | AdaptationChecker | AST Visitor |
| 🟠 MEDIA | `DUPLICATE_LOCATOR` | AdaptationChecker | Regex + Registro cross-file |
| 🟠 MEDIA | `LONG_TEST_FUNCTION` | QualityChecker | ast.walk + lineno |
| 🟠 MEDIA | `BROAD_EXCEPTION_HANDLING` | QualityChecker | AST (ExceptHandler) |
| 🟢 BAJA | `POOR_TEST_NAMING` | QualityChecker | ast.walk + Regex |

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

### 4. 🧠 Análisis Semántico con IA (✅ Fase 5-6)

**Activado con `--ai`:**
- Detección de 6 tipos de violaciones semánticas que AST no puede capturar
- Sugerencias AI contextuales en español para cada violación
- Gemini Flash API (free tier) con fallback a MockLLMClient
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
1. ✅ Desarrollar sistema de IA para validación arquitectónica (Fase 7/8 completa)
2. ✅ Integrar LLM real para análisis semántico (Gemini Flash - Fase 5)
3. ✅ Ampliar cobertura a 18 tipos de violación basados en catálogo CT-TAE (Fase 6)
4. ✅ Crear dataset etiquetado para la comunidad (ejemplos con ground truth)

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
- ⏳ Fase 8: Optimización y documentación final - **PENDIENTE**

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
- **[Decisiones Arquitectónicas (ADR)](docs/ARCHITECTURE_DECISIONS.md)** ✅ — Patrones de diseño, paradigmas, justificaciones técnicas
- **[Diagramas de Flujo - Fase 1](docs/PHASE1_FLOW_DIAGRAMS.md)** ✅ — Fundación del proyecto, CLI con Click, descubrimiento de archivos
- **[Diagramas de Flujo - Fase 2](docs/PHASE2_FLOW_DIAGRAMS.md)** ✅ — Motor de análisis estático, BrowserAPICallVisitor, scoring
- **[Diagramas de Flujo - Fase 3](docs/PHASE3_FLOW_DIAGRAMS.md)** ✅ — 4 checkers, 9 violaciones, AST visitors, cross-file state
- **[Diagramas de Flujo - Fase 4](docs/PHASE4_FLOW_DIAGRAMS.md)** ✅ — Reportes JSON/HTML, SVG inline, agrupación por checker
- **[Diagramas de Flujo - Fase 5](docs/PHASE5_FLOW_DIAGRAMS.md)** ✅ — Análisis semántico AI, Gemini Flash, prompt engineering, parsing LLM
- **[Diagramas de Flujo - Fase 6](docs/PHASE6_FLOW_DIAGRAMS.md)** ✅ — Ampliación a 18 violaciones, nuevos checkers, heurísticas mock
- **[Diagramas de Flujo - Fase 7](docs/PHASE7_FLOW_DIAGRAMS.md)** ✅ — Proyectos mixtos API+UI, FileClassifier, .gtaa.yaml, auto-wait Playwright
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

### Versión 0.8.0 - Fase 8 (Pendiente) ⏳

**Planificado:**
- ⏳ Optimización de prompts LLM (reducir tokens, mejorar precisión)
- ⏳ Integración CI/CD (`--min-score`, exit codes)
- ⏳ Documentación TFM final
- ⏳ PHASE8_FLOW_DIAGRAMS.md

---

<div align="center">

**Estado del proyecto:** Fase 7/8 | 18 violaciones | 274 tests

</div>
