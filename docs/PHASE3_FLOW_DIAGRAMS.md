# Fase 3 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Arquitectura](#1-visión-general-de-la-arquitectura)
2. [Flujo Principal: StaticAnalyzer.analyze()](#2-flujo-principal-staticanalyzeranalyze)
3. [Check a Dos Niveles: Proyecto vs Archivo](#3-check-a-dos-niveles-proyecto-vs-archivo)
4. [StructureChecker — Validación de Estructura](#4-structurechecker--validación-de-estructura)
5. [AdaptationChecker — Validación de Page Objects](#5-adaptationchecker--validación-de-page-objects)
6. [QualityChecker — Calidad de Tests](#6-qualitychecker--calidad-de-tests)
7. [Mapa de Visitors AST](#7-mapa-de-visitors-ast)
8. [Flujo de Detección de Locators Duplicados](#8-flujo-de-detección-de-locators-duplicados)
9. [Mapa Completo de Violaciones](#9-mapa-completo-de-violaciones)
10. [Interacción entre Componentes](#10-interacción-entre-componentes)

---

## 1. Visión General de la Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    StaticAnalyzer                        │
│                   (Facade Pattern)                       │
│                                                         │
│  analyze() ─────────────────────────────────────────►Report
│     │                                                   │
│     ├── check_project() ──► por cada checker            │
│     ├── _discover_python_files()                        │
│     └── _check_file() ───► por cada archivo             │
│              │                                          │
│              ▼                                          │
│  ┌─────────────────────────────────────────────┐       │
│  │            4 Checkers (Strategy)             │       │
│  │                                              │       │
│  │  ┌──────────────────┐ ┌──────────────────┐  │       │
│  │  │DefinitionChecker │ │StructureChecker  │  │       │
│  │  │  (Fase 2)        │ │  (Fase 3)        │  │       │
│  │  │  ADAPTATION_IN_  │ │  MISSING_LAYER_  │  │       │
│  │  │  DEFINITION      │ │  STRUCTURE       │  │       │
│  │  └──────────────────┘ └──────────────────┘  │       │
│  │  ┌──────────────────┐ ┌──────────────────┐  │       │
│  │  │AdaptationChecker │ │ QualityChecker   │  │       │
│  │  │  (Fase 3)        │ │  (Fase 3)        │  │       │
│  │  │  ASSERTION_IN_POM│ │  HARDCODED_DATA  │  │       │
│  │  │  FORBIDDEN_IMPORT│ │  LONG_TEST_FUNC  │  │       │
│  │  │  BUSINESS_LOGIC  │ │  POOR_NAMING     │  │       │
│  │  │  DUPLICATE_LOC   │ │                  │  │       │
│  │  └──────────────────┘ └──────────────────┘  │       │
│  └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Flujo Principal: StaticAnalyzer.analyze()

Este es el flujo completo que ejecuta el analizador cuando se llama a `analyze()`.
La novedad de Fase 3 es el paso "Project-Level Checks" antes del bucle de archivos.

```
analyze()
    │
    ▼
┌──────────────────────┐
│ Crear Report vacío   │
│ violations=[]        │
│ files_analyzed=0     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ ★ NUEVO FASE 3: Project-Level Checks        │
│                                              │
│ for checker in self.checkers:                │
│     violations = checker.check_project(path) │
│     report.violations += violations          │
│                                              │
│ Solo StructureChecker hace algo aquí         │
│ (los demás retornan [])                      │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│ _discover_python_files()                     │
│                                              │
│ project_path.rglob("*.py")                   │
│ Excluir: venv, .git, __pycache__,            │
│          node_modules, .pytest_cache, etc.   │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
           ┌───────────────┐
           │ Para cada .py  │◄─────────────────────┐
           └───────┬───────┘                       │
                   │                               │
                   ▼                               │
    ┌──────────────────────────────────┐           │
    │ _check_file(file_path)           │           │
    │                                  │           │
    │ 1. Filtrar checkers aplicables    │           │
    │ 2. tree = ast.parse(file) ←UNA  │           │
    │    VEZ para todos los checkers   │           │
    │ 3. for checker in applicable:    │           │
    │      checker.check(file, tree)   │           │
    └──────────────┬───────────────────┘           │
                   │                               │
                   ▼                               │
    ┌──────────────────────────────────┐           │
    │ report.violations += violations  │           │
    │ report.files_analyzed += 1       │───────────┘
    └──────────────────────────────────┘
                   │
                   ▼  (cuando terminan todos los archivos)
    ┌──────────────────────────────────┐
    │ report.calculate_score()         │
    │ report.execution_time_seconds =  │
    │     time() - start_time          │
    └──────────────┬───────────────────┘
                   │
                   ▼
              ┌─────────┐
              │ Return   │
              │ Report   │
              └─────────┘
```

---

## 3. Check a Dos Niveles: Proyecto vs Archivo

Fase 3 introduce `check_project()` en `BaseChecker`, separando la lógica en dos niveles:

```
                    BaseChecker
                    ┌─────────────────────────────────────┐
                    │ check_project(path) → List[Violation]│ ← Nivel PROYECTO
                    │   default: return []                 │
                    │                                      │
                    │ can_check(file) → bool                │ ← Filtro
                    │   default: .py files                  │
                    │                                      │
                    │ check(file, tree?) → List[Violation]  │ ← Nivel ARCHIVO
                    │   abstractmethod (tree pre-parseado)  │
                    └─────────────────────────────────────┘
                           ▲           ▲            ▲           ▲
                           │           │            │           │
              ┌────────────┤    ┌──────┤     ┌──────┤    ┌──────┤
              │             │    │      │     │      │    │      │
    ┌─────────┴──┐ ┌───────┴──┐ ┌──────┴──┐ ┌──────┴──┐
    │ Definition │ │ Structure│ │Adaptation│ │ Quality │
    │  Checker   │ │  Checker │ │ Checker  │ │ Checker │
    ├────────────┤ ├──────────┤ ├──────────┤ ├─────────┤
    │check_proj: │ │check_proj│ │check_proj│ │check_pr:│
    │  []        │ │  ★ valida│ │  []      │ │  []     │
    │            │ │  dirs    │ │          │ │         │
    │can_check:  │ │can_check:│ │can_check:│ │can_chk: │
    │  test files│ │  False   │ │ page obj │ │test file│
    │            │ │  siempre │ │  files   │ │         │
    │check:      │ │check:    │ │check:    │ │check:   │
    │  Selenium/ │ │  []      │ │  imports │ │ hardcode│
    │  Playwright│ │          │ │  asserts │ │ long fn │
    │  en tests  │ │          │ │  logic   │ │ naming  │
    │            │ │          │ │  locators│ │         │
    └────────────┘ └──────────┘ └──────────┘ └─────────┘
```

**¿Quién hace qué?**

| Checker            | check_project() | can_check()      | check()           |
|--------------------|-----------------|------------------|--------------------|
| DefinitionChecker  | `[]` (nada)     | test files       | Selenium/Playwright|
| StructureChecker   | ★ valida dirs   | `False` siempre  | `[]` (nada)        |
| AdaptationChecker  | `[]` (nada)     | page object files| imports/asserts/etc|
| QualityChecker     | `[]` (nada)     | test files       | hardcode/long/name |

---

## 4. StructureChecker — Validación de Estructura

El checker más simple: solo mira si existen directorios requeridos.

```
check_project(project_path)
    │
    ▼
┌────────────────────────────────┐
│ Listar subdirectorios          │
│ subdirs = {d.name.lower()      │
│   for d in path.iterdir()      │
│   if d.is_dir()}               │
│                                │
│ Ej: {"pages", "__init__",      │
│      "test_login.py"...}       │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ has_test_dir =                 │
│   subdirs ∩ {"tests","test"}   │
│   ≠ ∅ ?                       │
│                                │
│ has_page_dir =                 │
│   subdirs ∩ {"pages",          │
│     "page_objects","pom"}      │
│   ≠ ∅ ?                       │
└────────────┬───────────────────┘
             │
             ▼
      ┌──────┴──────┐
      │ ¿Ambos      │
      │ presentes?  │
      └──────┬──────┘
        Sí ╱   ╲ No
          ╱     ╲
         ▼       ▼
    ┌────────┐  ┌──────────────────────────┐
    │return []│  │ Construir mensaje:       │
    │(0 viol.)│  │ "Missing: tests dir,     │
    └────────┘  │  page objects dir"        │
                │                          │
                │ return [Violation(        │
                │   MISSING_LAYER_STRUCTURE │
                │   severity=CRITICAL       │
                │   line_number=None)]      │
                └──────────────────────────┘
```

---

## 5. AdaptationChecker — Validación de Page Objects

El checker más complejo: 4 sub-checks con AST visitors y estado cross-file.

### 5.1 Flujo Principal

```
check(file_path, tree=None)
    │
    ▼
┌────────────────────────────────┐
│ Leer archivo (siempre, para    │
│ regex sobre source_code):      │
│ source_code = open(...).read() │
│                                │
│ Si tree es None:               │
│   tree = ast.parse(source_code)│
│ (Si tree fue pre-parseado por  │
│  StaticAnalyzer, se reutiliza) │
└────────────┬───────────────────┘
             │
     ┌───────┴───────┬────────────────┬──────────────────┐
     ▼               ▼                ▼                  ▼
┌──────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────────┐
│_check_   │  │_check_     │  │_check_      │  │_check_       │
│forbidden_│  │assertions  │  │business_    │  │duplicate_    │
│imports   │  │            │  │logic        │  │locators      │
│          │  │ AST Visitor│  │ AST Visitor  │  │ Regex        │
│ ast.walk │  │ _Assertion │  │ _Business   │  │ + Registry   │
│          │  │  Visitor   │  │  LogicVisit │  │              │
└────┬─────┘  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘
     │              │                │                 │
     ▼              ▼                ▼                 ▼
  FORBIDDEN_    ASSERTION_    BUSINESS_LOGIC_    DUPLICATE_
  IMPORT        IN_POM        IN_POM             LOCATOR
  (HIGH)        (HIGH)        (MEDIUM)           (MEDIUM)
```

### 5.2 Detección de Imports Prohibidos

```
_check_forbidden_imports(file_path, tree)
    │
    ▼
┌──────────────────────────────────┐
│ for node in ast.walk(tree):      │
│                                  │
│   ¿Es ast.Import?               │
│   ├── Sí: ¿alias.name ∈         │
│   │       {"pytest","unittest"}? │
│   │   ├── Sí → VIOLATION         │
│   │   └── No → skip             │
│   │                              │
│   ¿Es ast.ImportFrom?           │
│   ├── Sí: ¿module empieza con   │
│   │       "pytest" o "unittest"? │
│   │   ├── Sí → VIOLATION         │
│   │   └── No → skip             │
│   │                              │
│   └── Otro nodo → skip          │
└──────────────────────────────────┘

Ejemplo detectado:
    import pytest          → FORBIDDEN_IMPORT
    from unittest import X → FORBIDDEN_IMPORT
    from selenium import X → OK (esperado en Page Objects)
```

### 5.3 AST Visitor: Assertions en POM

```
_AssertionVisitor recorre el AST rastreando contexto:

    visit_ClassDef ──► _in_class = True
        │
        └─► visit_FunctionDef ──► _in_method = True
                │
                └─► visit_Assert
                        │
                        ▼
                    ┌──────────────────────┐
                    │ ¿_in_class AND       │
                    │  _in_method?         │
                    │                      │
                    │  Sí → VIOLATION      │
                    │       ASSERTION_IN_  │
                    │       POM (HIGH)     │
                    │                      │
                    │  No → skip           │
                    │  (assert a nivel     │
                    │   módulo = OK)       │
                    └──────────────────────┘

Ejemplo:
    class LoginPage:          ← _in_class = True
        def verify(self):     ← _in_method = True
            assert x == y     ← ¡VIOLACIÓN!

    assert True               ← _in_class = False → OK
```

### 5.4 AST Visitor: Lógica de Negocio en POM

```
_BusinessLogicVisitor — misma estructura que _AssertionVisitor:

    visit_ClassDef ──► _in_class = True
        │
        └─► visit_FunctionDef ──► _in_method = True
                │
                ├─► visit_If    ──► "if/else"    → VIOLATION
                ├─► visit_For   ──► "for loop"   → VIOLATION
                └─► visit_While ──► "while loop" → VIOLATION

    Solo dentro de class + method → BUSINESS_LOGIC_IN_POM (MEDIUM)

Ejemplo:
    class CheckoutPage:
        def apply_discount(self, code):
            if code == "SAVE20":     ← ¡VIOLACIÓN! if/else
                ...
            for item in items:       ← ¡VIOLACIÓN! for loop
                ...
```

---

## 6. QualityChecker — Calidad de Tests

### 6.1 Flujo Principal

```
check(file_path, tree=None)
    │
    ▼
┌────────────────────────────────┐
│ Si tree es None:               │
│   source = open(...).read()    │
│   tree = ast.parse(source)     │
│ (Normalmente tree viene        │
│  pre-parseado del Analyzer)    │
└────────────┬───────────────────┘
             │
     ┌───────┴──────────┬──────────────────┐
     ▼                  ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│_check_       │ │_check_long_  │ │_check_test_  │
│hardcoded_data│ │functions     │ │naming        │
│              │ │              │ │              │
│ AST Visitor  │ │ ast.walk     │ │ ast.walk +   │
│ _Hardcoded   │ │ + lineno     │ │ regex match  │
│  DataVisitor │ │ counting     │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ▼                ▼                ▼
  HARDCODED_       LONG_TEST_       POOR_TEST_
  TEST_DATA        FUNCTION         NAMING
  (HIGH)           (MEDIUM)         (LOW)
```

### 6.2 Detección de Datos Hardcoded

```
_HardcodedDataVisitor

    visit_FunctionDef("test_login")
        │
        └─► _in_test = True
              │
              └─► visit_Constant(node)
                      │
                      ▼
                  ┌─────────────────────────────────┐
                  │ value = "user@example.com"       │
                  │                                  │
                  │ ¿len(value) < 5? → skip          │
                  │                                  │
                  │ ¿EMAIL_PATTERN.search(value)?    │
                  │   ✓ → VIOLATION (email)          │
                  │                                  │
                  │ ¿URL_PATTERN.search(value)?      │
                  │   ✓ → VIOLATION (URL)            │
                  │                                  │
                  │ ¿PHONE_PATTERN.search(value)?    │
                  │   ✓ → VIOLATION (teléfono)       │
                  │                                  │
                  │ ¿contiene "password"/"passwd"/   │
                  │  "pwd" (case-insensitive)?       │
                  │   ✓ → VIOLATION (contraseña)     │
                  └─────────────────────────────────┘

IMPORTANTE: Solo se chequean strings DENTRO de funciones test_*.
Strings a nivel de módulo (constantes, docstrings) NO se detectan.

Ejemplo:
    BASE_URL = "https://api.com"    ← NO detectado (fuera de test)

    def test_login():
        email = "admin@test.com"    ← VIOLACIÓN (email)
        url = "https://api.com/v1"  ← VIOLACIÓN (URL)
        phone = "555-123-4567"      ← VIOLACIÓN (teléfono)
        pwd = "MyPassword123"       ← VIOLACIÓN (password keyword)
```

### 6.3 Detección de Funciones Largas

```
_check_long_functions(file_path, tree)
    │
    ▼
┌──────────────────────────────────────┐
│ for node in ast.walk(tree):          │
│   if FunctionDef AND name="test_*":  │
│                                      │
│     Recoger todos los lineno y       │
│     end_lineno de nodos hijos        │
│                                      │
│     length = max_line - min_line + 1 │
│                                      │
│     ┌────────────────────────┐       │
│     │ ¿length > 50?          │       │
│     │  Sí → VIOLATION        │       │
│     │       LONG_TEST_FUNC   │       │
│     │  No → OK               │       │
│     └────────────────────────┘       │
└──────────────────────────────────────┘

Ejemplo:
    def test_checkout():     ← línea 1
        step_1 = "..."       ← línea 2
        step_2 = "..."       ← línea 3
        ...                     ...
        step_55 = "..."      ← línea 56
        assert True          ← línea 57
                             length = 57 > 50 → ¡VIOLACIÓN!
```

### 6.4 Detección de Nombres Genéricos

```
_check_test_naming(file_path, tree)
    │
    ▼
┌──────────────────────────────────────┐
│ for node in ast.walk(tree):          │
│   if FunctionDef AND name="test_*":  │
│                                      │
│     ┌──────────────────────────────┐ │
│     │ GENERIC_NAME_RE.match(name)? │ │
│     │                              │ │
│     │ Patrón:                      │ │
│     │   ^test_[0-9]+$   → test_1  │ │
│     │   ^test_[a-z]$    → test_a  │ │
│     │   ^test_case[0-9]*$ → test_ │ │
│     │                    case1     │ │
│     │                              │ │
│     │ ¿Match?                      │ │
│     │   Sí → POOR_TEST_NAMING     │ │
│     │   No → OK (descriptivo)     │ │
│     └──────────────────────────────┘ │
└──────────────────────────────────────┘

Ejemplos:
    def test_1():                    ← ¡VIOLACIÓN! genérico
    def test_a():                    ← ¡VIOLACIÓN! genérico
    def test_case1():                ← ¡VIOLACIÓN! genérico
    def test_user_can_login():       ← OK (descriptivo)
    def test_checkout_total():       ← OK (descriptivo)
```

---

## 7. Mapa de Visitors AST

Fase 3 introduce 3 nuevos AST Visitors (Fase 2 tenía 1):

```
                       ast.NodeVisitor
                            │
            ┌───────────────┼───────────────────────┐
            │               │                       │
            ▼               ▼                       ▼
┌───────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│BrowserAPICall     │ │_AssertionVisitor│ │_BusinessLogic    │
│Visitor (Fase 2)   │ │   (Fase 3)      │ │Visitor (Fase 3)  │
│                   │ │                 │ │                  │
│Contexto:          │ │Contexto:        │ │Contexto:         │
│ inside_test_func  │ │ _in_class       │ │ _in_class        │
│                   │ │ _in_method      │ │ _in_method       │
│Detecta:           │ │                 │ │                  │
│ visit_FunctionDef │ │Detecta:         │ │Detecta:          │
│ visit_Call        │ │ visit_ClassDef  │ │ visit_ClassDef   │
│                   │ │ visit_FuncDef   │ │ visit_FuncDef    │
│Usado por:         │ │ visit_Assert    │ │ visit_If         │
│ DefinitionChecker │ │                 │ │ visit_For        │
│                   │ │Usado por:       │ │ visit_While      │
│                   │ │ AdaptationCheck │ │                  │
│                   │ │                 │ │Usado por:        │
│                   │ │                 │ │ AdaptationChecker│
└───────────────────┘ └─────────────────┘ └──────────────────┘

                            ┌──────────────────┐
                            │_HardcodedData    │
                            │Visitor (Fase 3)  │
                            │                  │
                            │Contexto:         │
                            │ _in_test         │
                            │                  │
                            │Detecta:          │
                            │ visit_FunctionDef│
                            │ visit_Constant   │
                            │                  │
                            │Usado por:        │
                            │ QualityChecker   │
                            └──────────────────┘

Patrón común de todos los visitors:
    1. Entrar en contexto (set flag True)
    2. generic_visit(node) — recorrer hijos
    3. Restaurar contexto anterior (set flag prev)
    → Esto permite funciones anidadas sin contaminar estado
```

---

## 8. Flujo de Detección de Locators Duplicados

Este es el único sub-check que mantiene **estado entre archivos**:

```
AdaptationChecker._locator_registry = {}  (se limpia en __init__)

    Archivo 1: login_page.py
    ┌─────────────────────────────────────┐
    │ class LoginPage:                    │
    │   loc = (By.ID, "username")         │
    │   loc2 = (By.CSS_SELECTOR, "#btn")  │
    └─────────────────────────────────────┘
         │
         ▼ regex extrae: "username", "#btn"
         │
    ┌────────────────────────────────────────┐
    │ registry:                              │
    │   "username" → [login_page.py]         │
    │   "#btn"     → [login_page.py]         │
    │                                        │
    │ No hay duplicados → 0 violaciones      │
    └────────────────────────────────────────┘

    Archivo 2: checkout_page.py
    ┌─────────────────────────────────────┐
    │ class CheckoutPage:                 │
    │   submit = (By.CSS_SELECTOR, "#btn")│  ← "#btn" ya existe!
    │   total = (By.ID, "total")          │
    └─────────────────────────────────────┘
         │
         ▼ regex extrae: "#btn", "total"
         │
    ┌────────────────────────────────────────┐
    │ "#btn" ya está en registry             │
    │   → DUPLICATE_LOCATOR violation        │
    │     "Also found in: login_page.py"     │
    │                                        │
    │ registry actualizado:                  │
    │   "username" → [login_page.py]         │
    │   "#btn"     → [login_page.py,         │
    │                 checkout_page.py]       │
    │   "total"    → [checkout_page.py]      │
    └────────────────────────────────────────┘

Regex utilizado:
    By\.\w+,\s*["']([^"']+)["']
                     ^^^^^^^^
                     Grupo capturado = selector

Ejemplos que captura:
    (By.ID, "username")          → "username"
    (By.CSS_SELECTOR, "#submit") → "#submit"
    (By.XPATH, "//input[@id]")   → "//input[@id]"
```

---

## 9. Mapa Completo de Violaciones

Las 9 violaciones detectadas, agrupadas por checker y severidad:

```
┌─────────┬───────────────────────┬────────────────────┬─────────────┐
│Severidad│ Violación             │ Checker            │ Técnica     │
├─────────┼───────────────────────┼────────────────────┼─────────────┤
│         │ ADAPTATION_IN_        │ DefinitionChecker  │ AST Visitor │
│CRITICAL │ DEFINITION            │ (Fase 2)           │ visit_Call  │
│ (-10)   ├───────────────────────┼────────────────────┼─────────────┤
│         │ MISSING_LAYER_        │ StructureChecker   │ Filesystem  │
│         │ STRUCTURE             │ (Fase 3)           │ iterdir()   │
├─────────┼───────────────────────┼────────────────────┼─────────────┤
│         │ ASSERTION_IN_POM      │ AdaptationChecker  │ AST Visitor │
│         │                       │                    │ visit_Assert│
│ HIGH    ├───────────────────────┤                    ├─────────────┤
│ (-5)    │ FORBIDDEN_IMPORT      │ AdaptationChecker  │ ast.walk    │
│         │                       │                    │ Import nodes│
│         ├───────────────────────┼────────────────────┼─────────────┤
│         │ HARDCODED_TEST_DATA   │ QualityChecker     │ AST Visitor │
│         │                       │                    │ + Regex     │
├─────────┼───────────────────────┼────────────────────┼─────────────┤
│         │ BUSINESS_LOGIC_IN_POM │ AdaptationChecker  │ AST Visitor │
│         │                       │                    │ If/For/While│
│ MEDIUM  ├───────────────────────┤                    ├─────────────┤
│ (-2)    │ DUPLICATE_LOCATOR     │ AdaptationChecker  │ Regex +     │
│         │                       │                    │ Registry    │
│         ├───────────────────────┼────────────────────┼─────────────┤
│         │ LONG_TEST_FUNCTION    │ QualityChecker     │ ast.walk    │
│         │                       │                    │ + lineno    │
├─────────┼───────────────────────┼────────────────────┼─────────────┤
│ LOW     │ POOR_TEST_NAMING      │ QualityChecker     │ ast.walk    │
│ (-1)    │                       │                    │ + Regex     │
└─────────┴───────────────────────┴────────────────────┴─────────────┘

Técnicas utilizadas en Fase 3:
    ★ AST Visitor Pattern   → asserts, business logic, hardcoded data
    ★ ast.walk()            → imports, long functions, naming
    ★ Regex                 → emails, URLs, phones, locators
    ★ Filesystem            → directory structure
    ★ Cross-file state      → duplicate locators (registry)
```

---

## 10. Interacción entre Componentes

Diagrama de secuencia simplificado para un análisis completo:

```
StaticAnalyzer          Structure    Definition   Adaptation   Quality
     │                  Checker      Checker      Checker      Checker
     │                     │            │            │            │
     │── check_project ──►│            │            │            │
     │◄── [0 or 1 viol]──│            │            │            │
     │── check_project ──────────────►│            │            │
     │◄── []──────────────────────────│            │            │
     │── check_project ──────────────────────────►│            │
     │◄── []──────────────────────────────────────│            │
     │── check_project ──────────────────────────────────────►│
     │◄── []──────────────────────────────────────────────────│
     │                                                         │
     │ ═══ Discover .py files ═══                              │
     │                                                         │
     │ ═══ Para test_login.py: ═══                             │
     │ ast.parse(test_login.py) → tree  ← PARSE UNA VEZ      │
     │                                                         │
     │── can_check(test_login.py) ──►│            │            │
     │◄── False ─────────────────────│            │            │
     │── can_check(test_login.py) ──────────────►│            │
     │◄── True ──────────────────────────────────│            │
     │── check(test_login.py, tree) ────────────►│            │
     │◄── [violations] ─────────────────────────│            │
     │── can_check(test_login.py) ────────────────────────────►│
     │◄── False ───────────────────────────────────────────────│
     │── can_check(test_login.py) ──────────────────────────────►│
     │◄── True ──────────────────────────────────────────────────│
     │── check(test_login.py, tree) ────────────────────────────►│
     │◄── [violations] ─────────────────────────────────────────│
     │                                                           │
     │ ═══ Para login_page.py: ═══                               │
     │ ast.parse(login_page.py) → tree  ← PARSE UNA VEZ       │
     │                                                          │
     │── can_check(login_page.py) ─►│            │              │
     │◄── False ────────────────────│            │              │
     │── can_check(login_page.py) ─────────────►│              │
     │◄── False ────────────────────────────────│              │
     │── can_check(login_page.py) ───────────────────────────►│
     │◄── True ──────────────────────────────────────────────│
     │── check(login_page.py, tree) ─────────────────────────►│
     │◄── [violations] ─────────────────────────────────────│
     │── can_check(login_page.py) ──────────────────────────────►│
     │◄── False ─────────────────────────────────────────────────│
     │                                                           │
     │ ═══ Aggregate all violations ═══                          │
     │ ═══ calculate_score() ═══                                 │
     │ ═══ Return Report ═══                                     │
```

**Flujo de datos:**
1. **Project-level**: Solo StructureChecker produce datos (0 o 1 violación)
2. **Test files**: DefinitionChecker + QualityChecker ambos analizan
3. **Page Object files**: Solo AdaptationChecker analiza
4. **Otros .py**: Ningún checker los procesa (can_check = False para todos)
5. **Agregación**: Todas las violaciones se acumulan en un único Report
