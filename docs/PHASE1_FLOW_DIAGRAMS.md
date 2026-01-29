# Diagramas de Flujo - Fase 1: Fundación del Proyecto y CLI

Este documento describe la Fase 1 del proyecto gTAA AI Validator: la estructura fundacional del proyecto y la interfaz de línea de comandos (CLI).

**Autor**: Jose Antonio Membrive Guillen
**Fecha**: 26 Enero 2026
**Versión**: 0.1.0

---

## Índice

1. [Visión General de la Fase 1](#1-visión-general-de-la-fase-1)
2. [Estructura del Proyecto](#2-estructura-del-proyecto)
3. [Flujo del CLI (`__main__.py`)](#3-flujo-del-cli-__main__py)
4. [Descubrimiento de Archivos](#4-descubrimiento-de-archivos)
5. [Diagrama de Interacción entre Componentes](#5-diagrama-de-interacción-entre-componentes)
6. [Decisiones de Diseño de la Fase 1](#6-decisiones-de-diseño-de-la-fase-1)

---

## 1. Visión General de la Fase 1

La Fase 1 establece los cimientos del proyecto: la estructura de paquetes Python, la interfaz de línea de comandos con Click y el mecanismo de descubrimiento recursivo de archivos.

```
┌─────────────────────────────────────────────────────────┐
│                    Fase 1 — Alcance                      │
│                                                         │
│  ✅ Estructura de paquete Python instalable (setup.py)  │
│  ✅ CLI funcional con Click framework                   │
│  ✅ Validación de entrada (directorio existente)        │
│  ✅ Descubrimiento recursivo de archivos .py            │
│  ✅ Exclusión de directorios no relevantes              │
│  ✅ Modo verbose (--verbose / -v)                       │
│  ✅ Código de salida para integración CI/CD             │
│                                                         │
│  ❌ Sin análisis de código (se añade en Fase 2)         │
│  ❌ Sin detección de violaciones (se añade en Fase 2)   │
│  ❌ Sin sistema de scoring (se añade en Fase 2)         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Estructura del Proyecto

La estructura creada en Fase 1 sigue las convenciones estándar de un paquete Python:

```
gtaa-ai-validator/
│
├── README.md                   # Documentación principal
├── LICENSE                     # Licencia MIT
├── requirements.txt            # Dependencias: click, pytest
├── setup.py                    # Configuración del paquete instalable
├── .gitignore                  # Archivos excluidos de Git
│
├── gtaa_validator/             # Paquete principal
│   ├── __init__.py             # Metadatos del paquete (versión, autor)
│   ├── __main__.py             # Punto de entrada CLI
│   │
│   ├── analyzers/              # Motores de análisis (Fase 2+)
│   │   └── __init__.py
│   │
│   └── checkers/               # Detectores de violaciones (Fase 2+)
│       └── __init__.py
│
└── examples/                   # Proyectos de ejemplo
    ├── bad_project/            # Proyecto con violaciones
    └── good_project/           # Proyecto con arquitectura correcta
```

**Decisiones clave:**

| Decisión | Justificación |
|----------|---------------|
| Paquete instalable (`setup.py`) | Permite ejecutar con `python -m gtaa_validator` desde cualquier ubicación |
| `__main__.py` como entry point | Convención de Python para paquetes ejecutables |
| Separación `analyzers/` y `checkers/` | Anticipación de la arquitectura Facade + Strategy de Fase 2 |
| Click como framework CLI | API declarativa con decoradores, validación automática, `--help` generado |

---

## 3. Flujo del CLI (`__main__.py`)

```
                 ┌──────────────────────────────────────┐
                 │ python -m gtaa_validator <ruta> [-v]  │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ Click parsea argumentos               │
                 │                                      │
                 │  project_path = <ruta>               │
                 │  verbose = True/False                 │
                 │                                      │
                 │  Validación automática:               │
                 │  click.Path(exists=True)              │
                 │  → Si no existe: Click muestra error  │
                 │    y termina (exit 2)                 │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ Mostrar cabecera                      │
                 │                                      │
                 │ "=== gTAA AI Validator ==="           │
                 │ "Analizando proyecto: <ruta>"         │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ Convertir a Path y resolver           │
                 │                                      │
                 │ project_path = Path(ruta).resolve()   │
                 │ → Ruta absoluta canónica              │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ ¿Es directorio?                      │
                 │                                      │
                 │  Sí → Continuar                       │
                 │  No → ERROR + exit(1)                 │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ Crear StaticAnalyzer                  │
                 │ Ejecutar análisis                     │
                 │                                      │
                 │ analyzer = StaticAnalyzer(path, v)    │
                 │ report = analyzer.analyze()           │
                 │                                      │
                 │ (En Fase 1 el analyzer solo            │
                 │  descubría archivos, sin análisis)    │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ Mostrar resultados                    │
                 │                                      │
                 │ • Archivos analizados                 │
                 │ • Violaciones totales                 │
                 │ • Violaciones por severidad           │
                 │ • Puntuación de cumplimiento          │
                 │ • Estado (EXCELENTE/BUENO/etc.)       │
                 │                                      │
                 │ Si verbose:                           │
                 │   → Detalle de cada violación         │
                 └────────────────┬─────────────────────┘
                                  │
                                  ▼
                 ┌──────────────────────────────────────┐
                 │ Código de salida                      │
                 │                                      │
                 │ CRITICAL > 0 → exit(1)               │
                 │ Otro         → exit(0)               │
                 │                                      │
                 │ Permite integración en CI/CD:         │
                 │ pipeline falla si hay violaciones     │
                 │ críticas                              │
                 └──────────────────────────────────────┘
```

---

## 4. Descubrimiento de Archivos

El mecanismo de descubrimiento recursivo de archivos Python es una funcionalidad fundamental establecida en Fase 1:

```
_discover_python_files(project_path)
    │
    ▼
┌──────────────────────────────────────┐
│ project_path.rglob("*.py")          │
│                                      │
│ Busca recursivamente todos los       │
│ archivos con extensión .py           │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Filtrar directorios excluidos        │
│                                      │
│ exclude_dirs = {                     │
│   "venv", "env", ".venv",           │  ← Entornos virtuales
│   ".git", ".hg", ".svn",            │  ← Control de versiones
│   "__pycache__",                     │  ← Caché de Python
│   "node_modules",                    │  ← Dependencias JS
│   ".pytest_cache", ".tox",           │  ← Artefactos de testing
│   "build", "dist", "*.egg-info"     │  ← Artefactos de build
│ }                                    │
│                                      │
│ Para cada archivo .py:               │
│   ¿Algún directorio padre ∈         │
│    exclude_dirs?                     │
│     Sí → Descartar                   │
│     No → Incluir                     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Ordenar resultados                   │
│                                      │
│ python_files.sort()                  │
│                                      │
│ Garantiza un orden determinista      │
│ independiente del sistema operativo  │
└──────────────┬───────────────────────┘
               │
               ▼
         return List[Path]
```

**Ejemplo concreto:**

```
Directorio de entrada:
    mi-proyecto/
    ├── venv/              ← Excluido
    │   └── lib.py
    ├── __pycache__/       ← Excluido
    │   └── module.cpython.pyc
    ├── tests/
    │   ├── test_login.py  ← Incluido
    │   └── test_cart.py   ← Incluido
    ├── pages/
    │   └── login_page.py  ← Incluido
    └── conftest.py        ← Incluido

Resultado: [conftest.py, pages/login_page.py,
            tests/test_cart.py, tests/test_login.py]
            (4 archivos, ordenados alfabéticamente)
```

---

## 5. Diagrama de Interacción entre Componentes

En Fase 1, la interacción es lineal y simple:

```
┌────────────┐     ┌─────────────────┐     ┌──────────┐
│ __main__.py│────►│ StaticAnalyzer   │────►│ Report   │
│            │     │                  │     │          │
│ • Click    │     │ • discover_files │     │ • score  │
│ • args     │     │ • analyze()      │     │ • viols  │
│ • output   │     │                  │     │          │
└────────────┘     └─────────────────┘     └──────────┘
      │                                          │
      │◄─────────────────────────────────────────┘
      │
      ▼
  Consola (stdout)
  + exit code
```

**Comparación con fases posteriores:**

| Componente | Fase 1 | Fase 2 | Fase 3 |
|-----------|--------|--------|--------|
| CLI (`__main__.py`) | ✅ | ✅ | ✅ |
| `StaticAnalyzer` | Descubre archivos | + Parseo AST + 1 checker | + 4 checkers + project checks |
| `BaseChecker` | — | ✅ 1 checker | ✅ 4 checkers |
| `Report` | Estructura básica | + scoring | + 9 tipos de violación |
| Checkers | — | DefinitionChecker | + Structure, Adaptation, Quality |
| AST Visitors | — | BrowserAPICallVisitor | + 3 visitors adicionales |

---

## 6. Decisiones de Diseño de la Fase 1

### Click como framework CLI

```python
@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Activar salida detallada')
def main(project_path, verbose):
    ...
```

| Alternativa | Motivo de descarte |
|-------------|-------------------|
| `argparse` (stdlib) | Más verboso, sin validación automática de rutas |
| `sys.argv` manual | Sin `--help` generado, sin validación, difícil de mantener |
| `typer` | Dependencia adicional para un caso simple |

Click proporciona:
- Validación automática de que la ruta existe (`click.Path(exists=True)`)
- Generación automática de `--help`
- Decoradores declarativos para argumentos y opciones
- Conversión de tipos integrada

### Estructura preparada para extensión

Los directorios `analyzers/` y `checkers/` se crearon vacíos en Fase 1. Esta decisión responde al principio de anticipación arquitectónica: la estructura de paquetes refleja la separación Facade (analyzers) + Strategy (checkers) que se implementa en Fase 2.

---

## Conexión con Fases Posteriores

- **[Fase 2 — Motor de Análisis Estático](PHASE2_FLOW_DIAGRAMS.md)**: Añade `DefinitionChecker`, `BrowserAPICallVisitor`, sistema de scoring y modelos de datos.
- **[Fase 3 — Cobertura Completa](PHASE3_FLOW_DIAGRAMS.md)**: Añade 3 checkers adicionales (Structure, Adaptation, Quality) y 8 tipos de violación nuevos.
- **[Decisiones Arquitectónicas](ARCHITECTURE_DECISIONS.md)**: Justificación de cada patrón de diseño y paradigma utilizado.

---

**Última actualización**: 29 Enero 2026
**Versión del documento**: 1.0
**Proyecto**: gTAA AI Validator
**Repositorio**: https://github.com/Membrive92/gtaa-ai-validator
