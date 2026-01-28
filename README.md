# 🤖 gTAA AI Validator

**Sistema Híbrido de IA para Validación Automática de Arquitectura de Test Automation: Análisis Estático y Semántico con LLMs**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)](https://github.com/Membrive92/gtaa-ai-validator)
[![Fase](https://img.shields.io/badge/fase-3%2F6%20completa-blue)](https://github.com/Membrive92/gtaa-ai-validator)
[![Progreso](https://img.shields.io/badge/progreso-50%25-orange)](https://github.com/Membrive92/gtaa-ai-validator)

> **📌 TRABAJO DE FIN DE MÁSTER - EN DESARROLLO INCREMENTAL**
>
> Autor: Jose Antonio Membrive Guillen
> Universidad: [Tu Universidad]
> Año: 2025-2026
> **Estado:** Fase 3/6 Completa | Última actualización: 28 Enero 2026

---

## ⚠️ ESTADO DEL PROYECTO

> **IMPORTANTE:** Este README describe la **visión completa** del proyecto TFM.
> El desarrollo sigue una metodología incremental con 6 fases.
> Funcionalidades marcadas con ⏳ están pendientes de implementación.

### 🚀 Estado de Implementación por Fases

| Fase | Componente | Estado | Fecha Completada |
|------|-----------|--------|------------------|
| **✅ Fase 1** | **CLI básico y descubrimiento de archivos** | **COMPLETO** | **26/01/2025** |
| **✅ Fase 2** | **Análisis estático con AST (1 violación)** | **COMPLETO** | **26/01/2025** |
| **✅ Fase 3** | **Cobertura completa (9 tipos de violaciones) + Tests** | **COMPLETO** | **28/01/2026** |
| ⏳ Fase 4 | Reportes HTML/JSON profesionales | Pendiente | - |
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
| ✅ Tests unitarios + integración (140 tests) | Implementado | pytest con unit/ e integration/ |
| ✅ Documentación técnica con diagramas | Implementado | docs/ con flujos Fase 2 y 3 |
| ⏳ Reportes HTML interactivos | Pendiente | Fase 4 |
| ⏳ Reportes JSON para CI/CD | Pendiente | Fase 4 |
| ⏳ Análisis semántico con LLM | Pendiente | Fase 5 (opcional) |
| ⏳ Clasificador ML (Random Forest) | Pendiente | Fase 7 (opcional) |

**Leyenda:** ✅ Implementado | ⏳ Pendiente

---

## 📖 Descripción General del Proyecto

**gTAA AI Validator** es una herramienta de análisis automático que valida el cumplimiento de la arquitectura **gTAA (Generic Test Automation Architecture)** definida en el estándar **ISTQB CT-TAE (Certified Tester Advanced Level - Test Automation Engineer)**.

### 🎯 Problema que resuelve

Los frameworks de test automation (Selenium, Playwright, Cypress) frecuentemente se desarrollan sin seguir principios arquitectónicos sólidos, resultando en:
- ❌ Código difícil de mantener
- ❌ Tests frágiles que fallan con cualquier cambio
- ❌ Violación de principios de separación de responsabilidades
- ❌ Mezcla de capas arquitectónicas (Definition, Adaptation, Execution)

### ✨ Solución propuesta

Sistema híbrido que combina **3 técnicas de IA** para detectar automáticamente violaciones arquitectónicas:

1. **🔍 Análisis Estático**: Pattern matching con AST y regex
2. **🧠 Análisis Semántico (LLM)**: Claude/GPT-4 para detección profunda
3. **📊 Clasificador ML**: Random Forest entrenado con código etiquetado

### 🏆 Contribuciones Planificadas (TFM)

- 🎯 **Primera herramienta** que valida automáticamente gTAA (objetivo del TFM)
- 🎯 **Sistema híbrido** que combina reglas estáticas + IA semántica (en desarrollo)
- ✅ **Detecta 9 tipos** de violaciones arquitectónicas (implementado Fase 3)
- 🎯 **Reportes visuales** en HTML y JSON para CI/CD (pendiente Fase 4)
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
# jinja2>=3.0          # Reportes HTML (Fase 4)
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
git clone https://github.com/tu-usuario/gtaa-ai-validator.git
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

### ✅ Funcionalidad ACTUAL (Fase 3)

**Lo que puedes hacer AHORA:**

```bash
# Análisis estático con detección de 9 tipos de violaciones
python -m gtaa_validator /path/to/your/selenium-project

# Modo verbose para ver detalles de cada violación
python -m gtaa_validator /path/to/project --verbose

# Probar con ejemplos incluidos
python -m gtaa_validator examples/bad_project --verbose
python -m gtaa_validator examples/good_project

# Ejecutar tests
pytest tests/               # Todos (140 tests)
pytest tests/unit/          # Solo unitarios (122 tests)
pytest tests/integration/   # Solo integración (18 tests)
```

**Capacidades implementadas:**
- ✅ 4 checkers detectando 9 tipos de violaciones
- ✅ Análisis AST con Visitor Pattern (BrowserAPICallVisitor, AssertionVisitor, BusinessLogicVisitor, HardcodedDataVisitor)
- ✅ Análisis de estructura de proyecto (directorios requeridos)
- ✅ Detección por regex (emails, URLs, teléfonos, passwords, locators duplicados)
- ✅ Sistema de scoring 0-100 basado en severidad de violaciones
- ✅ Modo verbose con detalles: archivo, línea, código, mensaje
- ✅ Exit code 1 si hay violaciones críticas (útil para CI/CD)
- ✅ 140 tests automatizados (122 unitarios + 18 integración)

**Ejemplo de salida:**
```
=== gTAA AI Validator - Fase 3 ===
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
- ✅ **Checklist de validación**: Para evaluadores y profesores
- ✅ **Ground truth etiquetado**: Dataset para validación empírica del TFM

---

### ⏳ Funcionalidad FUTURA (Fases 4-6)

**Las siguientes funcionalidades están PENDIENTES de implementación:**

#### Fase 4: Reportes profesionales
```bash
# ⏳ PRÓXIMAMENTE - Generar reportes HTML
python -m gtaa_validator /path/to/project --format html --output report.html

# ⏳ PRÓXIMAMENTE - Generar reportes JSON para CI/CD
python -m gtaa_validator /path/to/project --format json --output report.json
```

#### Fase 5: Análisis con IA
```bash
# ⏳ PRÓXIMAMENTE - Análisis semántico con LLM (requiere API key)
export ANTHROPIC_API_KEY="tu-api-key"
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
│   └── checkers/                       # ✅ Detectores de violaciones
│       ├── base.py                     # Clase base abstracta (Strategy Pattern)
│       ├── definition_checker.py       # Test Definition Layer (AST Visitor)
│       ├── structure_checker.py        # Estructura del proyecto (Filesystem)
│       ├── adaptation_checker.py       # Test Adaptation Layer (AST + Regex)
│       └── quality_checker.py          # Calidad de tests (AST + Regex)
│
├── tests/                              # 🧪 Tests automatizados (140 tests)
│   ├── conftest.py                     # Fixtures compartidas
│   ├── unit/                           # Tests unitarios (122 tests)
│   │   ├── test_models.py             # Modelos de datos
│   │   ├── test_definition_checker.py # DefinitionChecker
│   │   ├── test_structure_checker.py  # StructureChecker
│   │   ├── test_adaptation_checker.py # AdaptationChecker
│   │   └── test_quality_checker.py    # QualityChecker
│   └── integration/                    # Tests de integración (18 tests)
│       └── test_static_analyzer.py    # Pipeline completo
│
├── examples/                           # 📝 Proyectos de ejemplo
│   ├── README.md                       # Documentación de violaciones
│   ├── bad_project/                    # Proyecto con ~35 violaciones
│   └── good_project/                   # Proyecto gTAA correcto (score 100)
│
└── docs/                               # 📚 Documentación técnica
    ├── README.md                       # Índice de documentación
    ├── PHASE2_FLOW_DIAGRAMS.md         # Diagramas Fase 2
    └── PHASE3_FLOW_DIAGRAMS.md         # Diagramas Fase 3
```

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

### 3. 📈 Reportes Visuales (⏳ Fase 4)

#### Reporte HTML
- Dashboard interactivo
- Violaciones agrupadas por severidad
- Fragmentos de código resaltados
- Recomendaciones de corrección

#### Reporte JSON
- Formato estructurado para CI/CD
- Integración con pipelines

### 4. 🧠 Análisis Semántico con IA (⏳ Fase 5)

**Componente de LLM:**
- Detección de violaciones semánticas que reglas estáticas no pueden capturar
- Análisis contextual del código
- Recomendaciones inteligentes de refactorización

---

## 🎓 Contexto Académico (TFM)

### Objetivos del TFM
1. ✅ Desarrollar sistema de IA para validación arquitectónica (Fase 3/6 completa)
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
- ⏳ Fase 4: Reportes HTML/JSON profesionales
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
- **[Diagramas de Flujo - Fase 2](docs/PHASE2_FLOW_DIAGRAMS.md)** ✅ — Motor de análisis estático, BrowserAPICallVisitor, scoring
- **[Diagramas de Flujo - Fase 3](docs/PHASE3_FLOW_DIAGRAMS.md)** ✅ — 4 checkers, 9 violaciones, AST visitors, cross-file state
- **[Índice de documentación](docs/README.md)** ✅

---

## 📝 Historial de Desarrollo

### Versión 0.1.0 - Fase 1 (26 Enero 2025) ✅

**Implementado:**
- ✅ Estructura básica del proyecto (setup.py, requirements.txt, etc.)
- ✅ CLI funcional con Click framework
- ✅ Descubrimiento recursivo de archivos de test
- ✅ Modo verbose para output detallado

---

### Versión 0.2.0 - Fase 2 (26 Enero 2025) ✅

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
- ✅ 140 tests automatizados (122 unitarios + 18 integración)
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

**Próximos pasos:** Fase 4 - Reportes HTML/JSON profesionales

---

<div align="center">

**⭐ Si este proyecto te resulta interesante, síguelo para ver su evolución ⭐**

**Estado del proyecto:** 🚧 En desarrollo activo | Fase 3/6 completa

</div>
