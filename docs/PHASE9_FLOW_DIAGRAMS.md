# Fase 9 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Fase 9](#1-visión-general-de-la-fase-9)
2. [ParseResult: Interfaz Unificada](#2-parseresult-interfaz-unificada)
3. [TreeSitterBaseParser: Parser Base](#3-treesitterbaseparser-parser-base)
4. [Parsers por Lenguaje](#4-parsers-por-lenguaje)
5. [Factory Function: get_parser_for_file](#5-factory-function-get_parser_for_file)
6. [Checkers Language-Agnostic](#6-checkers-language-agnostic)
7. [Integración en StaticAnalyzer](#7-integración-en-staticanalyzer)
8. [Mapa de Violaciones Multilenguaje](#8-mapa-de-violaciones-multilenguaje)
9. [Ejemplos por Lenguaje](#9-ejemplos-por-lenguaje)
10. [Mapa de Tests](#10-mapa-de-tests)
11. [Decisiones Arquitectónicas](#11-decisiones-arquitectónicas)

---

## 1. Visión General de la Fase 9

La Fase 9 añade soporte completo para proyectos de test automation en **Java**, **JavaScript/TypeScript** y **C#**, además de Python. La clave arquitectónica es la implementación de **checkers language-agnostic** que trabajan con una interfaz unificada `ParseResult`.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Fase 9: Soporte Multilenguaje                             │
│                                                                             │
│  Problema:                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Solo se analizaban proyectos Python. Proyectos Java/JS/C# con        │  │
│  │ las mismas violaciones gTAA no eran detectados:                      │  │
│  │                                                                       │  │
│  │  LoginTest.java:                                                      │  │
│  │    @Test                                                              │  │
│  │    void testLogin() {                                                 │  │
│  │        driver.findElement(By.id("user"));  ← ADAPTATION_IN_DEFINITION│  │
│  │    }                                                                  │  │
│  │                                                                       │  │
│  │  login.spec.ts:                                                       │  │
│  │    test('login', async () => {                                        │  │
│  │        await page.locator('#user');         ← ADAPTATION_IN_DEFINITION│  │
│  │    });                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Solución: Arquitectura Language-Agnostic                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │  │
│  │   │ Python  │  │  Java   │  │  JS/TS  │  │   C#    │                 │  │
│  │   │ Parser  │  │ Parser  │  │ Parser  │  │ Parser  │                 │  │
│  │   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                 │  │
│  │        │            │            │            │                       │  │
│  │        └────────────┴────────────┴────────────┘                       │  │
│  │                         │                                             │  │
│  │                         ▼                                             │  │
│  │              ┌─────────────────────┐                                  │  │
│  │              │     ParseResult     │  ◄── Interfaz unificada         │  │
│  │              │  (imports, classes, │                                  │  │
│  │              │   functions, calls) │                                  │  │
│  │              └──────────┬──────────┘                                  │  │
│  │                         │                                             │  │
│  │                         ▼                                             │  │
│  │     ┌───────────────────────────────────────────────────────┐        │  │
│  │     │          CHECKERS LANGUAGE-AGNOSTIC                   │        │  │
│  │     │  (misma lógica, patrones por extensión)               │        │  │
│  │     │                                                       │        │  │
│  │     │  DefinitionChecker  AdaptationChecker  QualityChecker │        │  │
│  │     └───────────────────────────────────────────────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Nuevos módulos:                                                            │
│  ├── parsers/treesitter_base.py       — Parser base tree-sitter            │
│  ├── parsers/python_parser.py         — Parser Python (ast nativo)         │
│  ├── parsers/java_parser.py           — Parser Java                        │
│  ├── parsers/js_parser.py             — Parser JavaScript/TypeScript       │
│  ├── parsers/csharp_parser.py         — Parser C#                          │
│  │                                                                          │
│  Módulos refactorizados (language-agnostic):                                │
│  ├── checkers/definition_checker.py   — Patrones por extensión             │
│  ├── checkers/adaptation_checker.py   — Patrones por extensión             │
│  ├── checkers/quality_checker.py      — Patrones por extensión             │
│  │                                                                          │
│  Módulos modificados:                                                       │
│  ├── analyzers/static_analyzer.py     — Multi-ext file discovery           │
│  ├── file_classifier.py               — Multi-lang classification          │
│  ├── setup.py                         — Python >=3.10, tree-sitter deps    │
│  │                                                                          │
│  Dependencias nuevas:                                                       │
│  ├── tree-sitter-language-pack>=0.4.0 — Java, JS, TS                       │
│  └── tree-sitter-c-sharp>=0.23.0      — C# (separado)                      │
│                                                                             │
│  Python requerido: >=3.10 (requisito de tree-sitter 0.25.x)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ParseResult: Interfaz Unificada

`parsers/treesitter_base.py:15-90`

La clave de la arquitectura language-agnostic es `ParseResult`, un conjunto de dataclasses que representan la estructura de cualquier archivo de código, independientemente del lenguaje.

### Dataclasses

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Estructuras de datos unificadas (ParseResult)                               │
│                                                                             │
│  ParsedImport                                                               │
│  ├── module: str         # "org.openqa.selenium", "axios", "OpenQA.Selenium"│
│  └── line: int           # Número de línea                                  │
│                                                                             │
│  ParsedFunction                                                             │
│  ├── name: str           # "test_login", "testLogin", "TestLogin"           │
│  ├── line_start: int                                                        │
│  ├── line_end: int                                                          │
│  ├── decorators: List[str]   # ["Test", "given"], ["@Test"], ["[Fact]"]    │
│  └── body_text: str      # Código fuente de la función                      │
│                                                                             │
│  ParsedClass                                                                │
│  ├── name: str           # "LoginPage", "LoginTests"                        │
│  ├── line_start: int                                                        │
│  ├── methods: List[ParsedFunction]                                          │
│  └── is_page_object: bool    # Heurística: *Page, *PageObject              │
│                                                                             │
│  ParsedCall                                                                 │
│  ├── object_name: str    # "driver", "page", "cy", "_driver"                │
│  ├── method_name: str    # "findElement", "locator", "get"                  │
│  ├── line: int                                                              │
│  └── in_function: Optional[str]  # Nombre de la función contenedora        │
│                                                                             │
│  ParsedString                                                               │
│  ├── value: str          # "admin@test.com", "https://example.com"          │
│  ├── line: int                                                              │
│  └── in_function: Optional[str]                                             │
│                                                                             │
│  ParseResult                                                                │
│  ├── imports: List[ParsedImport]                                            │
│  ├── classes: List[ParsedClass]                                             │
│  ├── functions: List[ParsedFunction]  # Top-level functions                 │
│  ├── calls: List[ParsedCall]                                                │
│  └── strings: List[ParsedString]                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Principio de diseño

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Dependency Inversion Principle                                              │
│                                                                             │
│  ANTES (hipotético, no implementado):                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DefinitionChecker                                                  │   │
│  │       │                                                             │   │
│  │       ├──► PythonAST (ast.parse)                                   │   │
│  │       ├──► tree_sitter.Parser("java")                              │   │
│  │       └──► tree_sitter.Parser("typescript")                        │   │
│  │                                                                     │   │
│  │  Problema: Checker acoplado a múltiples implementaciones            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AHORA (implementado):                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DefinitionChecker                                                  │   │
│  │       │                                                             │   │
│  │       └──► ParseResult (abstracción)                               │   │
│  │                 ▲                                                   │   │
│  │                 │                                                   │   │
│  │       ┌─────────┼─────────┬─────────┬─────────┐                    │   │
│  │       │         │         │         │         │                    │   │
│  │   PythonParser  │    JavaParser    JSParser  CSharpParser          │   │
│  │   (ast nativo)  │  (tree-sitter)                                   │   │
│  │                 │                                                   │   │
│  │  Ventaja: Checker solo conoce ParseResult, no parsers concretos    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. TreeSitterBaseParser: Parser Base

`parsers/treesitter_base.py:100-250`

Clase base abstracta que encapsula la lógica común de tree-sitter para Java, JS/TS y C#.

### Estructura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TreeSitterBaseParser                                                        │
│                                                                             │
│  Atributos:                                                                 │
│  ├── language: str           # "java", "javascript", "typescript", "c_sharp"│
│  ├── _parser: tree_sitter.Parser                                           │
│  └── _language: tree_sitter.Language                                       │
│                                                                             │
│  Métodos abstractos (implementar en subclases):                             │
│  ├── _extract_imports(tree) → List[ParsedImport]                           │
│  ├── _extract_classes(tree) → List[ParsedClass]                            │
│  ├── _extract_functions(tree) → List[ParsedFunction]                       │
│  ├── _extract_calls(tree) → List[ParsedCall]                               │
│  └── _extract_strings(tree) → List[ParsedString]                           │
│                                                                             │
│  Método público:                                                            │
│  └── parse(source: str) → ParseResult                                      │
│      │                                                                      │
│      ├── tree = self._parser.parse(bytes(source, "utf-8"))                 │
│      │                                                                      │
│      └── return ParseResult(                                               │
│              imports=self._extract_imports(tree),                          │
│              classes=self._extract_classes(tree),                          │
│              functions=self._extract_functions(tree),                      │
│              calls=self._extract_calls(tree),                              │
│              strings=self._extract_strings(tree),                          │
│          )                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de parsing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TreeSitterBaseParser.parse(source: str) → ParseResult                       │
│                                                                             │
│  source: str (código fuente)                                                │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  tree = self._parser.parse(bytes(source, "utf-8"))                   │  │
│  │                                                                      │  │
│  │  tree-sitter parsea el código a un árbol de sintaxis concreto (CST) │  │
│  │  Similar a AST pero preserva todos los tokens                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Recorrido del árbol con tree-sitter queries                         │  │
│  │                                                                      │  │
│  │  for node in self._walk(tree.root_node):                            │  │
│  │      match node.type:                                                │  │
│  │          case "import_declaration":  → _extract_imports             │  │
│  │          case "class_declaration":   → _extract_classes             │  │
│  │          case "method_declaration":  → _extract_functions           │  │
│  │          case "method_invocation":   → _extract_calls               │  │
│  │          case "string_literal":      → _extract_strings             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│       │                                                                     │
│       ▼                                                                     │
│  ParseResult(imports, classes, functions, calls, strings)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Parsers por Lenguaje

### PythonParser (ast nativo)

`parsers/python_parser.py`

Usa el módulo `ast` de la biblioteca estándar de Python en lugar de tree-sitter.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PythonParser                                                                │
│                                                                             │
│  Ventaja: ast es parte de stdlib, no requiere dependencias                 │
│                                                                             │
│  parse(source: str) → ParseResult                                          │
│       │                                                                     │
│       ├── tree = ast.parse(source)                                         │
│       │                                                                     │
│       ├── _extract_imports: ast.Import, ast.ImportFrom                     │
│       │   └── "from selenium import webdriver" → ParsedImport("selenium")  │
│       │                                                                     │
│       ├── _extract_classes: ast.ClassDef                                   │
│       │   └── "class LoginPage:" → ParsedClass("LoginPage", is_page=True) │
│       │                                                                     │
│       ├── _extract_functions: ast.FunctionDef, ast.AsyncFunctionDef        │
│       │   └── "def test_login():" → ParsedFunction("test_login")          │
│       │                                                                     │
│       ├── _extract_calls: ast.Call con ast.Attribute                       │
│       │   └── "driver.find_element()" → ParsedCall("driver", "find_element")│
│       │                                                                     │
│       └── _extract_strings: ast.Constant (str)                             │
│           └── '"admin@test.com"' → ParsedString("admin@test.com")          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JavaParser

`parsers/java_parser.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ JavaParser (tree-sitter)                                                    │
│                                                                             │
│  Extensiones: .java                                                         │
│                                                                             │
│  Nodos tree-sitter específicos de Java:                                     │
│  ├── import_declaration    → ParsedImport                                  │
│  │   "import org.openqa.selenium.*;"                                       │
│  │                                                                          │
│  ├── class_declaration     → ParsedClass                                   │
│  │   "public class LoginPage { ... }"                                      │
│  │                                                                          │
│  ├── method_declaration    → ParsedFunction                                │
│  │   "@Test public void testLogin() { ... }"                               │
│  │   Decoradores: anotaciones @Test, @BeforeEach, @ParameterizedTest       │
│  │                                                                          │
│  ├── method_invocation     → ParsedCall                                    │
│  │   "driver.findElement(By.id("user"))"                                   │
│  │   object_name = "driver", method_name = "findElement"                   │
│  │                                                                          │
│  └── string_literal        → ParsedString                                  │
│      '"admin@test.com"'                                                    │
│                                                                             │
│  Heurística is_page_object:                                                 │
│  └── class_name.endswith("Page") or class_name.endswith("PageObject")     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JSParser

`parsers/js_parser.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ JSParser (tree-sitter)                                                      │
│                                                                             │
│  Extensiones: .js, .ts, .tsx, .jsx, .mjs, .cjs                             │
│  Lenguajes: javascript, typescript (tree-sitter)                           │
│                                                                             │
│  Nodos tree-sitter específicos de JS/TS:                                    │
│  ├── import_statement      → ParsedImport                                  │
│  │   "import { test } from '@playwright/test';"                            │
│  │                                                                          │
│  ├── class_declaration     → ParsedClass                                   │
│  │   "export class LoginPage { ... }"                                      │
│  │                                                                          │
│  ├── function_declaration  → ParsedFunction                                │
│  │   arrow_function        → ParsedFunction                                │
│  │   "test('login', async ({ page }) => { ... })"                          │
│  │   Decoradores: describe/it/test wrapper detectado                       │
│  │                                                                          │
│  ├── call_expression       → ParsedCall                                    │
│  │   "page.locator('#user')"                                               │
│  │   "cy.get('.button')"                                                   │
│  │                                                                          │
│  └── string / template_string → ParsedString                               │
│      "'admin@test.com'" / `${baseUrl}/login`                               │
│                                                                             │
│  Detección de test wrappers:                                                │
│  ├── describe("...", () => {})                                             │
│  ├── it("...", () => {})                                                   │
│  └── test("...", async () => {})                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CSharpParser

`parsers/csharp_parser.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CSharpParser (tree-sitter-c-sharp)                                          │
│                                                                             │
│  Extensiones: .cs                                                           │
│  Dependencia separada: tree-sitter-c-sharp (no en language-pack)           │
│                                                                             │
│  Nodos tree-sitter específicos de C#:                                       │
│  ├── using_directive       → ParsedImport                                  │
│  │   "using OpenQA.Selenium;"                                              │
│  │                                                                          │
│  ├── class_declaration     → ParsedClass                                   │
│  │   "public class LoginPage { ... }"                                      │
│  │                                                                          │
│  ├── method_declaration    → ParsedFunction                                │
│  │   "[Test] public void TestLogin() { ... }"                              │
│  │   Decoradores: atributos [Test], [Fact], [Theory], [TestMethod]         │
│  │                                                                          │
│  ├── invocation_expression → ParsedCall                                    │
│  │   "driver.FindElement(By.Id("user"))"                                   │
│  │   "_driver.Navigate().GoToUrl(url)"                                     │
│  │                                                                          │
│  └── string_literal        → ParsedString                                  │
│      '"admin@test.com"'                                                    │
│                                                                             │
│  Heurística is_page_object:                                                 │
│  └── class_name ends with "Page" or inherits from "BasePage"              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Factory Function: get_parser_for_file

`parsers/__init__.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ get_parser_for_file(file_path: Path) → Optional[BaseParser]                │
│                                                                             │
│  Factory function que selecciona el parser correcto por extensión          │
│                                                                             │
│  file_path.suffix                                                           │
│       │                                                                     │
│       ├── ".py"                    → PythonParser()                        │
│       │                                                                     │
│       ├── ".java"                  → JavaParser()                          │
│       │                                                                     │
│       ├── ".js", ".mjs", ".cjs"    → JSParser("javascript")               │
│       │                                                                     │
│       ├── ".ts", ".tsx"            → JSParser("typescript")               │
│       │                                                                     │
│       ├── ".cs"                    → CSharpParser()                        │
│       │                                                                     │
│       ├── ".feature"               → GherkinParser() (Fase 8)              │
│       │                                                                     │
│       └── otro                     → None (no soportado)                   │
│                                                                             │
│  Uso en StaticAnalyzer:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  parser = get_parser_for_file(file_path)                              │ │
│  │  if parser:                                                           │ │
│  │      parse_result = parser.parse(source)                              │ │
│  │      for checker in applicable_checkers:                              │ │
│  │          violations += checker.check(file_path, parse_result, ...)    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Checkers Language-Agnostic

### Arquitectura refactorizada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Checkers Language-Agnostic                                                  │
│                                                                             │
│  Principio: UN checker, patrones por extensión                              │
│                                                                             │
│  ANTES (alternativa no implementada):                                       │
│  ├── DefinitionChecker     (Python)                                        │
│  ├── JavaDefinitionChecker (Java)      ← Duplicación de código             │
│  ├── JSDefinitionChecker   (JS/TS)     ← Mismo algoritmo                   │
│  └── CSharpDefinitionChecker (C#)      ← Solo patrones diferentes          │
│                                                                             │
│  AHORA (implementado):                                                      │
│  └── DefinitionChecker (todos los lenguajes)                               │
│          │                                                                  │
│          ├── BROWSER_METHODS_PYTHON = {"find_element", "find_elements"...} │
│          ├── BROWSER_METHODS_JAVA = {"findElement", "findElements"...}     │
│          ├── BROWSER_METHODS_JS = {"locator", "getByRole", "$"...}        │
│          └── BROWSER_METHODS_CSHARP = {"FindElement", "FindElements"...}   │
│                                                                             │
│  Método _get_browser_methods(extension: str) → Set[str]:                   │
│      match extension:                                                       │
│          case ".py": return BROWSER_METHODS_PYTHON                         │
│          case ".java": return BROWSER_METHODS_JAVA                         │
│          case ".js" | ".ts" | ".tsx": return BROWSER_METHODS_JS           │
│          case ".cs": return BROWSER_METHODS_CSHARP                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DefinitionChecker (refactorizado)

`checkers/definition_checker.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ DefinitionChecker — ADAPTATION_IN_DEFINITION                                │
│                                                                             │
│  Detecta llamadas directas al browser en funciones de test                 │
│                                                                             │
│  Patrones por lenguaje:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  BROWSER_METHODS_PYTHON = {                                           │ │
│  │      "find_element", "find_elements", "get", "navigate",              │ │
│  │      "locator", "query_selector", "wait_for_selector"                 │ │
│  │  }                                                                    │ │
│  │                                                                       │ │
│  │  BROWSER_METHODS_JAVA = {                                             │ │
│  │      "findElement", "findElements", "get", "navigate",                │ │
│  │      "switchTo", "manage"                                             │ │
│  │  }                                                                    │ │
│  │                                                                       │ │
│  │  BROWSER_METHODS_JS = {                                               │ │
│  │      "locator", "getByRole", "getByText", "getByTestId",              │ │
│  │      "$", "$$", "get", "visit", "request"                            │ │
│  │  }                                                                    │ │
│  │                                                                       │ │
│  │  BROWSER_METHODS_CSHARP = {                                           │ │
│  │      "FindElement", "FindElements", "Navigate", "SwitchTo",           │ │
│  │      "Manage", "GoToUrl"                                              │ │
│  │  }                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TEST_DECORATORS por lenguaje:                                              │
│  ├── Python: "test_", "pytest.mark", async def test_                       │
│  ├── Java: @Test, @ParameterizedTest, @RepeatedTest                        │
│  ├── JS/TS: test(), it(), describe()                                       │
│  └── C#: [Test], [Fact], [Theory], [TestMethod]                            │
│                                                                             │
│  Algoritmo:                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  def check(file_path, parse_result, file_type):                       │ │
│  │      ext = file_path.suffix                                           │ │
│  │      browser_methods = self._get_browser_methods(ext)                 │ │
│  │                                                                       │ │
│  │      for call in parse_result.calls:                                  │ │
│  │          if call.method_name in browser_methods:                      │ │
│  │              if self._is_in_test_function(call, parse_result, ext):  │ │
│  │                  violations.append(ADAPTATION_IN_DEFINITION)          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AdaptationChecker (refactorizado)

`checkers/adaptation_checker.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AdaptationChecker — Violaciones en Page Objects                             │
│                                                                             │
│  Violaciones detectadas:                                                    │
│  ├── ASSERTION_IN_POM                                                      │
│  ├── FORBIDDEN_IMPORT                                                      │
│  └── BUSINESS_LOGIC_IN_POM                                                 │
│                                                                             │
│  Patrones de assertions por lenguaje:                                       │
│  ├── Python: assert, assertEqual, assertTrue, pytest.raises                │
│  ├── Java: assertEquals, assertTrue, assertThat, Assert.*                  │
│  ├── JS/TS: expect, assert, should, chai.*                                 │
│  └── C#: Assert.*, Should, Expect                                          │
│                                                                             │
│  Forbidden imports por lenguaje:                                            │
│  ├── Python: pytest, unittest, nose                                        │
│  ├── Java: org.junit, org.testng, org.junit.jupiter                        │
│  ├── JS/TS: jest, mocha, jasmine, @playwright/test (en page class)        │
│  └── C#: NUnit.Framework, Xunit, Microsoft.VisualStudio.TestTools          │
│                                                                             │
│  Algoritmo (ejemplo ASSERTION_IN_POM):                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  for cls in parse_result.classes:                                     │ │
│  │      if cls.is_page_object:                                           │ │
│  │          for call in parse_result.calls:                              │ │
│  │              if call.method_name in ASSERTION_METHODS[ext]:           │ │
│  │                  if call.in_function in [m.name for m in cls.methods]:│ │
│  │                      violations.append(ASSERTION_IN_POM)              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### QualityChecker (refactorizado)

`checkers/quality_checker.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ QualityChecker — Violaciones de calidad de código                           │
│                                                                             │
│  Violaciones detectadas:                                                    │
│  ├── HARDCODED_TEST_DATA                                                   │
│  ├── LONG_TEST_FUNCTION                                                    │
│  └── POOR_TEST_NAMING                                                      │
│                                                                             │
│  HARDCODED_TEST_DATA (patrones universales):                                │
│  └── Regex: EMAIL_RE, URL_RE, IP_RE, PASSWORD_RE                           │
│      Funcionan igual para todos los lenguajes                              │
│                                                                             │
│  LONG_TEST_FUNCTION:                                                        │
│  └── MAX_LINES = 50 (configurable)                                         │
│      Detecta line_end - line_start > MAX_LINES                             │
│                                                                             │
│  POOR_TEST_NAMING por lenguaje:                                             │
│  ├── Python: test_\d+$, test_?$, test_[a-z]$                               │
│  ├── Java: test\d+$, test[A-Z]?$                                           │
│  ├── JS/TS: it\(['"]test\s*\d*['"]\), describe\(['"]test['"]\)            │
│  └── C#: Test\d+$, TestMethod\d+$                                          │
│                                                                             │
│  Algoritmo HARDCODED_TEST_DATA:                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  for s in parse_result.strings:                                       │ │
│  │      if self._is_in_test_function(s.in_function, parse_result, ext): │ │
│  │          if EMAIL_RE.search(s.value) or URL_RE.search(s.value):      │ │
│  │              violations.append(HARDCODED_TEST_DATA)                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Integración en StaticAnalyzer

`analyzers/static_analyzer.py`

### File discovery ampliado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ StaticAnalyzer._discover_files()                                            │
│                                                                             │
│  SUPPORTED_EXTENSIONS = {".py", ".java", ".js", ".ts", ".tsx", ".cs",      │
│                          ".feature", ".jsx", ".mjs", ".cjs"}               │
│                                                                             │
│  Antes (Fase 8):                                                            │
│    files = list(project.rglob("*.py")) + list(project.rglob("*.feature"))  │
│                                                                             │
│  Ahora (Fase 9):                                                            │
│    files = []                                                               │
│    for ext in SUPPORTED_EXTENSIONS:                                         │
│        files.extend(project.rglob(f"*{ext}"))                              │
│                                                                             │
│  Exclusiones (sin cambios):                                                 │
│    - venv/, .venv/, env/, __pycache__/, .git/, node_modules/              │
│    - build/, dist/, .pytest_cache/                                         │
│    - conftest.py, __init__.py, setup.py                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### _check_file actualizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ StaticAnalyzer._check_file(file_path: Path)                                 │
│                                                                             │
│  file_path                                                                  │
│       │                                                                     │
│       ├── 1. Leer contenido                                                │
│       │   source = file_path.read_text(encoding="utf-8")                   │
│       │                                                                     │
│       ├── 2. Obtener parser por extensión                                  │
│       │   parser = get_parser_for_file(file_path)                          │
│       │                                                                     │
│       ├── 3. Parsear a ParseResult                                         │
│       │   parse_result = parser.parse(source) if parser else None          │
│       │                                                                     │
│       ├── 4. Clasificar archivo (solo Python por ahora)                    │
│       │   if file_path.suffix == ".py":                                    │
│       │       file_type = classifier.classify_detailed(file_path, source)  │
│       │   else:                                                            │
│       │       file_type = "unknown"  # Los checkers clasifican internamente│
│       │                                                                     │
│       ├── 5. Seleccionar checkers aplicables                               │
│       │   applicable = [c for c in checkers if c.can_check(file_path)]    │
│       │                                                                     │
│       └── 6. Ejecutar checkers                                             │
│           for checker in applicable:                                        │
│               violations += checker.check(file_path, parse_result, file_type)│
│                                                                             │
│  Nota: checkers reciben ParseResult, NO el AST crudo                       │
│        Esto permite independencia del lenguaje                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### can_check por checker

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ can_check por checker                                                       │
│                                                                             │
│  DefinitionChecker.can_check(file_path):                                   │
│      return file_path.suffix in {".py", ".java", ".js", ".ts", ".tsx",    │
│                                  ".jsx", ".mjs", ".cjs", ".cs"}            │
│                                                                             │
│  AdaptationChecker.can_check(file_path):                                   │
│      return file_path.suffix in {".py", ".java", ".js", ".ts", ".tsx",    │
│                                  ".jsx", ".mjs", ".cjs", ".cs"}            │
│                                                                             │
│  QualityChecker.can_check(file_path):                                      │
│      return file_path.suffix in {".py", ".java", ".js", ".ts", ".tsx",    │
│                                  ".jsx", ".mjs", ".cjs", ".cs"}            │
│                                                                             │
│  StructureChecker.can_check(file_path):                                    │
│      return True  # Solo usa check_project, no check por archivo           │
│                                                                             │
│  BDDChecker.can_check(file_path):                                          │
│      return file_path.suffix == ".feature" or                              │
│             (file_path.suffix == ".py" and is_step_definition(file_path)) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Mapa de Violaciones Multilenguaje

### Violaciones soportadas por lenguaje

| Violación | Python | Java | JS/TS | C# | Técnica |
|-----------|--------|------|-------|-----|---------|
| `ADAPTATION_IN_DEFINITION` | ✅ | ✅ | ✅ | ✅ | ParseResult.calls |
| `HARDCODED_TEST_DATA` | ✅ | ✅ | ✅ | ✅ | ParseResult.strings + regex |
| `ASSERTION_IN_POM` | ✅ | ✅ | ✅ | ✅ | ParseResult.calls en page |
| `FORBIDDEN_IMPORT` | ✅ | ✅ | ✅ | ✅ | ParseResult.imports |
| `BUSINESS_LOGIC_IN_POM` | ✅ | ✅ | ✅ | ✅ | ParseResult.functions body |
| `LONG_TEST_FUNCTION` | ✅ | ✅ | ✅ | ✅ | ParseResult.functions lines |
| `POOR_TEST_NAMING` | ✅ | ✅ | ✅ | ✅ | ParseResult.functions name |
| `DUPLICATE_LOCATOR` | ✅ | ✅ | ✅ | ✅ | check_project cross-file |
| `MISSING_LAYER_STRUCTURE` | ✅ | ✅ | ✅ | ✅ | check_project dirs |

### Métodos browser por lenguaje

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Browser Methods Detection Matrix                                            │
│                                                                             │
│  Python (Selenium, Playwright):                                             │
│  ├── driver.find_element(), driver.find_elements()                         │
│  ├── driver.get(), driver.navigate()                                       │
│  ├── page.locator(), page.query_selector()                                 │
│  └── page.wait_for_selector(), page.goto()                                 │
│                                                                             │
│  Java (Selenium, Playwright):                                               │
│  ├── driver.findElement(), driver.findElements()                           │
│  ├── driver.get(), driver.navigate()                                       │
│  ├── driver.switchTo(), driver.manage()                                    │
│  └── page.locator(), page.navigate()                                       │
│                                                                             │
│  JavaScript/TypeScript (Playwright, Cypress, WebdriverIO):                  │
│  ├── page.locator(), page.getByRole(), page.getByText()                   │
│  ├── page.getByTestId(), page.$(), page.$$()                              │
│  ├── cy.get(), cy.visit(), cy.request()                                   │
│  └── browser.$(), browser.$$(), $(), $$()                                 │
│                                                                             │
│  C# (Selenium, Playwright):                                                 │
│  ├── driver.FindElement(), driver.FindElements()                           │
│  ├── driver.Navigate().GoToUrl()                                           │
│  ├── driver.SwitchTo(), driver.Manage()                                    │
│  └── page.Locator(), page.GetByRole()                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Ejemplos por Lenguaje

### Ejemplo Java

`examples/java_project/`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ java_project/                                                               │
│ ├── src/test/java/com/example/tests/                                       │
│ │   └── LoginTest.java                                                     │
│ └── src/main/java/com/example/pages/                                       │
│     └── LoginPage.java                                                     │
│                                                                             │
│  LoginTest.java:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  @Test                                                                │ │
│  │  public void test1() {              ← POOR_TEST_NAMING               │ │
│  │      driver.get("https://...");     ← HARDCODED_TEST_DATA            │ │
│  │      driver.findElement(By.id("u")) ← ADAPTATION_IN_DEFINITION       │ │
│  │          .sendKeys("admin@...");    ← HARDCODED_TEST_DATA            │ │
│  │  }                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  LoginPage.java:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  import org.junit.Assert;           ← FORBIDDEN_IMPORT               │ │
│  │                                                                       │ │
│  │  public void login(String user) {                                    │ │
│  │      Assert.assertNotNull(user);    ← ASSERTION_IN_POM               │ │
│  │      if (user.isEmpty()) { ... }    ← BUSINESS_LOGIC_IN_POM          │ │
│  │  }                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ejemplo JavaScript/TypeScript

`examples/js_project/`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ js_project/                                                                 │
│ ├── tests/                                                                  │
│ │   └── login.spec.ts                                                      │
│ └── pages/                                                                  │
│     └── LoginPage.ts                                                       │
│                                                                             │
│  login.spec.ts:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  test('test1', async ({ page }) => { ← POOR_TEST_NAMING              │ │
│  │      await page.goto('https://...'); ← HARDCODED_TEST_DATA           │ │
│  │      await page.locator('#user')     ← ADAPTATION_IN_DEFINITION      │ │
│  │          .fill('admin@test.com');    ← HARDCODED_TEST_DATA           │ │
│  │  });                                                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  LoginPage.ts:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  import { expect } from '@playwright/test'; ← FORBIDDEN_IMPORT       │ │
│  │                                                                       │ │
│  │  async login(user: string) {                                         │ │
│  │      expect(user).toBeTruthy();     ← ASSERTION_IN_POM               │ │
│  │      if (!user) { throw ... }       ← BUSINESS_LOGIC_IN_POM          │ │
│  │  }                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ejemplo C#

`examples/csharp_project/`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ csharp_project/                                                             │
│ ├── Tests/                                                                  │
│ │   └── LoginTests.cs                                                      │
│ └── Pages/                                                                  │
│     └── LoginPage.cs                                                       │
│                                                                             │
│  LoginTests.cs:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  [Test]                                                               │ │
│  │  public void Test1() {              ← POOR_TEST_NAMING               │ │
│  │      driver.Navigate().GoToUrl("https://..."); ← HARDCODED           │ │
│  │      driver.FindElement(By.Id("u")) ← ADAPTATION_IN_DEFINITION       │ │
│  │          .SendKeys("admin@...");    ← HARDCODED_TEST_DATA            │ │
│  │  }                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  LoginPage.cs:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  using NUnit.Framework;             ← FORBIDDEN_IMPORT               │ │
│  │                                                                       │ │
│  │  public void Login(string user) {                                    │ │
│  │      Assert.IsNotNull(user);        ← ASSERTION_IN_POM               │ │
│  │      if (string.IsNullOrEmpty(user)) { ... } ← BUSINESS_LOGIC        │ │
│  │  }                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Mapa de Tests

### Tests nuevos (Fase 9)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_treesitter_base.py                                         │
│                                                                             │
│  TestParseResult:                                                           │
│  ├── test_parse_result_dataclass                                           │
│  ├── test_parsed_import                                                    │
│  ├── test_parsed_function                                                  │
│  ├── test_parsed_class                                                     │
│  ├── test_parsed_call                                                      │
│  └── test_parsed_string                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_python_parser.py                                           │
│                                                                             │
│  TestPythonParser:                                                          │
│  ├── test_parse_imports                                                    │
│  ├── test_parse_classes                                                    │
│  ├── test_parse_functions                                                  │
│  ├── test_parse_calls                                                      │
│  ├── test_parse_strings                                                    │
│  ├── test_is_page_object_heuristic                                         │
│  └── test_function_decorators                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_java_parser.py                                             │
│                                                                             │
│  TestJavaParser:                                                            │
│  ├── test_parse_imports                                                    │
│  ├── test_parse_classes                                                    │
│  ├── test_parse_methods                                                    │
│  ├── test_parse_method_invocations                                         │
│  ├── test_parse_strings                                                    │
│  ├── test_detect_test_annotation                                           │
│  └── test_is_page_object_class                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_js_parser.py                                               │
│                                                                             │
│  TestJSParser:                                                              │
│  ├── test_parse_imports_es6                                                │
│  ├── test_parse_imports_commonjs                                           │
│  ├── test_parse_classes                                                    │
│  ├── test_parse_arrow_functions                                            │
│  ├── test_parse_call_expressions                                           │
│  ├── test_parse_strings                                                    │
│  ├── test_detect_test_wrappers                                             │
│  └── test_typescript_types_ignored                                         │
│                                                                             │
│  TestTSParser:                                                              │
│  ├── test_parse_typescript_file                                            │
│  └── test_parse_tsx_file                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_csharp_parser.py                                           │
│                                                                             │
│  TestCSharpParser:                                                          │
│  ├── test_parse_using_directives                                           │
│  ├── test_parse_classes                                                    │
│  ├── test_parse_methods                                                    │
│  ├── test_parse_invocations                                                │
│  ├── test_parse_strings                                                    │
│  ├── test_detect_test_attributes                                           │
│  └── test_is_page_object_class                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_definition_checker_multilang.py                            │
│                                                                             │
│  TestDefinitionCheckerJava:                                                 │
│  ├── test_detect_browser_call_in_test_java                                 │
│  ├── test_no_violation_in_page_object_java                                 │
│  └── test_detect_multiple_browser_calls_java                               │
│                                                                             │
│  TestDefinitionCheckerJS:                                                   │
│  ├── test_detect_locator_in_test_js                                        │
│  ├── test_detect_cy_get_in_test                                            │
│  └── test_no_violation_in_page_class_js                                    │
│                                                                             │
│  TestDefinitionCheckerCSharp:                                               │
│  ├── test_detect_find_element_in_test_csharp                               │
│  └── test_no_violation_in_page_object_csharp                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ tests/unit/test_quality_checker_multilang.py                               │
│                                                                             │
│  TestHardcodedDataJava:                                                     │
│  ├── test_detect_email_in_java_test                                        │
│  └── test_detect_url_in_java_test                                          │
│                                                                             │
│  TestHardcodedDataJS:                                                       │
│  ├── test_detect_email_in_js_test                                          │
│  └── test_detect_url_in_ts_test                                            │
│                                                                             │
│  TestPoorNamingMultilang:                                                   │
│  ├── test_detect_test1_java                                                │
│  ├── test_detect_test_js                                                   │
│  └── test_detect_Test1_csharp                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Totales estimados

| Categoría | Fase 8 | Fase 9 | Delta |
|-----------|--------|--------|-------|
| Tests parsers | 15 | ~45 | +30 |
| Tests checkers multilang | 0 | ~25 | +25 |
| Tests integración | 47 | ~55 | +8 |
| **Total** | **317** | **~380** | **+63** |

---

## 11. Decisiones Arquitectónicas

Las decisiones técnicas de la Fase 9 están documentadas en [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md):

| ADR | Título | Decisión |
|-----|--------|----------|
| 33 | tree-sitter-language-pack vs parsers separados | Usar language-pack unificado para Java/JS/TS |
| 34 | Checkers language-agnostic vs per-language | **Language-agnostic** con patrones por extensión |
| 35 | ParseResult como interfaz unificada | Abstracción que desacopla parsers de checkers |
| 36 | Factory function para selección de parser | `get_parser_for_file()` centralizado |

### Principios aplicados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Principios SOLID en Fase 9                                                  │
│                                                                             │
│  S — Single Responsibility:                                                 │
│      Cada parser solo parsea su lenguaje, cada checker solo detecta        │
│      un tipo de violación                                                   │
│                                                                             │
│  O — Open/Closed:                                                           │
│      Añadir nuevo lenguaje = nuevo parser + entradas en diccionarios       │
│      No requiere modificar checkers existentes                             │
│                                                                             │
│  L — Liskov Substitution:                                                   │
│      Todos los parsers producen ParseResult, intercambiables               │
│                                                                             │
│  I — Interface Segregation:                                                 │
│      ParseResult es interfaz mínima necesaria para checkers                │
│                                                                             │
│  D — Dependency Inversion:                                                  │
│      Checkers dependen de ParseResult (abstracción), no de parsers         │
│      concretos (implementaciones)                                          │
│                                                                             │
│  DRY — Don't Repeat Yourself:                                               │
│      Mismos algoritmos de detección para todos los lenguajes               │
│      Solo patrones específicos en diccionarios                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Última actualización: 4 de febrero de 2026*
