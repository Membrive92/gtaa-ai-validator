# 🤖 gTAA AI Validator

**Sistema Híbrido de IA para Validación Automática de Arquitectura de Test Automation: Análisis Estático y Semántico con LLMs**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)](https://github.com/Membrive92/gtaa-ai-validator)
[![Fase](https://img.shields.io/badge/fase-4%2F6%20completa-blue)](https://github.com/Membrive92/gtaa-ai-validator)
[![Progreso](https://img.shields.io/badge/progreso-67%25-yellow)](https://github.com/Membrive92/gtaa-ai-validator)

> **📌 TRABAJO DE FIN DE MÁSTER - EN DESARROLLO INCREMENTAL**
>
> Autor: Jose Antonio Membrive Guillen
> Año: 2025-2026
> **Estado:** Fase 4/6 Completa | Última actualización: 31 Enero 2026

---

## ⚠️ ESTADO DEL PROYECTO

> **IMPORTANTE:** Este README describe la **visión completa** del proyecto TFM.
> El desarrollo sigue una metodología incremental con 6 fases.
> Funcionalidades marcadas con ⏳ están pendientes de implementación.

### 🚀 Estado de Implementación por Fases

| Fase | Componente | Estado | Fecha Completada |
|------|-----------|--------|------------------|
| **✅ Fase 1** | **CLI básico y descubrimiento de archivos** | **COMPLETO** | **26/01/2026** |
| **✅ Fase 2** | **Análisis estático con AST (1 violación)** | **COMPLETO** | **26/01/2026** |
| **✅ Fase 3** | **Cobertura completa (9 tipos de violaciones) + Tests** | **COMPLETO** | **28/01/2026** |
| **✅ Fase 4** | **Reportes HTML/JSON profesionales** | **COMPLETO** | **31/01/2026** |
| ⏳ Fase 5 | Integración LLM (opcional, sin API key aún) | Pendiente | - |
| ⏳ Fase 6 | Validación empírica y documentación TFM | Pendiente | - |

### 📊 Funcionalidades Implementadas vs Planeadas

| Funcionalidad | Estado | Notas |
|--------------|--------|-------|
| ✅ CLI con Click | Implementado | Acepta ruta de proyecto y opción --verbose |
| ✅ Descubrimiento de archivos test | Implementado | Soporta patrones test_*.py y *_test.py |
| ✅ Validación de entrada | Implementado | Verifica existencia de directorio |
| ✅ Análisis AST de código Python | Implementado | Visitor Pattern + ast.walk |
| ✅ Detección de 9 tipos de violaciones gTAA | Implementado | Fase 2-3 — 4 checkers |
| ✅ Sistema de scoring (0-100) | Implementado | Penalización por severidad |
| ✅ Proyectos de ejemplo (bueno/malo) | Implementado | En directorio examples/ |
| ✅ Tests unitarios + integración (165 tests) | Implementado | pytest con unit/ e integration/ |
| ✅ Documentación técnica con diagramas | Implementado | docs/ con flujos Fase 1-4 |
| ✅ Reportes HTML dashboard | Implementado | Fase 4 — SVG inline, autocontenido |
| ✅ Reportes JSON para CI/CD | Implementado | Fase 4 — `--json` / `--html` |
| ⏳ Análisis semántico con LLM | Pendiente | Fase 5 (opcional) |
| ⏳ Clasificador ML (Random Forest) | Pendiente | Fase 7 (opcional) |

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

1. **🔍 Análisis Estático**: Pattern matching con AST y regex
2. **🧠 Análisis Semántico (LLM)**: Claude/GPT-4 para detección profunda
3. **📊 Clasificador ML**: Random Forest entrenado con código etiquetado

### 🏆 Contribuciones Planificadas (TFM)

- 🎯 **Primera herramienta** que valida automáticamente gTAA (objetivo del TFM)
- 🎯 **Sistema híbrido** que combina reglas estáticas + IA semántica (en desarrollo)
- ✅ **Detecta 9 tipos** de violaciones arquitectónicas (implementado Fase 3)
- ✅ **Reportes visuales** en HTML y JSON para CI/CD (implementado Fase 4)
- 🎯 **Validación empírica** con proyectos reales (pendiente Fase 6)

---

## 🛠️ Stack Tecnológico

### Lenguajes y Frameworks
- **Python 3.8+** - Lenguaje principal
- **AST (Abstract Syntax Tree)** - Análisis sintáctico de código
- **Anthropic Claude API** - LLM para análisis semántico (futuro)
- **scikit-learn** - Clasificador ML (opcional)

### Librerías principales
```python
click>=8.0             # Interfaz CLI
pytest>=7.0            # Framework de testing
# Futuro:
# anthropic>=0.18.0    # API de Claude (Fase 5)
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
│  AST + Regex │    │  LLM (Claude)    │
│  4 Checkers  │    │  ⏳ Pendiente    │
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

### ✅ Funcionalidad ACTUAL (Fase 4)

**Funcionalidad disponible en la versión actual:**

```bash
# Análisis estático con detección de 9 tipos de violaciones
python -m gtaa_validator /path/to/your/selenium-project

# Modo verbose para ver detalles de cada violación
python -m gtaa_validator /path/to/project --verbose

# Exportar reportes
python -m gtaa_validator examples/bad_project --html report.html
python -m gtaa_validator examples/bad_project --json report.json
python -m gtaa_validator examples/bad_project --html report.html --json report.json --verbose

# Probar con ejemplos incluidos
python -m gtaa_validator examples/bad_project --verbose
python -m gtaa_validator examples/good_project

# Ejecutar tests
pytest tests/               # Todos (165 tests)
pytest tests/unit/          # Solo unitarios (143 tests)
pytest tests/integration/   # Solo integración (22 tests)
```

**Capacidades implementadas:**
- ✅ 4 checkers detectando 9 tipos de violaciones
- ✅ Análisis AST con Visitor Pattern (BrowserAPICallVisitor, AssertionVisitor, BusinessLogicVisitor, HardcodedDataVisitor)
- ✅ Análisis de estructura de proyecto (directorios requeridos)
- ✅ Detección por regex (emails, URLs, teléfonos, passwords, locators duplicados)
- ✅ Sistema de scoring 0-100 basado en severidad de violaciones
- ✅ Modo verbose con detalles: archivo, línea, código, mensaje
- ✅ Exit code 1 si hay violaciones críticas (útil para CI/CD)
- ✅ Reporte HTML dashboard autocontenido con SVG inline (score gauge, gráficos, tablas)
- ✅ Reporte JSON estructurado para integración CI/CD
- ✅ Flags `--json` y `--html` compatibles entre sí y con salida de texto
- ✅ 165 tests automatizados (143 unitarios + 22 integración)

**Ejemplo de salida:**
```
=== gTAA AI Validator - Fase 4 ===
Analizando proyecto: examples/bad_project

Ejecutando análisis estático...

============================================================
RESULTADOS DEL ANÁLISIS
============================================================

Archivos analizados: 6
Violaciones totales: 35

Violaciones por severidad:
  CRÍTICA: 16
  ALTA:    13
  MEDIA:   4
  BAJA:    2

Puntuación de cumplimiento: 0.0/100
Estado: PROBLEMAS CRÍTICOS

============================================================
Análisis completado en 0.00s
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

### ⏳ Funcionalidad FUTURA (Fases 5-6)

**Las siguientes funcionalidades están PENDIENTES de implementación:**

#### Fase 5: Análisis con IA
```bash
# ⏳ PRÓXIMAMENTE - Análisis semántico con LLM (requiere API key)
export ANTHROPIC_API_KEY="sk-ant-..."
python -m gtaa_validator /path/to/project --use-ai
```

#### Integración CI/CD
```bash
# ⏳ PRÓXIMAMENTE - Validación en pipelines
python -m gtaa_validator . --min-score 70 --format json
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
│   │
│   ├── analyzers/                      # 🔍 Motores de análisis
│   │   └── static_analyzer.py          # Orquestador (Facade Pattern)
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
├── tests/                              # 🧪 Tests automatizados (165 tests)
│   ├── conftest.py                     # Fixtures compartidas
│   ├── unit/                           # Tests unitarios (143 tests)
│   │   ├── test_models.py             # Modelos de datos
│   │   ├── test_definition_checker.py # DefinitionChecker
│   │   ├── test_structure_checker.py  # StructureChecker
│   │   ├── test_adaptation_checker.py # AdaptationChecker
│   │   ├── test_quality_checker.py    # QualityChecker
│   │   ├── test_json_reporter.py      # JsonReporter
│   │   └── test_html_reporter.py      # HtmlReporter
│   └── integration/                    # Tests de integración (22 tests)
│       ├── test_static_analyzer.py    # Pipeline completo
│       └── test_reporters.py          # Análisis → JSON/HTML
│
├── examples/                           # 📝 Proyectos de ejemplo
│   ├── README.md                       # Documentación de violaciones
│   ├── bad_project/                    # Proyecto con ~35 violaciones
│   └── good_project/                   # Proyecto gTAA correcto (score 100)
│
└── docs/                               # 📚 Documentación técnica
    ├── README.md                       # Índice de documentación
    ├── ARCHITECTURE_DECISIONS.md       # Decisiones arquitectónicas (ADR)
    ├── PHASE1_FLOW_DIAGRAMS.md         # Diagramas Fase 1 (CLI y fundación)
    ├── PHASE2_FLOW_DIAGRAMS.md         # Diagramas Fase 2
    ├── PHASE3_FLOW_DIAGRAMS.md         # Diagramas Fase 3
    └── PHASE4_FLOW_DIAGRAMS.md         # Diagramas Fase 4 (Reportes)
```

> **Nota sobre `docs/`**: La documentación técnica se distribuye en múltiples documentos independientes, uno por cada fase del proyecto y uno para las decisiones arquitectónicas. Esta separación responde a un criterio de **transparencia y trazabilidad**: cada documento refleja el estado del proyecto en el momento de su elaboración, permitiendo seguir la evolución del diseño y las decisiones técnicas a lo largo del desarrollo. El índice general se encuentra en [`docs/README.md`](docs/README.md).

---

## ⚙️ Funcionalidades Principales

### 1. 🔍 Detección de Violaciones Arquitectónicas

#### 4 Checkers — 9 tipos de violaciones

| Severidad | Tipo | Checker | Técnica |
|-----------|------|---------|---------|
| 🔴 CRÍTICA | `ADAPTATION_IN_DEFINITION` | DefinitionChecker | AST Visitor (BrowserAPICallVisitor) |
| 🔴 CRÍTICA | `MISSING_LAYER_STRUCTURE` | StructureChecker | Sistema de archivos (iterdir) |
| 🟡 ALTA | `HARDCODED_TEST_DATA` | QualityChecker | AST Visitor + Regex |
| 🟡 ALTA | `ASSERTION_IN_POM` | AdaptationChecker | AST Visitor |
| 🟡 ALTA | `FORBIDDEN_IMPORT` | AdaptationChecker | ast.walk |
| 🟠 MEDIA | `BUSINESS_LOGIC_IN_POM` | AdaptationChecker | AST Visitor |
| 🟠 MEDIA | `DUPLICATE_LOCATOR` | AdaptationChecker | Regex + Registro cross-file |
| 🟠 MEDIA | `LONG_TEST_FUNCTION` | QualityChecker | ast.walk + lineno |
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

### 4. 🧠 Análisis Semántico con IA (⏳ Fase 5)

**Componente de LLM:**
- Detección de violaciones semánticas que reglas estáticas no pueden capturar
- Análisis contextual del código
- Recomendaciones inteligentes de refactorización

---

## 🎓 Contexto Académico (TFM)

### Objetivos del TFM
1. ✅ Desarrollar sistema de IA para validación arquitectónica (Fase 4/6 completa)
2. 🎯 Comparar análisis estático vs semántico (LLM) (pendiente - Fase 5)
3. 🎯 Demostrar viabilidad de LLMs en code analysis (pendiente - Fase 5)
4. ✅ Crear dataset etiquetado para la comunidad (ejemplos con ground truth)

### Tecnologías de IA a Utilizar
- **Abstract Syntax Tree (AST)** para análisis estático (✅ Implementado)
- **Regex patterns** para detección de datos y locators (✅ Implementado)
- **Large Language Models** (Claude - ⏳ Fase 5)
- **Machine Learning** (Random Forest - opcional)

### Metodología
**Desarrollo Incremental:**
- ✅ Fase 1: Fundación (CLI básico) - **COMPLETA**
- ✅ Fase 2: Motor de análisis estático con AST (1 violación) - **COMPLETA**
- ✅ Fase 3: Cobertura completa (9 violaciones) + Tests (140) - **COMPLETA**
- ✅ Fase 4: Reportes HTML/JSON profesionales - **COMPLETA**
- ⏳ Fase 5: Integración LLM y comparativa
- ⏳ Fase 6: Validación empírica y documentación TFM

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
| QualityChecker | HARDCODED_TEST_DATA, LONG_TEST_FUNCTION, POOR_TEST_NAMING | AST Visitor + Regex |

**Próximos pasos:** Fase 5 - Integración LLM (análisis semántico)

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

**Próximos pasos:** Fase 5 - Integración LLM (análisis semántico)

---

<div align="center">

**Estado del proyecto:** En desarrollo activo | Fase 4/6 completa

</div>
