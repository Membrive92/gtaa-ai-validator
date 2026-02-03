# Fase 8 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Fase 8](#1-visión-general-de-la-fase-8)
2. [GherkinParser: Parsing de archivos .feature](#2-gherkinparser-parsing-de-archivos-feature)
3. [BDDChecker: Verificación de archivos BDD](#3-bddchecker-verificación-de-archivos-bdd)
4. [Detección de Step Definitions](#4-detección-de-step-definitions)
5. [Verificación de archivos .feature](#5-verificación-de-archivos-feature)
6. [Verificación de Step Definitions](#6-verificación-de-step-definitions)
7. [Detección Cross-File: DUPLICATE_STEP_PATTERN](#7-detección-cross-file-duplicate_step_pattern)
8. [Integración en StaticAnalyzer](#8-integración-en-staticanalyzer)
9. [Mapa de Violaciones BDD](#9-mapa-de-violaciones-bdd)
10. [Mapa de Tests](#10-mapa-de-tests)
11. [Decisiones Arquitectónicas](#11-decisiones-arquitectónicas)

---

## 1. Visión General de la Fase 8

La Fase 8 añade soporte completo para proyectos BDD (Behave y pytest-bdd), analizando archivos `.feature` (Gherkin) y step definitions para detectar violaciones arquitectónicas en la capa de definición BDD.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Fase 8: Soporte BDD/Gherkin                          │
│                                                                             │
│  Problema:                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Proyectos BDD con Behave/pytest-bdd no eran analizados:              │  │
│  │                                                                       │  │
│  │  login.feature:                                                       │  │
│  │    When I type "admin" into //input[@id='username']  ← DETALLE IMPL  │  │
│  │    (XPath en lenguaje de negocio)                                    │  │
│  │                                                                       │  │
│  │  steps/login_steps.py:                                               │  │
│  │    @given("I am on the login page")                                  │  │
│  │    def step_login(context):                                          │  │
│  │        context.driver.find_element(...)  ← BROWSER DIRECTO          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Solución:                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. GherkinParser   — parser regex para archivos .feature             │  │
│  │ 2. BDDChecker      — 5 nuevas violaciones BDD                        │  │
│  │ 3. File discovery  — incluye *.feature además de *.py                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Nuevos módulos:                                                            │
│  ├── parsers/__init__.py              — nuevo paquete                       │
│  ├── parsers/gherkin_parser.py        — GherkinParser + dataclasses        │
│  ├── checkers/bdd_checker.py          — BDDChecker (5 violaciones)         │
│  │                                                                          │
│  Módulos modificados:                                                       │
│  ├── models.py                        — 5 nuevos ViolationType             │
│  ├── file_classifier.py               — BDD_IMPORTS, is_bdd flag           │
│  ├── analyzers/static_analyzer.py     — file discovery + BDDChecker        │
│  ├── llm/prompts.py                   — capas BDD en SYSTEM_PROMPT         │
│  ├── llm/client.py                    — enrichments BDD                    │
│  ├── llm/gemini_client.py             — VALID_TYPES += 2 BDD               │
│  │                                                                          │
│  Tests: 274 → 317 (+43)                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. GherkinParser: Parsing de archivos .feature

`parsers/gherkin_parser.py:71-183`

Parser ligero basado en regex que extrae la estructura de archivos Gherkin sin dependencias externas.

### Dataclasses

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Estructuras de datos del parser                                             │
│                                                                             │
│  GherkinStep                                                                │
│  ├── keyword: str      # "Given", "When", "Then", "And", "But"             │
│  ├── text: str         # Texto del step sin el keyword                     │
│  └── line: int         # Número de línea en el archivo                     │
│                                                                             │
│  GherkinScenario                                                            │
│  ├── name: str                                                              │
│  ├── line: int                                                              │
│  ├── steps: List[GherkinStep]                                              │
│  ├── is_outline: bool         # True si es Scenario Outline                │
│  ├── has_given: bool          # Property: ¿tiene Given efectivo?           │
│  ├── has_when: bool           # Property: ¿tiene When efectivo?            │
│  └── has_then: bool           # Property: ¿tiene Then efectivo?            │
│                                                                             │
│  GherkinFeature                                                             │
│  ├── name: str                                                              │
│  ├── line: int                                                              │
│  ├── scenarios: List[GherkinScenario]                                      │
│  └── background: Optional[GherkinScenario]                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de parsing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ GherkinParser.parse(content: str)                                           │
│                                                                             │
│  Entrada: contenido del archivo .feature como string                        │
│                                                                             │
│  for i, line in enumerate(lines, start=1):                                 │
│      │                                                                      │
│      ├── FEATURE_RE.match(line)?                                           │
│      │   └── Crear GherkinFeature(name=match.group(1), line=i)            │
│      │                                                                      │
│      ├── BACKGROUND_RE.match(line)?                                        │
│      │   └── Crear scenario Background, asignar a feature.background       │
│      │                                                                      │
│      ├── SCENARIO_OUTLINE_RE.match(line)?                                  │
│      │   └── Crear GherkinScenario(is_outline=True), append a scenarios   │
│      │                                                                      │
│      ├── SCENARIO_RE.match(line)?                                          │
│      │   └── Crear GherkinScenario, append a feature.scenarios            │
│      │                                                                      │
│      ├── STEP_RE.match(line)?                                              │
│      │   └── Crear GherkinStep, append a current_scenario.steps           │
│      │                                                                      │
│      ├── TAG_RE.match(line)?                                               │
│      │   └── Ignorar (@smoke, @regression, etc.)                          │
│      │                                                                      │
│      └── COMMENT_RE.match(line)?                                           │
│          └── Ignorar (# comentarios)                                       │
│                                                                             │
│  Salida: GherkinFeature con toda la estructura parseada                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Herencia de keywords And/But

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ GherkinScenario._has_effective_keyword(keyword: str) -> bool               │
│                                                                             │
│  Problema: And/But heredan el keyword del step anterior                    │
│                                                                             │
│  Ejemplo:                                                                   │
│    Given I am logged in                                                    │
│    And I have items in cart    ← efectivamente es "Given"                  │
│    When I checkout                                                          │
│    Then I see confirmation                                                  │
│    And I receive email         ← efectivamente es "Then"                   │
│                                                                             │
│  Algoritmo:                                                                 │
│    effective = None                                                         │
│    for step in self.steps:                                                 │
│        if step.keyword in ("Given", "When", "Then"):                       │
│            effective = step.keyword    # Actualizar keyword activo         │
│        if effective == keyword:                                            │
│            return True                 # Encontrado                        │
│    return False                                                             │
│                                                                             │
│  has_then usa este método para detectar correctamente verificaciones       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. BDDChecker: Verificación de archivos BDD

`checkers/bdd_checker.py:26-360`

Nuevo checker que hereda de BaseChecker y detecta 5 tipos de violación BDD.

### Estructura del checker

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BDDChecker                                                                  │
│                                                                             │
│  Constantes de clase:                                                       │
│  ├── IMPLEMENTATION_PATTERNS    # 11 regex para detalles técnicos          │
│  ├── BROWSER_METHODS            # find_element, locator, etc.              │
│  ├── BROWSER_OBJECTS            # driver, page, browser, context           │
│  └── MAX_STEP_LINES = 15        # Umbral de complejidad                    │
│                                                                             │
│  Métodos principales:                                                       │
│  ├── can_check(file_path)       # ¿Es .feature o step definition?         │
│  ├── check(file_path, tree)     # Bifurca a _check_feature o _check_step  │
│  └── check_project(project)     # Detección cross-file de duplicados      │
│                                                                             │
│  Métodos de verificación:                                                   │
│  ├── _check_feature_file()      # GHERKIN_IMPLEMENTATION_DETAIL            │
│  │                              # MISSING_THEN_STEP                        │
│  └── _check_step_definition()   # STEP_DEF_DIRECT_BROWSER_CALL            │
│                                 # STEP_DEF_TOO_COMPLEX                     │
│                                                                             │
│  Utilidades:                                                                │
│  ├── _is_step_definition_path() # Detecta por directorio/nombre           │
│  ├── _is_step_function()        # Detecta decorador @given/@when/@then    │
│  ├── _get_object_name()         # Extrae nombre de objeto de AST          │
│  └── _collect_step_patterns()   # Extrae patterns para duplicados         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Detección de Step Definitions

### can_check: Filtrado rápido por path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BDDChecker.can_check(file_path: Path) -> bool                              │
│                                                                             │
│  file_path                                                                  │
│      │                                                                      │
│      ├── suffix == ".feature"?                                             │
│      │   └── return True                                                   │
│      │                                                                      │
│      ├── suffix == ".py"?                                                  │
│      │   └── _is_step_definition_path(file_path)?                         │
│      │       ├── "steps" in path.parts?     → True                        │
│      │       ├── "step_defs" in path.parts? → True                        │
│      │       ├── name ends with "_steps.py"? → True                       │
│      │       └── otherwise                   → False                       │
│      │                                                                      │
│      └── otherwise                                                         │
│          └── return False                                                  │
│                                                                             │
│  Ejemplos:                                                                  │
│    "login.feature"           → True  (extensión)                          │
│    "steps/login_steps.py"    → True  (directorio)                         │
│    "login_steps.py"          → True  (nombre)                             │
│    "pages/login_page.py"     → False (no es step def)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### _is_step_function: Validación AST de decoradores

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BDDChecker._is_step_function(node: ast.FunctionDef) -> bool                │
│                                                                             │
│  Detecta si una función tiene decorador @given/@when/@then/@step           │
│                                                                             │
│  for decorator in node.decorator_list:                                     │
│      │                                                                      │
│      ├── isinstance(decorator, ast.Call)?                                  │
│      │   # @given("I am on the login page")                               │
│      │   └── decorator.func.id.lower() in {"given","when","then","step"}? │
│      │       └── return True                                               │
│      │                                                                      │
│      └── isinstance(decorator, ast.Name)?                                  │
│          # @given (sin argumentos, raro)                                   │
│          └── decorator.id.lower() in {"given","when","then","step"}?      │
│              └── return True                                               │
│                                                                             │
│  return False                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Verificación de archivos .feature

`_check_feature_file` detecta 2 tipos de violación.

### GHERKIN_IMPLEMENTATION_DETAIL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Detección de detalles de implementación en steps                           │
│                                                                             │
│  IMPLEMENTATION_PATTERNS:                                                   │
│  ├── //[\w\[\]@='"\.]+       # XPath (//input[@id='user'])                │
│  ├── css=                     # CSS prefix                                 │
│  ├── #[\w-]{3,}              # CSS ID (#username)                         │
│  ├── \.[\w-]{3,}\b           # CSS class (.btn-submit)                    │
│  ├── By\.\w+                  # Selenium By.ID, By.XPATH                  │
│  ├── \[data-[\w-]+           # data attributes ([data-testid)            │
│  ├── https?://\S+            # URLs                                        │
│  ├── SELECT\s+.+\s+FROM      # SQL SELECT                                 │
│  ├── INSERT\s+INTO           # SQL INSERT                                 │
│  ├── localhost:\d+           # localhost URLs                              │
│  └── <[\w/]+>                # HTML tags                                   │
│                                                                             │
│  for scenario in feature.scenarios:                                        │
│      for step in scenario.steps:                                           │
│          for pattern in IMPLEMENTATION_PATTERNS:                           │
│              if pattern.search(step.text):                                 │
│                  → GHERKIN_IMPLEMENTATION_DETAIL (HIGH)                   │
│                  break  # Un match por step suficiente                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MISSING_THEN_STEP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Detección de scenarios sin verificación                                     │
│                                                                             │
│  for scenario in feature.scenarios:                                        │
│      │                                                                      │
│      ├── scenario.has_then?                                                │
│      │   └── OK (tiene verificación)                                      │
│      │                                                                      │
│      └── not scenario.has_then AND len(steps) > 0?                        │
│          └── → MISSING_THEN_STEP (MEDIUM)                                 │
│                                                                             │
│  Nota: has_then usa _has_effective_keyword que considera And/But           │
│                                                                             │
│  Ejemplo de violación:                                                      │
│    Scenario: User logs in with invalid credentials                         │
│      Given I am on the login page                                          │
│      When I enter invalid credentials                                       │
│      And I click submit                                                     │
│      # ← Sin Then: no verifica el resultado esperado                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Verificación de Step Definitions

`_check_step_definition` detecta 2 tipos de violación en archivos Python.

### STEP_DEF_DIRECT_BROWSER_CALL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Detección de llamadas directas al navegador en step definitions            │
│                                                                             │
│  BROWSER_METHODS:                                                           │
│  ├── Selenium: find_element, find_elements, find_element_by_*             │
│  └── Playwright: locator, query_selector, wait_for_selector               │
│                                                                             │
│  BROWSER_OBJECTS:                                                           │
│  └── driver, page, browser, context                                        │
│                                                                             │
│  for func_node in ast.walk(tree):                                          │
│      if not _is_step_function(func_node):                                  │
│          continue                                                           │
│                                                                             │
│      for node in ast.walk(func_node):                                      │
│          if isinstance(node, ast.Call):                                    │
│              if isinstance(node.func, ast.Attribute):                      │
│                  method = node.func.attr                                   │
│                  object = _get_object_name(node.func.value)               │
│                                                                             │
│                  if method in BROWSER_METHODS and object in BROWSER_OBJECTS│
│                      → STEP_DEF_DIRECT_BROWSER_CALL (CRITICAL)            │
│                                                                             │
│  Ejemplo de violación:                                                      │
│    @given("I am on the login page")                                        │
│    def step_login(context):                                                │
│        context.driver.find_element("id", "username")  ← VIOLACIÓN         │
│        # Debería usar: context.login_page.navigate()                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### STEP_DEF_TOO_COMPLEX

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Detección de step definitions demasiado largas                             │
│                                                                             │
│  MAX_STEP_LINES = 15                                                        │
│                                                                             │
│  for func_node in ast.walk(tree):                                          │
│      if not _is_step_function(func_node):                                  │
│          continue                                                           │
│                                                                             │
│      if hasattr(func_node, "end_lineno"):                                  │
│          func_lines = func_node.end_lineno - func_node.lineno + 1         │
│                                                                             │
│          if func_lines > MAX_STEP_LINES:                                   │
│              → STEP_DEF_TOO_COMPLEX (MEDIUM)                               │
│                                                                             │
│  Ejemplo de violación:                                                      │
│    @then("I should see the dashboard")                                     │
│    def step_verify_dashboard(context):                                     │
│        dashboard = context.driver.find_element(...)                        │
│        assert dashboard is not None                                        │
│        title = context.driver.find_element(...)                           │
│        assert title.text == "Dashboard"                                    │
│        ... (18 líneas total)                                               │
│        # Debería delegar a un Page Object                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Detección Cross-File: DUPLICATE_STEP_PATTERN

`check_project` detecta patterns duplicados entre archivos de step definitions.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BDDChecker.check_project(project_path: Path)                               │
│                                                                             │
│  FASE 1: Recolectar patterns de todos los step files                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ self._step_patterns = {}  # Reset                                   │   │
│  │                                                                     │   │
│  │ for py_file in project_path.rglob("*.py"):                         │   │
│  │     if _is_step_definition_path(py_file):                          │   │
│  │         _collect_step_patterns(py_file)                            │   │
│  │             │                                                       │   │
│  │             └── Parse AST, find @given/@when/@then decorators      │   │
│  │                 Extract string argument → add to _step_patterns    │   │
│  │                                                                     │   │
│  │ Resultado:                                                          │   │
│  │   _step_patterns = {                                                │   │
│  │     "I am on the login page": [login_steps.py, search_steps.py],   │   │
│  │     "I search for {query}": [search_steps.py],                     │   │
│  │   }                                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: Detectar duplicados                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ for pattern, files in _step_patterns.items():                      │   │
│  │     if len(files) > 1:                                             │   │
│  │         for dup_file in files[1:]:  # Reportar en archivos extras │   │
│  │             → DUPLICATE_STEP_PATTERN (LOW)                         │   │
│  │               message: "También definido en: {files[0]}"           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Integración en StaticAnalyzer

### File discovery ampliado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ StaticAnalyzer._discover_python_files()                                     │
│                                                                             │
│  Antes (Fase 7):                                                            │
│    files = list(project_path.rglob("*.py"))                                │
│                                                                             │
│  Ahora (Fase 8):                                                            │
│    py_files = list(project_path.rglob("*.py"))                             │
│    feature_files = list(project_path.rglob("*.feature"))                   │
│    files = py_files + feature_files                                        │
│                                                                             │
│  Filtros de exclusión (sin cambios):                                        │
│    - venv/, .venv/, env/, __pycache__/, .git/, node_modules/              │
│    - conftest.py, __init__.py, setup.py                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### _check_file para archivos .feature

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ StaticAnalyzer._check_file(file_path)                                       │
│                                                                             │
│  if file_path.suffix == ".feature":                                        │
│      # No parsear AST (no es Python)                                       │
│      tree = None                                                            │
│      source = ""  # No necesario para BDDChecker                           │
│      classification = ClassificationResult(file_type="unknown")            │
│                                                                             │
│      if verbose:                                                            │
│          print(f"  [BDD] {file_path.name}")                                │
│  else:                                                                      │
│      # Flujo normal: parsear AST, clasificar, etc.                         │
│      source = file_path.read_text(encoding="utf-8")                        │
│      tree = ast.parse(source)                                              │
│      classification = classifier.classify_detailed(...)                    │
│                                                                             │
│  # Pasar a checkers (BDDChecker maneja .feature internamente)              │
│  for checker in self.checkers:                                             │
│      if checker.can_check(file_path):                                      │
│          violations.extend(checker.check(file_path, tree, ...))            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Lista de checkers actualizada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ StaticAnalyzer._initialize_checkers()                                       │
│                                                                             │
│  return [                                                                   │
│      DefinitionChecker(),    # ADAPTATION_IN_DEFINITION                    │
│      StructureChecker(),     # MISSING_LAYER_STRUCTURE                     │
│      AdaptationChecker(),    # ASSERTION_IN_POM, FORBIDDEN_IMPORT, ...     │
│      QualityChecker(),       # HARDCODED_TEST_DATA, LONG_TEST_FUNCTION, ...│
│      BDDChecker(),           # ← NUEVO: 5 violaciones BDD                  │
│  ]                                                                          │
│                                                                             │
│  Total: 5 checkers (antes: 4)                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Mapa de Violaciones BDD

### 5 nuevas violaciones (Fase 8)

| Violación | Severidad | Archivo | Técnica |
|-----------|-----------|---------|---------|
| `GHERKIN_IMPLEMENTATION_DETAIL` | HIGH | .feature | Regex (11 patrones) |
| `STEP_DEF_DIRECT_BROWSER_CALL` | CRITICAL | steps/*.py | AST (Call → Attribute) |
| `STEP_DEF_TOO_COMPLEX` | MEDIUM | steps/*.py | AST (lineno count) |
| `MISSING_THEN_STEP` | MEDIUM | .feature | GherkinParser (has_then) |
| `DUPLICATE_STEP_PATTERN` | LOW | steps/*.py | check_project cross-file |

### Cobertura total actualizada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Violaciones por capa gTAA                                                   │
│                                                                             │
│  Test Definition Layer (tests/):                                            │
│  ├── ADAPTATION_IN_DEFINITION      (CRITICAL) — DefinitionChecker          │
│  ├── HARDCODED_TEST_DATA           (HIGH)     — QualityChecker             │
│  ├── LONG_TEST_FUNCTION            (MEDIUM)   — QualityChecker             │
│  ├── POOR_TEST_NAMING              (LOW)      — QualityChecker             │
│  ├── BROAD_EXCEPTION_HANDLING      (MEDIUM)   — QualityChecker             │
│  ├── HARDCODED_CONFIGURATION       (HIGH)     — QualityChecker             │
│  └── SHARED_MUTABLE_STATE          (HIGH)     — QualityChecker             │
│                                                                             │
│  Test Definition Layer BDD (.feature):                      ← FASE 8       │
│  ├── GHERKIN_IMPLEMENTATION_DETAIL (HIGH)     — BDDChecker                 │
│  └── MISSING_THEN_STEP             (MEDIUM)   — BDDChecker                 │
│                                                                             │
│  Test Adaptation Layer (pages/):                                            │
│  ├── ASSERTION_IN_POM              (HIGH)     — AdaptationChecker          │
│  ├── FORBIDDEN_IMPORT              (HIGH)     — AdaptationChecker          │
│  ├── BUSINESS_LOGIC_IN_POM         (MEDIUM)   — AdaptationChecker          │
│  └── DUPLICATE_LOCATOR             (MEDIUM)   — AdaptationChecker          │
│                                                                             │
│  Test Adaptation Layer BDD (steps/):                        ← FASE 8       │
│  ├── STEP_DEF_DIRECT_BROWSER_CALL  (CRITICAL) — BDDChecker                 │
│  ├── STEP_DEF_TOO_COMPLEX          (MEDIUM)   — BDDChecker                 │
│  └── DUPLICATE_STEP_PATTERN        (LOW)      — BDDChecker (check_project) │
│                                                                             │
│  Project Structure:                                                         │
│  └── MISSING_LAYER_STRUCTURE       (CRITICAL) — StructureChecker           │
│                                                                             │
│  Semánticas (LLM):                                                          │
│  ├── UNCLEAR_TEST_PURPOSE          (MEDIUM)   — MockLLMClient/Gemini       │
│  ├── PAGE_OBJECT_DOES_TOO_MUCH     (HIGH)     — MockLLMClient/Gemini       │
│  ├── IMPLICIT_TEST_DEPENDENCY      (HIGH)     — MockLLMClient/Gemini       │
│  ├── MISSING_WAIT_STRATEGY         (MEDIUM)   — MockLLMClient/Gemini       │
│  ├── MISSING_AAA_STRUCTURE         (MEDIUM)   — MockLLMClient/Gemini       │
│  └── MIXED_ABSTRACTION_LEVEL       (MEDIUM)   — MockLLMClient/Gemini       │
│                                                                             │
│  Total: 23 violaciones (18 anteriores + 5 BDD)                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Mapa de Tests

### Tests nuevos (Fase 8): +43

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_gherkin_parser.py (15 tests)                               │
│                                                                             │
│  TestBasicParsing:                                                          │
│  ├── test_parse_simple_feature                                             │
│  ├── test_parse_multiple_scenarios                                         │
│  ├── test_parse_returns_none_for_empty_content                             │
│  └── test_parse_returns_none_for_no_feature                                │
│                                                                             │
│  TestSteps:                                                                 │
│  ├── test_step_keywords                                                    │
│  ├── test_step_text_extraction                                             │
│  └── test_step_line_numbers                                                │
│                                                                             │
│  TestHasKeywords:                                                           │
│  ├── test_has_all_keywords                                                 │
│  ├── test_missing_then                                                     │
│  ├── test_and_inherits_keyword                                             │
│  └── test_but_inherits_keyword                                             │
│                                                                             │
│  TestBackground:                                                            │
│  └── test_parse_background                                                 │
│                                                                             │
│  TestScenarioOutline:                                                       │
│  └── test_parse_scenario_outline                                           │
│                                                                             │
│  TestCommentsAndTags:                                                       │
│  ├── test_comments_are_ignored                                             │
│  └── test_tags_are_ignored                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_bdd_checker.py (28 tests)                                  │
│                                                                             │
│  TestCanCheck:                                                              │
│  ├── test_feature_file                                                     │
│  ├── test_step_file_in_steps_dir                                           │
│  ├── test_step_file_by_name                                                │
│  ├── test_regular_python_file                                              │
│  ├── test_non_python_non_feature                                           │
│  ├── test_step_defs_dir                                                    │
│  └── test_step_definitions_dir                                             │
│                                                                             │
│  TestIsStepFunction:                                                        │
│  ├── test_given_decorator                                                  │
│  ├── test_when_decorator                                                   │
│  ├── test_then_decorator                                                   │
│  └── test_no_step_decorator                                                │
│                                                                             │
│  TestFeatureFileChecks:                                                     │
│  ├── test_detect_xpath_in_feature                                          │
│  ├── test_detect_url_in_feature                                            │
│  ├── test_detect_sql_in_feature                                            │
│  ├── test_clean_feature_no_violations                                      │
│  ├── test_detect_missing_then                                              │
│  └── test_scenario_with_then_no_missing_then                               │
│                                                                             │
│  TestStepDefinitionChecks:                                                  │
│  ├── test_detect_browser_call_selenium                                     │
│  ├── test_detect_browser_call_playwright                                   │
│  ├── test_clean_step_no_browser_call                                       │
│  ├── test_detect_too_complex_step                                          │
│  └── test_short_step_not_too_complex                                       │
│                                                                             │
│  TestCheckProject:                                                          │
│  ├── test_detect_duplicate_step_pattern                                    │
│  └── test_no_duplicate_when_unique_patterns                                │
│                                                                             │
│  TestIsStepDefinitionPath:                                                  │
│  ├── test_steps_directory                                                  │
│  ├── test_step_prefix                                                      │
│  ├── test_steps_suffix                                                     │
│  └── test_regular_file                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/integration/test_static_analyzer.py (actualizado)                    │
│                                                                             │
│  Cambios:                                                                   │
│  ├── test_initializes_five_checkers (antes: four)                          │
│  ├── checker_types incluye BDDChecker                                      │
│  ├── summary["checker_count"] == 5                                         │
│  └── file discovery incluye .feature                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Totales

| Categoría | Antes (Fase 7) | Después (Fase 8) | Delta |
|-----------|---------------|------------------|-------|
| Tests unitarios | ~230 | ~270 | +40 |
| Tests integración | ~44 | ~47 | +3 |
| **Total** | **274** | **317** | **+43** |

---

## 11. Decisiones Arquitectónicas

Las decisiones técnicas de la Fase 8 están documentadas en [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md):

| ADR | Título | Decisión |
|-----|--------|----------|
| 28 | Parser Gherkin: regex vs dependencia | Regex propio sin dependencias |
| 29 | Herencia de keywords And/But | Rastreo de keyword efectivo |
| 30 | Detección step definitions | Path + validación AST |
| 31 | Duplicados step pattern | check_project cross-file |
| 32 | Detalles implementación Gherkin | Regex específicas por tipo |

---

*Última actualización: 3 de febrero de 2026*
