# Diagramas de Flujo - Fase 2: Motor de Análisis Estático

Este documento contiene todos los diagramas de flujo que explican el funcionamiento de la Fase 2 del proyecto gTAA AI Validator.

**Autor**: Jose Antonio Membrive Guillen
**Fecha**: 26 Enero 2026
**Versión**: 0.2.0

---

## Índice

1. [Diagrama de Flujo Principal - Vista General](#1-diagrama-de-flujo-principal---vista-general)
2. [Subdiagrama 1: DefinitionChecker.check()](#2-subdiagrama-1-definitioncheckercheck---el-corazón-del-análisis)
3. [Subdiagrama 2: BrowserAPICallVisitor](#3-subdiagrama-2-seleniumcallvisitor---recorrido-del-ast)
4. [Subdiagrama 3: _get_object_name()](#4-subdiagrama-3-_get_object_name---extraer-nombre-del-objeto)
5. [Subdiagrama 4: Creación de Violation](#5-subdiagrama-4-creación-de-violation)
6. [Subdiagrama 5: Cálculo de Score](#6-subdiagrama-5-cálculo-de-score)
7. [Diagrama de Datos](#7-diagrama-de-datos---transformación-de-estructuras)
8. [Diagrama de Interacción entre Clases](#8-diagrama-de-interacción-entre-clases)
9. [Ejemplo Concreto Paso a Paso](#9-ejemplo-concreto-paso-a-paso)

---

## 1. Diagrama de Flujo Principal - Vista General

Este diagrama muestra el flujo completo desde que el usuario ejecuta el comando hasta que obtiene los resultados.

```
┌─────────────────────────────────────────────────────────────────┐
│                        INICIO                                   │
│              python -m gtaa_validator examples/bad_project      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   __main__.py                                   │
│                                                                 │
│  1. Click parsea argumentos                                     │
│     ├─ project_path = "examples/bad_project"                   │
│     └─ verbose = False                                          │
│                                                                 │
│  2. Convertir a Path object                                     │
│     └─ Path("C:/Users/.../examples/bad_project")               │
│                                                                 │
│  3. Validar directorio                                          │
│     └─ ¿Existe? ──No──> ERROR: exit(1)                         │
│            │                                                    │
│           Sí                                                    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Crear StaticAnalyzer                               │
│                                                                 │
│  analyzer = StaticAnalyzer(project_path, verbose)               │
│                                                                 │
│  Constructor hace:                                              │
│  ├─ self.project_path = project_path                           │
│  ├─ self.verbose = verbose                                      │
│  └─ self.checkers = _initialize_checkers()                     │
│                     │                                           │
│                     └──> [DefinitionChecker()]                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              analyzer.analyze()                                 │
│                                                                 │
│  ┌───────────────────────────────────────────────┐             │
│  │ report = Report(                               │             │
│  │   project_path = path,                         │             │
│  │   violations = [],                             │             │
│  │   files_analyzed = 0                           │             │
│  │ )                                              │             │
│  └───────────────────────────────────────────────┘             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│         _discover_python_files()                                │
│                                                                 │
│  Buscar recursivamente *.py                                     │
│  Excluir: venv/, .git/, __pycache__/                           │
│                                                                 │
│  Resultado:                                                     │
│  ┌──────────────────────────────┐                              │
│  │ [                            │                              │
│  │   Path("__init__.py"),       │                              │
│  │   Path("test_login.py"),     │                              │
│  │   Path("test_search.py")     │                              │
│  │ ]                            │                              │
│  └──────────────────────────────┘                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│         Para cada archivo Python                                │
│         (Loop sobre python_files)                               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────┐
             │              │
             ▼              ▼
     ┌──────────────┐  ┌──────────────┐
     │ __init__.py  │  │test_login.py │  ...
     └──────┬───────┘  └──────┬───────┘
            │                 │
            ▼                 ▼
   ┌─────────────────────────────────────────┐
   │    _check_file(file_path)               │
   │                                         │
   │    1. Filtrar checkers aplicables        │
   │    2. Parsear AST una sola vez:         │
   │       tree = ast.parse(source_code)     │
   │                                         │
   │    Para cada checker aplicable:         │
   │       checker.check(file, tree)         │
   │       └─► checker reutiliza el tree     │
   │                                         │
   │                  [violations]           │
   └─────────────────────────┬───────────────┘
                             │
                             ▼
                  report.violations.extend(violations)
                  report.files_analyzed += 1
                             │
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        │   Después de todos los archivos         │
        │                                         │
        ▼                                         ▼
┌──────────────────┐                   ┌──────────────────┐
│ report ahora:    │                   │  calculate_score()│
│                  │                   │                  │
│ violations: [    │                   │  total_penalty = │
│   Violation1,    │                   │  Σ(v.severity.   │
│   Violation2,    │                   │    penalty)      │
│   ...            │                   │                  │
│   Violation15    │                   │  = 15 × 10       │
│ ]                │                   │  = 150           │
│                  │                   │                  │
│ files_analyzed:3 │                   │  score =         │
└──────────────────┘                   │  max(0, 100-150) │
                                       │  = 0.0           │
                                       └────────┬─────────┘
                                                │
                                                ▼
                                       report.score = 0.0
                                                │
                                                ▼
                                     return report completo
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Volver a __main__.py                               │
│                                                                 │
│  report recibido, ahora mostrar resultados:                     │
│                                                                 │
│  ┌───────────────────────────────────────────┐                 │
│  │ Files analyzed: 3                         │                 │
│  │ Total violations: 15                      │                 │
│  │                                           │                 │
│  │ Violations by severity:                   │                 │
│  │   CRITICAL: 15                            │                 │
│  │   HIGH:     0                             │                 │
│  │   MEDIUM:   0                             │                 │
│  │   LOW:      0                             │                 │
│  │                                           │                 │
│  │ Compliance Score: 0.0/100                 │                 │
│  │ Status: CRITICAL ISSUES                   │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
│  if verbose:                                                    │
│    └─> Mostrar detalles de cada violación                      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Exit Code                                          │
│                                                                 │
│  if severity_counts['CRITICAL'] > 0:                            │
│      return 1  ◄─── bad_project (15 CRITICAL)                  │
│  else:                                                          │
│      return 0  ◄─── good_project (0 violations)                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                          FIN
```

**Archivos involucrados**:
- `gtaa_validator/__main__.py` - Entry point y CLI
- `gtaa_validator/analyzers/static_analyzer.py` - Orquestador del análisis
- `gtaa_validator/checkers/definition_checker.py` - Detector de violaciones
- `gtaa_validator/models.py` - Estructuras de datos

---

## 2. Subdiagrama 1: DefinitionChecker.check() - El Corazón del Análisis

Este diagrama detalla cómo funciona el método `check()` del `DefinitionChecker`, que es responsable de detectar violaciones usando AST.

```
┌─────────────────────────────────────────────────────────────────┐
│         DefinitionChecker.check(file_path, tree=None)            │
│                                                                 │
│  Entrada: Path("examples/bad_project/test_login.py")           │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Inicializar                                                 │
│     self.violations = []                                        │
│     self.current_file = file_path                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Obtener AST                                                  │
│                                                                 │
│     Si tree fue proporcionado (pre-parseado por StaticAnalyzer):│
│       → Usar directamente, sin leer ni parsear                  │
│                                                                 │
│     Si tree es None (llamada standalone):                       │
│       → Leer archivo y parsear:                                 │
│         source_code = open(file_path).read()                    │
│         tree = ast.parse(source_code)                           │
│                                                                 │
│  Convierte código Python en árbol:                              │
│                                                                 │
│  Module                                                         │
│    ├─ Import(selenium)                                          │
│    ├─ FunctionDef(test_login_with_valid_credentials)           │
│    │    ├─ Assign(driver = ...)                                │
│    │    ├─ Expr                                                 │
│    │    │   └─ Call                                             │
│    │    │       └─ Attribute(driver.find_element)  ◄─ CLAVE    │
│    │    └─ ...                                                  │
│    └─ FunctionDef(test_login_with_invalid_credentials)         │
│         └─ ...                                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Crear Visitor y recorrer AST                                │
│                                                                 │
│     visitor = BrowserAPICallVisitor(self)                        │
│     visitor.visit(tree)  ◄─ Comienza recorrido recursivo       │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
        [Ver siguiente diagrama: BrowserAPICallVisitor]
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Después del recorrido                                       │
│                                                                 │
│     self.violations = [                                         │
│         Violation(line=24, method="find_element"...),           │
│         Violation(line=25, method="find_element"...),           │
│         ...                                                     │
│         Violation(line=51, method="find_element"...)            │
│     ]                                                           │
│                                                                 │
│     Total: 8 violaciones encontradas                            │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Retornar violaciones                                        │
│                                                                 │
│     return self.violations                                      │
└─────────────────────────────────────────────────────────────────┘
```

**Concepto clave**: AST (Abstract Syntax Tree) - Representación en árbol del código Python que permite analizar su estructura sin ejecutarlo.

**Archivo**: `gtaa_validator/checkers/definition_checker.py:101-135`

---

## 3. Subdiagrama 2: BrowserAPICallVisitor - Recorrido del AST

Este diagrama muestra cómo el Visitor Pattern recorre el árbol AST y detecta violaciones.

```
┌─────────────────────────────────────────────────────────────────┐
│         visitor.visit(tree)                                     │
│                                                                 │
│  Estado inicial:                                                │
│    inside_test_function = False                                 │
│    current_function_name = None                                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
   Python llama automáticamente a métodos visit_*
   según el tipo de nodo del AST
             │
             ├──────────────────────┬──────────────────┬──────────
             │                      │                  │
             ▼                      ▼                  ▼
    ┌─────────────┐      ┌──────────────┐    ┌──────────────┐
    │visit_Import │      │visit_        │    │visit_        │
    │             │      │FunctionDef   │    │FunctionDef   │
    │(selenium)   │      │              │    │              │
    │             │      │test_login... │    │test_login... │
    │No hace nada │      │              │    │invalid...    │
    │Continúa     │      └──────┬───────┘    └──────┬───────┘
    └─────────────┘             │                   │
                                │                   │
                                ▼                   ▼
           ┌─────────────────────────────────────────────────────┐
           │ visit_FunctionDef(node)                             │
           │                                                     │
           │ ¿node.name.startswith("test_")? ──No──> Skip       │
           │          │                                          │
           │         Sí                                          │
           │          │                                          │
           │          ▼                                          │
           │  ┌─────────────────────────────────┐               │
           │  │ inside_test_function = True     │               │
           │  │ current_function_name = node.name│               │
           │  └─────────────────────────────────┘               │
           │          │                                          │
           │          ▼                                          │
           │  self.generic_visit(node)  ◄─ Visita cuerpo        │
           │          │                      de la función       │
           │          │                                          │
           │          └──> visit_Call(line 20)                   │
           │          └──> visit_Call(line 24)  ◄─ CLAVE        │
           │          └──> visit_Call(line 25)                   │
           │          └──> ...                                   │
           │          │                                          │
           │          ▼                                          │
           │  inside_test_function = False  ◄─ Al salir          │
           └─────────────────────────────────────────────────────┘
                         │
                         ▼
           ┌─────────────────────────────────────────────────────┐
           │ visit_Call(node) - Línea 24                         │
           │                                                     │
           │ node = driver.find_element(By.ID, "username")       │
           │                                                     │
           │ ¿inside_test_function? ──No──> Ignorar             │
           │          │                                          │
           │         Sí                                          │
           │          │                                          │
           │          ▼                                          │
           │  ¿isinstance(node.func, ast.Attribute)?            │
           │  (¿Es llamada a método obj.method()?)              │
           │          │                                          │
           │         Sí                                          │
           │          │                                          │
           │          ▼                                          │
           │  ┌──────────────────────────────────┐              │
           │  │ method_name = node.func.attr     │              │
           │  │             = "find_element"     │              │
           │  │                                  │              │
           │  │ object_name = _get_object_name() │              │
           │  │             = "driver"           │              │
           │  └──────────────────────────────────┘              │
           │          │                                          │
           │          ▼                                          │
           │  ┌─────────────────────────────────────────┐       │
           │  │ ¿"find_element" in SELENIUM_METHODS?    │       │
           │  │                 Sí ✓                    │       │
           │  │                                         │       │
           │  │ ¿"driver" in BROWSER_OBJECTS?          │       │
           │  │                 Sí ✓                    │       │
           │  └─────────────────┬───────────────────────┘       │
           │                    │                                │
           │                    ▼                                │
           │         ¡VIOLACIÓN ENCONTRADA!                      │
           │                    │                                │
           │                    ▼                                │
           │  ┌─────────────────────────────────────────┐       │
           │  │ self.checker.add_violation(             │       │
           │  │     line_number = 24,                   │       │
           │  │     method_name = "find_element",       │       │
           │  │     object_name = "driver",             │       │
           │  │     code_snippet = "driver.find_..."    │       │
           │  │ )                                       │       │
           │  └─────────────────────────────────────────┘       │
           │                    │                                │
           │                    ▼                                │
           │         Violation añadida a la lista                │
           └─────────────────────────────────────────────────────┘
                         │
                         ▼
              Continuar con siguiente Call
              (línea 25, 26, 34, 46, ...)
```

**Concepto clave**: Visitor Pattern - Patrón de diseño que permite separar el algoritmo de recorrido de la estructura de datos (AST).

**Conjuntos de detección**:
```python
SELENIUM_METHODS = {
    "find_element", "find_elements",
    "find_element_by_id", "find_element_by_xpath", ...
}

PLAYWRIGHT_METHODS = {
    "locator", "query_selector", "click", "fill", ...
}

BROWSER_OBJECTS = {
    "driver", "page", "browser", "context"
}
```

**Archivo**: `gtaa_validator/checkers/definition_checker.py:164-262`

---

## 4. Subdiagrama 3: _get_object_name() - Extraer nombre del objeto

Este diagrama muestra cómo se extrae el nombre del objeto de una llamada a método.

```
┌─────────────────────────────────────────────────────────────────┐
│  _get_object_name(node.func.value)                              │
│                                                                 │
│  Objetivo: De "driver.find_element" extraer "driver"            │
│            De "self.driver.find_element" extraer "driver"       │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Casos posibles:                                                │
│                                                                 │
│  CASO 1: driver.find_element()                                  │
│  ┌────────────────────────────────────┐                        │
│  │ node.func.value = Name(id="driver")│                        │
│  │                                    │                        │
│  │ isinstance(node, ast.Name) ──> Sí  │                        │
│  │                                    │                        │
│  │ return node.id = "driver"          │                        │
│  └────────────────────────────────────┘                        │
│                                                                 │
│  CASO 2: self.driver.find_element()                             │
│  ┌────────────────────────────────────────┐                    │
│  │ node.func.value = Attribute(           │                    │
│  │     value = Name(id="self"),           │                    │
│  │     attr = "driver"                    │                    │
│  │ )                                      │                    │
│  │                                        │                    │
│  │ isinstance(node, ast.Attribute) ──> Sí │                    │
│  │                                        │                    │
│  │ return _get_object_name(node.value)    │                    │
│  │        = "driver"  (recursivo)         │                    │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  CASO 3: Otra cosa                                              │
│  └──> return ""                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Ejemplos de uso**:
```python
# Código                         # Resultado
driver.find_element()        →   "driver"
self.driver.find_element()   →   "driver"
page.locator()               →   "page"
self.page.click()            →   "page"
```

**Archivo**: `gtaa_validator/checkers/definition_checker.py:264-288`

---

## 5. Subdiagrama 4: Creación de Violation

Este diagrama muestra cómo se crea un objeto Violation cuando se detecta una violación.

```
┌─────────────────────────────────────────────────────────────────┐
│  checker.add_violation(line=24, method="find_element", ...)     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Crear objeto Violation                                         │
│                                                                 │
│  violation = Violation(                                         │
│      violation_type = ViolationType.ADAPTATION_IN_DEFINITION,   │
│      severity = Severity.CRITICAL,  ◄─ Auto-asignado           │
│      file_path = Path("test_login.py"),                        │
│      line_number = 24,                                          │
│      message = "Test code directly calls...",                   │
│      code_snippet = "driver.find_element(By.ID, 'username')",  │
│      recommendation = "Create Page Objects..."                  │
│  )                                                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  __post_init__() se ejecuta automáticamente (dataclass)         │
│                                                                 │
│  if not self.severity:                                          │
│      self.severity = violation_type.get_severity()              │
│                    = Severity.CRITICAL                          │
│                                                                 │
│  if not self.recommendation:                                    │
│      self.recommendation = violation_type.get_recommendation()  │
│                                                                 │
│  if not self.message:                                           │
│      self.message = violation_type.get_description()            │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Violation completo creado                                      │
│                                                                 │
│  self.violations.append(violation)                              │
└─────────────────────────────────────────────────────────────────┘
```

**Estructura del objeto Violation**:
```python
@dataclass
class Violation:
    violation_type: ViolationType     # ADAPTATION_IN_DEFINITION
    severity: Severity                # CRITICAL
    file_path: Path                   # Path("test_login.py")
    line_number: Optional[int]        # 24
    message: str                      # Descripción detallada
    code_snippet: Optional[str]       # "driver.find_element(...)"
    recommendation: str               # Cómo corregirlo
```

**Archivos involucrados**:
- `gtaa_validator/checkers/definition_checker.py:137-162` - add_violation()
- `gtaa_validator/models.py:140-189` - Clase Violation

---

## 6. Subdiagrama 5: Cálculo de Score

Este diagrama muestra cómo se calcula el score de compliance (0-100) basado en las violaciones encontradas.

```
┌─────────────────────────────────────────────────────────────────┐
│  report.calculate_score()                                       │
│                                                                 │
│  violations = [Violation1, Violation2, ..., Violation15]        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Para cada violación, sumar penalización                        │
│                                                                 │
│  total_penalty = sum(                                           │
│      v.severity.get_score_penalty()                             │
│      for v in self.violations                                   │
│  )                                                              │
│                                                                 │
│  Desglose:                                                      │
│  ┌───────────────────────────────────────────┐                 │
│  │ Violation 1: CRITICAL → 10 puntos         │                 │
│  │ Violation 2: CRITICAL → 10 puntos         │                 │
│  │ Violation 3: CRITICAL → 10 puntos         │                 │
│  │ ...                                       │                 │
│  │ Violation 15: CRITICAL → 10 puntos        │                 │
│  │                                           │                 │
│  │ Total = 15 × 10 = 150 puntos              │                 │
│  └───────────────────────────────────────────┘                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Calcular score                                                 │
│                                                                 │
│  score = max(0.0, 100.0 - total_penalty)                       │
│        = max(0.0, 100.0 - 150)                                 │
│        = max(0.0, -50)                                         │
│        = 0.0                                                    │
│                                                                 │
│  self.score = 0.0                                              │
│  return 0.0                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Tabla de penalizaciones**:
```python
Severity.CRITICAL  →  10 puntos
Severity.HIGH      →   5 puntos
Severity.MEDIUM    →   2 puntos
Severity.LOW       →   1 punto
```

**Interpretación del score**:
```
90-100 → EXCELLENT           (Verde)
75-89  → GOOD                (Verde claro)
50-74  → NEEDS IMPROVEMENT   (Amarillo)
0-49   → CRITICAL ISSUES     (Rojo)
```

**Archivo**: `gtaa_validator/models.py:208-220`

---

## 7. Diagrama de Datos - Transformación de Estructuras

Este diagrama muestra cómo se transforman los datos a lo largo del proceso.

```
ENTRADA: Comando CLI
│
├─ "examples/bad_project"
│
▼
Path object
│
├─ Path("C:/Users/.../examples/bad_project")
│
▼
Lista de archivos Python
│
├─ [Path("test_login.py"), Path("test_search.py"), ...]
│
▼
Para cada archivo → Código fuente (string)
│
├─ "from selenium import webdriver\ndef test_login():\n    driver.find..."
│
▼
AST (árbol)
│
├─ Module(body=[Import(...), FunctionDef(...), ...])
│
▼
Visitor recorre y detecta → Lista de Violations
│
├─ [Violation(line=24, ...), Violation(line=25, ...), ...]
│
▼
Report object
│
├─ Report(
│      project_path = Path(...),
│      violations = [15 violations],
│      files_analyzed = 3,
│      score = 0.0
│    )
│
▼
Diccionario de conteo
│
├─ {'CRITICAL': 15, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
│
▼
SALIDA: Texto en consola + Exit code
│
├─ "Files analyzed: 3
│    Total violations: 15
│    ...
│    Score: 0.0/100"
│
└─ exit(1)  (porque hay violaciones CRITICAL)
```

**Tipos de datos en cada etapa**:
1. String (CLI argument)
2. pathlib.Path (ruta absoluta)
3. List[Path] (archivos descubiertos)
4. String (código fuente)
5. ast.Module (AST tree)
6. List[Violation] (violaciones detectadas)
7. Report (reporte completo)
8. Dict[str, int] (conteo por severidad)
9. String (output formateado) + int (exit code)

---

## 8. Diagrama de Interacción entre Clases

Este diagrama muestra cómo interactúan las diferentes clases del sistema.

```
┌─────────────┐
│  __main__   │
│             │
│  main()     │
└──────┬──────┘
       │
       │ crea
       ▼
┌─────────────────────┐
│  StaticAnalyzer     │
│                     │
│  + analyze()        │
│  + _discover_python_files()│
│  + _check_file()    │
└──────┬──────────────┘
       │
       │ tiene
       ▼
┌─────────────────────┐
│  List[BaseChecker]  │
│                     │
│  [DefinitionChecker]│
└──────┬──────────────┘
       │
       │ implementa
       ▼
┌─────────────────────┐        usa        ┌────────────────────────┐
│ DefinitionChecker   │◄─────────────────│ BrowserAPICallVisitor  │
│                     │                   │                        │
│  + can_check()      │                   │  + visit_FunctionDef() │
│  + check(file,tree) │                   │  + visit_Call()        │
│  + add_violation()  │                   │  + _get_object_name()  │
└──────┬──────────────┘                   └────────────────────────┘
       │
       │ crea
       ▼
┌─────────────────────┐
│    Violation        │
│                     │
│  - violation_type   │
│  - severity         │
│  - file_path        │
│  - line_number      │
│  - message          │
│  - code_snippet     │
│  - recommendation   │
└─────────────────────┘
       │
       │ agregada a
       ▼
┌─────────────────────┐
│     Report          │
│                     │
│  - project_path     │
│  - violations: []   │
│  - files_analyzed   │
│  - score: float     │
│                     │
│  + calculate_score()│
│  + get_violations_  │
│    by_severity()    │
└─────────────────────┘
       │
       │ retornado a
       ▼
┌─────────────────────┐
│    __main__         │
│                     │
│  Muestra resultados │
│  Retorna exit code  │
└─────────────────────┘
```

**Relaciones**:
- __main__ → StaticAnalyzer: **crea y usa**
- StaticAnalyzer → BaseChecker: **composición (tiene)**
- DefinitionChecker → BrowserAPICallVisitor: **usa**
- DefinitionChecker → Violation: **crea**
- StaticAnalyzer → Report: **crea y gestiona**
- Report → Violation: **composición (lista)**

**Patrones de diseño**:
- **Strategy Pattern**: BaseChecker define interfaz, DefinitionChecker implementa
- **Visitor Pattern**: BrowserAPICallVisitor recorre AST
- **Facade Pattern**: StaticAnalyzer simplifica acceso al subsistema
- **Builder/Factory**: Violations se crean con valores por defecto inteligentes

---

## 9. Ejemplo Concreto Paso a Paso

Este diagrama muestra un ejemplo real completo, desde una línea de código hasta su detección como violación.

```
┌─ EJEMPLO REAL ─────────────────────────────────────────────────┐
│                                                                 │
│  Archivo: test_login.py, Línea 24                              │
│  Código: driver.find_element(By.ID, "username").send_keys(...) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

PASO 1: Leer archivo
  └─> "...driver.find_element(By.ID, 'username')..."

PASO 2: Parsear a AST
  └─> Call(
        func=Attribute(
          value=Call(
            func=Attribute(
              value=Name(id='driver'),
              attr='find_element'
            ),
            args=[Attribute(By, 'ID'), Constant('username')]
          ),
          attr='send_keys'
        )
      )

PASO 3: Visitor detecta
  └─> visit_Call() llamado con este nodo
        │
        ├─ inside_test_function? → True ✓
        ├─ Es Attribute? → True ✓
        ├─ method_name → "find_element"
        ├─ object_name → "driver"
        ├─ En SELENIUM_METHODS? → True ✓
        ├─ En BROWSER_OBJECTS? → True ✓
        └─> ¡VIOLACIÓN!

PASO 4: Crear Violation
  └─> Violation(
        type=ADAPTATION_IN_DEFINITION,
        severity=CRITICAL,
        file=test_login.py,
        line=24,
        message="Test code directly calls driver.find_element()...",
        code="driver.find_element(By.ID, 'username')",
        recommendation="Create Page Objects that encapsulate..."
      )

PASO 5: Añadir a lista
  └─> self.violations.append(violation)

PASO 6: Repetir para líneas 25, 26, 34, 46, 47, 48, 51
  └─> Total: 8 violaciones en test_login.py

PASO 7: Calcular score
  └─> 8 × 10 = 80 puntos de penalización (solo para este archivo)

PASO 8: Mostrar en consola
  └─> "[1] CRITICAL - ADAPTATION_IN_DEFINITION
        Location: test_login.py:24
        Message: Test code directly calls driver.find_element()...
        Code: driver.find_element(By.ID, 'username')
        Recommendation: Create Page Objects that encapsulate..."
```

**Comparación: Código MAL vs BIEN**

```python
# ❌ MAL - test_login.py línea 24 (VIOLACIÓN)
driver.find_element(By.ID, "username").send_keys("user")

# ✅ BIEN - good_project/tests/test_login.py
login_page.enter_username("user")  # Usa Page Object
```

**¿Por qué es violación?**
- El test (capa Definition) llama directamente a Selenium (capa Adaptation)
- Según gTAA, el test debe llamar a Page Objects, no a driver
- Viola el principio de separación de responsabilidades

**Cómo corregirlo**:
1. Crear LoginPage (Page Object)
2. Mover `driver.find_element(By.ID, "username")` a LoginPage
3. Crear método `login_page.enter_username(username)`
4. El test llama al método del Page Object

---

## Resumen de Conceptos Clave

### AST (Abstract Syntax Tree)
Representación en árbol de la estructura sintáctica del código Python. Permite analizar código sin ejecutarlo.

```python
ast.parse(source_code)  # String → AST tree
```

### Visitor Pattern
Patrón de diseño que permite recorrer una estructura de datos compleja (como un AST) y ejecutar operaciones específicas en cada nodo.

```python
visitor.visit(tree)  # Automáticamente llama visit_FunctionDef, visit_Call, etc.
```

### Strategy Pattern
Patrón que define una familia de algoritmos (checkers) con una interfaz común (BaseChecker), haciendo que sean intercambiables.

```python
checkers = [DefinitionChecker(), StructureChecker(), ...]
tree = ast.parse(source_code)
for checker in checkers:
    violations = checker.check(file, tree)  # Misma interfaz, AST compartido
```

### Facade Pattern
Patrón que proporciona una interfaz simplificada a un subsistema complejo.

```python
analyzer = StaticAnalyzer(project_path)
report = analyzer.analyze()  # Simple interfaz que orquesta todo
```

### Dataclasses
Clases Python que automatizan la creación de constructores, métodos especiales, y permiten valores por defecto inteligentes.

```python
@dataclass
class Violation:
    violation_type: ViolationType
    severity: Severity

    def __post_init__(self):  # Se ejecuta automáticamente después de __init__
        if not self.severity:
            self.severity = self.violation_type.get_severity()
```

---

## Métricas de la Fase 2

**Código implementado**:
- 7 archivos Python nuevos
- ~1,672 líneas de código
- 1 tipo de violación detectado
- 2 frameworks soportados (Selenium, Playwright)

**Capacidades**:
- Análisis AST de código Python
- Detección de violación ADAPTATION_IN_DEFINITION
- Sistema de scoring 0-100
- Reportes por consola (normal y verbose)
- Exit codes para CI/CD
- Proyectos de ejemplo documentados

**Rendimiento**:
- Análisis de 2-5 archivos: <0.1s
- Precisión en ejemplos: 100% (15/15 violaciones detectadas)
- Recall: 100% (todas las violaciones conocidas detectadas)

---

## Conexión con Otras Fases

**✅ Fase 1** (completada): Fundación del proyecto y CLI. Ver [PHASE1_FLOW_DIAGRAMS.md](PHASE1_FLOW_DIAGRAMS.md).

**✅ Fase 3** (completada): Cobertura completa con 9 tipos de violaciones y 4 checkers. Ver [PHASE3_FLOW_DIAGRAMS.md](PHASE3_FLOW_DIAGRAMS.md).

**⏳ Fase 4**: Reportes HTML/JSON profesionales

**⏳ Fase 5**: Integración LLM (opcional)

**⏳ Fase 6**: Validación empírica y documentación TFM

---

**Última actualización**: 29 Enero 2026
**Versión del documento**: 1.1
**Proyecto**: gTAA AI Validator
**Repositorio**: https://github.com/Membrive92/gtaa-ai-validator
