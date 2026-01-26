# 🤖 gTAA AI Validator

**Sistema Híbrido de IA para Validación Automática de Arquitectura de Test Automation: Análisis Estático y Semántico con LLMs**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-in%20development-yellow)](https://github.com/yourusername/gtaa-ai-validator)
[![Phase](https://img.shields.io/badge/phase-2%2F6%20complete-blue)](https://github.com/yourusername/gtaa-ai-validator)
[![Progress](https://img.shields.io/badge/progress-35%25-orange)](https://github.com/yourusername/gtaa-ai-validator)

> **📌 TRABAJO DE FIN DE MÁSTER - EN DESARROLLO INCREMENTAL**
>
> Autor: Jose Antonio Membrive Guillen
> Universidad: [Tu Universidad]
> Año: 2025
> **Estado:** Fase 2/6 Completa | Última actualización: 26 Enero 2025

---

## ⚠️ ESTADO DEL PROYECTO

> **IMPORTANTE:** Este README describe la **visión completa** del proyecto TFM.
> El desarrollo sigue una metodología incremental con 6 fases.
> Funcionalidades marcadas con ⏳ están pendientes de implementación.

### 🚀 Estado de Implementación por Fases

| Fase | Componente | Estado | Fecha Completada |
|------|-----------|--------|------------------|
| **✅ Fase 1** | **CLI básico y descubrimiento de archivos** | **COMPLETO** | **26/01/2025** |
| **✅ Fase 2** | **Análisis estático con AST y detección de violaciones** | **COMPLETO** | **26/01/2025** |
| ⏳ Fase 3 | Cobertura completa (9 tipos de violaciones) | Pendiente | - |
| ⏳ Fase 4 | Reportes HTML/JSON profesionales | Pendiente | - |
| ⏳ Fase 5 | Tests unitarios y proyectos de ejemplo | Pendiente | - |
| ⏳ Fase 6 | Integración LLM (opcional, sin API key aún) | Pendiente | - |

### 📊 Funcionalidades Implementadas vs Planeadas

| Funcionalidad | Estado | Notas |
|--------------|--------|-------|
| ✅ CLI con Click | Implementado | Acepta ruta de proyecto y opción --verbose |
| ✅ Descubrimiento de archivos test | Implementado | Soporta patrones test_*.py y *_test.py |
| ✅ Validación de entrada | Implementado | Verifica existencia de directorio |
| ✅ Análisis AST de código Python | Implementado | Fase 2 - Visitor Pattern |
| ✅ Detección de violaciones gTAA | Implementado | Fase 2 - ADAPTATION_IN_DEFINITION |
| ✅ Sistema de scoring (0-100) | Implementado | Fase 2 - Penalización por severidad |
| ✅ Proyectos de ejemplo (bueno/malo) | Implementado | Fase 2 - En directorio examples/ |
| ⏳ Reportes HTML interactivos | Pendiente | Fase 4 |
| ⏳ Reportes JSON para CI/CD | Pendiente | Fase 4 |
| ⏳ Tests unitarios con pytest | Pendiente | Fase 5 |
| ⏳ Proyectos de ejemplo (bueno/malo) | Pendiente | Fase 5 |
| ⏳ Análisis semántico con LLM | Pendiente | Fase 6 (opcional) |
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
- 🎯 **Detecta 9+ tipos** de violaciones arquitectónicas (pendiente Fase 2-3)
- 🎯 **Reportes visuales** en HTML y JSON para CI/CD (pendiente Fase 4)
- 🎯 **Validación empírica** con proyectos reales (pendiente Fase 5)

---

## 🛠️ Stack Tecnológico

### Lenguajes y Frameworks
- **Python 3.10+** - Lenguaje principal
- **AST (Abstract Syntax Tree)** - Análisis sintáctico de código
- **Anthropic Claude API** - LLM para análisis semántico
- **scikit-learn** - Clasificador ML (opcional)

### Librerías principales
```python
anthropic>=0.18.0      # Claude API
click>=8.0             # CLI interface
jinja2>=3.0            # HTML reports
pytest>=7.0            # Testing framework
radon>=5.0             # Code complexity metrics
```

### Herramientas de desarrollo
- **Git/GitHub** - Control de versiones
- **pytest** - Tests unitarios
- **black** - Code formatting
- **mypy** - Type checking (opcional)

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

### Instalación (Fase 1)

#### Instalación desde código fuente
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/gtaa-ai-validator.git
cd gtaa-ai-validator

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias (actualmente solo Click)
pip install -r requirements.txt

# Instalar en modo desarrollo
pip install -e .
```

---

### ✅ Funcionalidad ACTUAL (Fase 2)

**Lo que puedes hacer AHORA:**

```bash
# Análisis estático con detección de violaciones
python -m gtaa_validator /path/to/your/selenium-project

# Modo verbose para ver detalles de cada violación
python -m gtaa_validator /path/to/project --verbose

# Probar con ejemplos incluidos
python -m gtaa_validator examples/bad_project
python -m gtaa_validator examples/good_project
```

**Capacidades implementadas:**
- ✅ Análisis AST (Abstract Syntax Tree) de código Python
- ✅ Detección de violación `ADAPTATION_IN_DEFINITION` (Selenium/Playwright en tests)
- ✅ Sistema de scoring 0-100 basado en severidad de violaciones
- ✅ Resumen de violaciones por severidad (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Modo verbose con detalles: archivo, línea, código, mensaje
- ✅ Exit code 1 si hay violaciones críticas (útil para CI/CD)
- ✅ Proyectos de ejemplo documentados en `examples/`

**Ejemplo de salida:**
```
=== gTAA AI Validator - Phase 2 ===
Analyzing project: examples/bad_project

Running static analysis...

============================================================
ANALYSIS RESULTS
============================================================

Files analyzed: 2
Total violations: 15

Violations by severity:
  CRITICAL: 15
  HIGH:     0
  MEDIUM:   0
  LOW:      0

Compliance Score: 0.0/100
Status: CRITICAL ISSUES

============================================================
Analysis completed in 0.00s
============================================================
```

---

## 📚 Proyectos de Ejemplo

El proyecto incluye ejemplos completamente documentados en el directorio [examples/](examples/).

### Estructura

```
examples/
├── README.md           # Documentación detallada de cada ejemplo
├── bad_project/        # Proyecto con 15 violaciones CRITICAL
│   ├── test_login.py   # 8 violaciones (Selenium directo)
│   └── test_search.py  # 7 violaciones (Playwright directo)
└── good_project/       # Proyecto con arquitectura gTAA correcta
    ├── tests/
    │   └── test_login.py   # Tests usando Page Objects
    └── pages/
        └── login_page.py   # Page Object que encapsula Selenium
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
- ✅ **Métricas calculables**: Precisión, recall, exactitud de línea
- ✅ **Ground truth etiquetado**: Dataset para validación empírica del TFM

**Propósito académico:**
Estos ejemplos permiten a evaluadores del TFM:
1. Ejecutar el validador inmediatamente sin preparación
2. Verificar que detecta exactamente las 15 violaciones documentadas
3. Cruzar resultados con el ground truth etiquetado
4. Reproducir resultados de forma determinística

---

### ⏳ Funcionalidad FUTURA (Fases 3-6)

**Las siguientes funcionalidades están PENDIENTES de implementación:**

#### Fase 3: Cobertura completa de violaciones
```bash
# ⏳ PRÓXIMAMENTE - Detectar violaciones arquitectónicas
python -m gtaa_validator /path/to/project
# Output esperado: Lista de violaciones, score 0-100
```

#### Fase 4: Reportes profesionales
```bash
# ⏳ PRÓXIMAMENTE - Generar reportes HTML
python -m gtaa_validator /path/to/project --format html --output report.html

# ⏳ PRÓXIMAMENTE - Generar reportes JSON para CI/CD
python -m gtaa_validator /path/to/project --format json --output report.json
```

#### Fase 5: Ejemplos demostrativos
```bash
# ⏳ PRÓXIMAMENTE - Probar con proyectos de ejemplo incluidos
cd examples
python test_analyzer.py
```

#### Fase 6: Análisis con IA
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
│   │   ├── static_analyzer.py          # Análisis estático (AST + regex)
│   │   ├── ai_analyzer.py              # Análisis semántico (LLM)
│   │   └── ml_classifier.py            # Clasificador ML (opcional)
│   │
│   ├── checkers/                       # ✅ Detectores de violaciones
│   │   ├── base.py                     # Clase base abstracta
│   │   ├── definition_checker.py       # Test Definition Layer
│   │   ├── adaptation_checker.py       # Test Adaptation Layer
│   │   └── structure_checker.py        # Estructura del proyecto
│   │
│   ├── reporters/                      # 📊 Generadores de reportes
│   │   ├── html_reporter.py            # Reportes HTML interactivos
│   │   └── json_reporter.py            # Reportes JSON (CI/CD)
│   │
│   └── utils/                          # 🛠️ Utilidades
│       ├── scorer.py                   # Sistema de puntuación
│       └── parser.py                   # Helpers de parseo
│
├── tests/                              # 🧪 Tests unitarios
│   ├── test_checkers.py
│   ├── test_analyzers.py
│   └── test_integration.py
│
├── examples/                           # 📝 Proyectos de ejemplo
│   ├── sample_bad_project/             # Proyecto con violaciones
│   │   ├── tests/
│   │   ├── pages/
│   │   └── data/
│   ├── sample_good_project/            # Proyecto bien estructurado
│   ├── test_analyzer.py                # Script de prueba
│   └── output/                         # Reportes generados
│
├── docs/                               # 📚 Documentación del TFM
│   ├── memoria_tfm.pdf                 # Memoria del TFM
│   ├── presentacion.pdf                # Slides de presentación
│   ├── arquitectura.md                 # Documentación técnica
│   └── user_guide.md                   # Guía de usuario
│
└── datasets/                           # 📊 Datasets para ML (opcional)
    ├── labeled_code/
    └── annotations.csv
```

---

## ⚙️ Funcionalidades Principales

### 1. 🔍 Detección de Violaciones Arquitectónicas

#### Violaciones detectadas (10+ tipos)

| Severidad | Tipo | Descripción |
|-----------|------|-------------|
| 🔴 CRÍTICA | `ADAPTATION_IN_DEFINITION` | Código de Selenium/Playwright directamente en tests |
| 🔴 CRÍTICA | `MISSING_LAYER_STRUCTURE` | Falta estructura de capas obligatorias |
| 🟡 ALTA | `HARDCODED_TEST_DATA` | Datos de prueba hardcoded en tests |
| 🟡 ALTA | `ASSERTION_IN_POM` | Assertions en Page Objects |
| 🟡 ALTA | `FORBIDDEN_IMPORT` | Imports prohibidos en capa incorrecta |
| 🟠 MEDIA | `BUSINESS_LOGIC_IN_POM` | Lógica de negocio en Page Objects |
| 🟠 MEDIA | `DUPLICATE_LOCATOR` | Locators duplicados sin centralizar |
| 🟠 MEDIA | `LONG_TEST_FUNCTION` | Tests demasiado largos (>50 líneas) |
| 🟢 BAJA | `POOR_TEST_NAMING` | Nombres de test genéricos |

### 2. 📊 Sistema de Puntuación (0-100)

- **Score Global**: Puntuación general del proyecto
- **Scores por Capa**: Evaluación independiente de cada capa gTAA
  - Test Generation Layer
  - Test Definition Layer
  - Test Execution Layer
  - Test Adaptation Layer

### 3. 📈 Reportes Visuales

#### HTML Report
- Dashboard interactivo
- Violaciones agrupadas por severidad
- Snippets de código con highlights
- Recomendaciones de corrección
- Gráficos de distribución

#### JSON Report
- Formato estructurado para CI/CD
- Integración con pipelines
- Parseable por herramientas externas

### 4. 🧠 Análisis Semántico con IA (Diferenciador clave)

**Componente de LLM:**
- Detección de violaciones semánticas que reglas estáticas no pueden capturar
- Análisis contextual del código
- Recomendaciones inteligentes de refactorización

**Ejemplo de detección semántica:**
```python
# Este código "se ve bien" sintácticamente
# pero viola principios de responsabilidad única
# Solo el LLM puede detectarlo

class LoginPage:
    def login_and_verify_success(self, user, pwd):
        # ❌ Mezcla acción (login) con verificación (responsabilidad del test)
        self.do_login(user, pwd)
        assert self.is_logged_in()  # ← LLM detecta esto
```

### 5. 🔄 Integración CI/CD

```yaml
# GitHub Actions example
- name: gTAA Compliance Check
  run: |
    gtaa-validator . --format json --min-score 70
```

---

## 🚀 Despliegue / Publicación (⏳ Futuro)

> **Nota:** La publicación está planeada una vez completadas las Fases 2-4.

### 📦 PyPI (Python Package Index) - Planeado
```bash
# ⏳ PRÓXIMAMENTE
pip install gtaa-ai-validator
```
**Estado:** Pendiente de publicación tras completar funcionalidad básica (Fase 4)

### 🌐 Web Demo (Opcional) - Considerando
- Interfaz web Streamlit para análisis sin instalación
- Upload de proyecto ZIP y recibir reporte HTML
- **Estado:** Evaluando viabilidad post-Fase 4

### 🐳 Docker Image (Opcional) - Considerando
```bash
# ⏳ PRÓXIMAMENTE
docker pull yourusername/gtaa-validator
docker run -v $(pwd):/project gtaa-validator /project
```
**Estado:** Evaluando necesidad según feedback del TFM

---

## 📊 Resultados y Validación (⏳ Pendiente)

> **Nota:** Esta sección describe los resultados esperados una vez completado el TFM.
> La validación empírica se realizará en las Fases 5-6.

### Proyectos a analizar (Fase 5)
- 🎯 15 proyectos Selenium reales de GitHub
- 🎯 5 proyectos Playwright
- 🎯 Target: 500+ archivos de código analizados

### Métricas esperadas de precisión

| Método | Precisión | Recall | F1-Score | Tiempo |
|--------|-----------|--------|----------|---------|
| Estático (objetivo) | >90% | >75% | >80% | <5s |
| LLM (objetivo) | >90% | >90% | >90% | <60s |
| **Híbrido (objetivo)** | **>95%** | **>90%** | **>92%** | <65s |

### Hipótesis a validar
- El análisis estático detectará violaciones estructurales obvias
- El LLM detectará violaciones semánticas sutiles
- El enfoque híbrido superará a ambos métodos individuales

---

## 🎓 Contexto Académico (TFM)

### Objetivos del TFM
1. 🎯 Desarrollar sistema de IA para validación arquitectónica (en progreso - Fase 2/6 completa)
2. 🎯 Comparar análisis estático vs semántico (LLM) (pendiente - Fase 6)
3. 🎯 Demostrar viabilidad de LLMs en code analysis (pendiente - Fase 6)
4. 🎯 Crear dataset etiquetado para la comunidad (implementado parcialmente - ejemplos en Fase 2)

### Contribuciones Científicas Planificadas
- Primera herramienta de validación automática de gTAA
- Comparativa empírica: análisis estático vs LLM vs híbrido
- Dataset público de código Python con violaciones gTAA etiquetadas
- Metodología híbrida reproducible para análisis arquitectónico

### Tecnologías de IA a Utilizar
- **Large Language Models** (Claude Sonnet 4.5 - Fase 6)
- **Prompt Engineering** para análisis de código (Fase 6)
- **Abstract Syntax Tree (AST)** para análisis estático (Fase 2-3)
- **Machine Learning** (Random Forest - opcional, Fase 7)

### Metodología
**Desarrollo Incremental:**
- ✅ Fase 1: Fundación (CLI básico) - **COMPLETA**
- ✅ Fase 2: Motor de análisis estático con AST - **COMPLETA**
- ⏳ Fase 3: Cobertura completa de violaciones (9 tipos)
- ⏳ Fase 4: Reportes HTML/JSON profesionales
- ⏳ Fase 5: Tests unitarios y validación empírica
- ⏳ Fase 6: Integración LLM y comparativa
- ⏳ Fase 7: (Opcional) Clasificador ML

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

```bash
# Fork el proyecto
# Crea una rama
git checkout -b feature/nueva-deteccion

# Commit cambios
git commit -m "Añadir detección de X"

# Push
git push origin feature/nueva-deteccion

# Abre Pull Request
```

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.

---

## 📧 Contacto

**Autor**: Jose Antonio Membrive Guillen
**Email**: membri_2@hotmail.com
**LinkedIn**: [Tu perfil LinkedIn](https://linkedin.com/in/tu-perfil)
**GitHub**: [@tu-usuario](https://github.com/tu-usuario)
**Proyecto**: [gtaa-ai-validator](https://github.com/tu-usuario/gtaa-ai-validator)

---

## 🙏 Agradecimientos

- **ISTQB** por el estándar CT-TAE y gTAA
- **Anthropic** por Claude API
- **Comunidad Open Source** por las herramientas utilizadas
- **Tutores del Máster** por la guía y apoyo

---

## 📚 Referencias

- [ISTQB CT-TAE Syllabus v2016](https://www.istqb.org/)
- [Generic Test Automation Architecture (gTAA)](docs/gtaa_reference.md) (⏳ pendiente)
- [Memoria del TFM](docs/memoria_tfm.pdf) (⏳ pendiente)
- [Presentación](docs/presentacion.pdf) (⏳ pendiente)

---

## 📝 Historial de Desarrollo

### Versión 0.1.0 - Fase 1 (26 Enero 2025) ✅

**Implementado:**
- ✅ Estructura básica del proyecto (setup.py, requirements.txt, etc.)
- ✅ CLI funcional con Click framework
- ✅ Descubrimiento recursivo de archivos de test
- ✅ Soporte para patrones test_*.py y *_test.py
- ✅ Modo verbose para output detallado
- ✅ Validación de entrada (directorio existe)

**Archivos creados:**
- `.gitignore`, `LICENSE`, `README.md`, `requirements.txt`, `setup.py`
- `gtaa_validator/__init__.py`, `gtaa_validator/__main__.py`

**Próximos pasos:** Fase 2 - Implementar análisis estático con AST

---

### Versión 0.2.0 - Fase 2 (26 Enero 2025) ✅

**Implementado:**
- ✅ Modelos de datos (Violation, Report, Severity, ViolationType)
- ✅ Sistema de checkers con Strategy Pattern
- ✅ Análisis AST con Visitor Pattern
- ✅ DefinitionChecker: Detecta llamadas directas a Selenium/Playwright en tests
- ✅ StaticAnalyzer: Orquesta múltiples checkers
- ✅ Sistema de scoring 0-100 con penalización por severidad
- ✅ CLI actualizado con resumen de violaciones
- ✅ Modo verbose con detalles completos de violaciones
- ✅ Exit code 1 si hay violaciones críticas
- ✅ Proyectos de ejemplo documentados (bad_project, good_project)

**Archivos creados:**
- `gtaa_validator/models.py` (280 líneas)
- `gtaa_validator/checkers/base.py` (Strategy Pattern)
- `gtaa_validator/checkers/definition_checker.py` (AST Visitor - 250 líneas)
- `gtaa_validator/analyzers/static_analyzer.py` (Facade Pattern - 200 líneas)
- `examples/bad_project/` (2 archivos con 15 violaciones documentadas)
- `examples/good_project/` (2 archivos con score 100/100)
- `examples/README.md` (Documentación completa de ejemplos)

**Violaciones detectadas:**
- `ADAPTATION_IN_DEFINITION` (CRITICAL): Tests llamando directamente a Selenium/Playwright

**Métricas:**
- Detección: 15/15 violaciones en bad_project (100% recall)
- Score bad_project: 0.0/100
- Score good_project: 100.0/100
- Tiempo de análisis: <0.1s para 2 archivos

**Conceptos aprendidos:**
- AST (Abstract Syntax Tree) parsing
- Visitor Pattern para recorrer árboles
- Strategy Pattern para checkers intercambiables
- Facade Pattern para simplificar subsistemas
- Dataclasses y Enums en Python
- Exit codes en CLI

**Próximos pasos:** Fase 3 - Añadir 8 tipos de violaciones adicionales

---

<div align="center">

**⭐ Si este proyecto te resulta interesante, síguelo para ver su evolución ⭐**

[🐛 Reportar Bug](https://github.com/tu-usuario/gtaa-ai-validator/issues) · [✨ Solicitar Feature](https://github.com/tu-usuario/gtaa-ai-validator/issues) · [📖 Plan de Desarrollo](.claude/plans/)

**Estado del proyecto:** 🚧 En desarrollo activo | Fase 2/6 completa

</div>
