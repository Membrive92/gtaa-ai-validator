# Fase 7 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Fase 7](#1-visión-general-de-la-fase-7)
2. [FileClassifier: Clasificación de Archivos](#2-fileclassifier-clasificación-de-archivos)
3. [ClassificationResult y Detección de Frameworks](#3-classificationresult-y-detección-de-frameworks)
4. [ProjectConfig y .gtaa.yaml](#4-projectconfig-y-gtaayaml)
5. [Integración en StaticAnalyzer](#5-integración-en-staticanalyzer)
6. [Integración en el Análisis Semántico (LLM)](#6-integración-en-el-análisis-semántico-llm)
7. [Auto-wait de Playwright](#7-auto-wait-de-playwright)
8. [CLI: Opción --config](#8-cli-opción---config)
9. [Mapa de Violaciones Actualizado](#9-mapa-de-violaciones-actualizado)
10. [Mapa de Tests](#10-mapa-de-tests)
11. [Decisiones Arquitectónicas](#11-decisiones-arquitectónicas)

---

## 1. Visión General de la Fase 7

La Fase 7 reduce falsos positivos en proyectos mixtos (API + UI testing) mediante clasificación a nivel de archivo y configuración por proyecto. También detecta automáticamente frameworks con auto-wait (Playwright) para evitar falsos `MISSING_WAIT_STRATEGY`.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Fase 7: Proyectos Mixtos                     │
│                                                                     │
│  Problema:                                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Proyecto con tests API + UI genera falsos positivos:          │  │
│  │                                                               │  │
│  │  test_api_users.py:  import requests                          │  │
│  │    → ADAPTATION_IN_DEFINITION  ← FALSO POSITIVO (no usa POM) │  │
│  │    → MISSING_WAIT_STRATEGY     ← FALSO POSITIVO (no hay UI)  │  │
│  │                                                               │  │
│  │  test_login.py:  from playwright... import Page               │  │
│  │    → MISSING_WAIT_STRATEGY     ← FALSO POSITIVO (auto-wait)  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Solución:                                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 1. FileClassifier    — clasifica cada archivo (api/ui/unknown)│  │
│  │ 2. ProjectConfig     — .gtaa.yaml para exclusiones custom     │  │
│  │ 3. Auto-wait detect  — Playwright salta MISSING_WAIT_STRATEGY │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Nuevos módulos:                                                    │
│  ├── file_classifier.py     — FileClassifier + ClassificationResult│
│  ├── config.py              — ProjectConfig + load_config()        │
│  │                                                                  │
│  Módulos modificados:                                               │
│  ├── checkers/base.py       — file_type en check()                 │
│  ├── checkers/definition_checker.py — skip si file_type="api"      │
│  ├── analyzers/static_analyzer.py   — integra classifier + config  │
│  ├── analyzers/semantic_analyzer.py — pasa has_auto_wait al LLM   │
│  ├── llm/client.py          — has_auto_wait en analyze_file()      │
│  ├── llm/gemini_client.py   — has_auto_wait en prompt              │
│  ├── llm/prompts.py         — contexto auto-wait en prompt         │
│  ├── __main__.py            — --config flag                        │
│  ├── setup.py               — PyYAML dependency                    │
│  └── requirements.txt       — PyYAML dependency                    │
│                                                                     │
│  Tests: 234 → 274 (+40)                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. FileClassifier: Clasificación de Archivos

`file_classifier.py:41-115`

El clasificador analiza cada archivo individualmente (no a nivel de proyecto) usando tres señales con puntuación ponderada.

### Estrategia de scoring

```
┌──────────────────────────────────────────────────────────────────┐
│ FileClassifier.classify_detailed(file_path, source, tree)        │
│                                                                  │
│ SEÑAL 1: Imports (AST) — peso 5 por import                      │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ API_IMPORTS = {requests, httpx, aiohttp, urllib,             │ │
│ │               fastapi, starlette, flask, rest_framework}     │ │
│ │                                                              │ │
│ │ UI_IMPORTS = {selenium, playwright, webdriver}                │ │
│ │                                                              │ │
│ │ Análisis via AST (ast.Import + ast.ImportFrom):              │ │
│ │   import requests         → api_score += 5                   │ │
│ │   from selenium import... → ui_score += 5                    │ │
│ │   from playwright.sync... → ui_score += 5                    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ SEÑAL 2: Patrones de código (Regex) — peso 2 por match          │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ response\.status_code    → api_score += 2                    │ │
│ │ \.json\(\)               → api_score += 2                    │ │
│ │ \.(get|post|put|...)     → api_score += 2                    │ │
│ │ status_code\s*==\s*\d{3} → api_score += 2                    │ │
│ │ application/json         → api_score += 2                    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ SEÑAL 3: Patrones de ruta — peso 3 por match                    │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ "/api/"       en ruta → api_score += 3                       │ │
│ │ "test_api_"   en ruta → api_score += 3                       │ │
│ │ "_api_test"   en ruta → api_score += 3                       │ │
│ │ "/api_"       en ruta → api_score += 3                       │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ DECISIÓN CONSERVADORA:                                           │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ if ui_score > 0:                                             │ │
│ │     return "ui"          ← UI siempre gana (conservador)     │ │
│ │ elif api_score > 0:                                          │ │
│ │     return "api"         ← Solo si NO hay señales UI         │ │
│ │ else:                                                        │ │
│ │     return "unknown"     ← Se trata como UI (no pierde nada) │ │
│ └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### ¿Por qué AST para imports y no regex?

```
Regex en source:
    "# import requests"        ← Falso positivo (comentario)
    "'import requests'"        ← Falso positivo (string)
    "some_requests_module"     ← Falso positivo (substring)

AST (preciso):
    ast.Import(names=[alias(name='requests')])
    ast.ImportFrom(module='requests', ...)
    → Solo imports reales, sin falsos positivos
```

### ¿Por qué UI siempre gana?

```
Archivo mixto:
    import requests              ← señal API
    from selenium import webdriver  ← señal UI

Si clasificamos como "api" → saltamos ADAPTATION_IN_DEFINITION
  → Pero el archivo USA Selenium → perdemos violaciones reales

Si clasificamos como "ui" → analizamos todo
  → Puede generar algún falso positivo menor
  → Pero NO perdemos violaciones reales

Principio: es mejor un falso positivo que un falso negativo
```

---

## 3. ClassificationResult y Detección de Frameworks

`file_classifier.py:25-38`

```
┌─────────────────────────────────────────────────────────────────┐
│ AUTO_WAIT_FRAMEWORKS = {"playwright"}                            │
│                                                                  │
│ @dataclass                                                       │
│ ClassificationResult:                                            │
│ ├── file_type: str           # "api", "ui", "unknown"           │
│ ├── frameworks: Set[str]     # {"playwright"}, {"selenium"}, {} │
│ │                                                                │
│ └── @property                                                    │
│     has_auto_wait: bool                                          │
│     return frameworks ∩ AUTO_WAIT_FRAMEWORKS ≠ ∅                │
│                                                                  │
│ Ejemplos:                                                        │
│ ┌───────────────────────────┬──────────┬──────────┬───────────┐ │
│ │ Archivo                   │ file_type│frameworks│auto_wait  │ │
│ ├───────────────────────────┼──────────┼──────────┼───────────┤ │
│ │ from playwright... Page   │ ui       │{playwright}│ True    │ │
│ │ from selenium... webdriver│ ui       │{selenium}  │ False   │ │
│ │ import requests           │ api      │ {}         │ False   │ │
│ │ import os                 │ unknown  │ {}         │ False   │ │
│ │ playwright + selenium     │ ui       │{playwright,│ True    │ │
│ │                           │          │ selenium}  │         │ │
│ └───────────────────────────┴──────────┴──────────┴───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Relación classify() vs classify_detailed()

```
classify()                          classify_detailed()
    │                                   │
    │  Backward compatible              │  Información completa
    │  Devuelve solo str                │  Devuelve ClassificationResult
    │                                   │
    │  Usado por:                       │  Usado por:
    │  └── tests existentes             │  ├── StaticAnalyzer
    │                                   │  └── SemanticAnalyzer
    │                                   │
    └──── Internamente llama a ─────────┘
          classify_detailed().file_type
```

---

## 4. ProjectConfig y .gtaa.yaml

`config.py`

### Estructura de configuración

```
┌──────────────────────────────────────────────────────────────────┐
│ @dataclass                                                        │
│ ProjectConfig:                                                    │
│ ├── exclude_checks: List[str]    # Violaciones a ignorar         │
│ │   Ej: ["MISSING_WAIT_STRATEGY"]                                │
│ │                                                                 │
│ ├── ignore_paths: List[str]      # Globs de archivos a excluir   │
│ │   Ej: ["tests/legacy/**"]                                      │
│ │                                                                 │
│ └── api_test_patterns: List[str] # Patrones extra para API tests │
│     Ej: ["**/test_api_*.py"]                                     │
└──────────────────────────────────────────────────────────────────┘
```

### Flujo de carga

```
load_config(project_path)
    │
    ▼
┌──────────────────────────────────┐
│ ¿Existe .gtaa.yaml en project/? │
├──── No ──────────────────────────┤
│   return ProjectConfig()         │  ← Defaults vacíos
│   (exclude_checks=[], ...)       │
├──── Sí ──────────────────────────┤
│   ▼                              │
│ yaml.safe_load(contenido)        │
│   │                              │
│   ├── ¿Resultado es None?        │
│   │   └── return ProjectConfig() │  ← YAML vacío
│   │                              │
│   ├── ¿No es dict?               │
│   │   └── return ProjectConfig() │  ← YAML con lista u otro tipo
│   │                              │
│   ├── ¿yaml.YAMLError?           │
│   │   └── return ProjectConfig() │  ← YAML malformado
│   │                              │
│   └── Parsear campos:            │
│       exclude_checks = data.get("exclude_checks") or []
│       ignore_paths   = data.get("ignore_paths") or []
│       api_test_patterns = data.get("api_test_patterns") or []
│       return ProjectConfig(...)  │
└──────────────────────────────────┘

Principio: degradación elegante. Nunca falla, siempre devuelve
un config válido. El análisis funciona sin .gtaa.yaml.
```

### Ejemplo de .gtaa.yaml

```yaml
# .gtaa.yaml — Configuración del proyecto analizado
# Ubicación: raíz del proyecto analizado (NO del analizador)

exclude_checks:
  - MISSING_WAIT_STRATEGY    # Framework custom con auto-waits

ignore_paths:
  - "tests/legacy/**"        # Tests legacy que no siguen gTAA

api_test_patterns:
  - "**/test_api_*.py"       # Patrón adicional para tests API
  - "**/api/**"              # Directorio completo
```

### ¿Por qué .gtaa.yaml y no .env?

```
.env:                               .gtaa.yaml:
├── Secretos (API keys)             ├── Reglas del proyecto
├── NO se commitea                  ├── SÍ se commitea
├── Por desarrollador               ├── Compartido por equipo
└── Variables de entorno             └── Configuración semántica

.env es para GEMINI_API_KEY (secreto personal)
.gtaa.yaml es para exclusiones de reglas (decisión de equipo)
```

---

## 5. Integración en StaticAnalyzer

`static_analyzer.py`

### Cambios en __init__()

```
StaticAnalyzer.__init__(project_path, verbose=False, config=None)
    │
    ├── self.config = config or load_config(project_path)
    │     └── Carga .gtaa.yaml si existe, sino defaults
    │
    └── self.classifier = FileClassifier()
          └── Instancia para clasificar archivos
```

### Cambios en _check_file()

```
_check_file(file_path)
    │
    ▼
┌───────────────────────────────────────────────────┐
│ 1. Parsear AST (una sola vez por archivo)         │
│                                                   │
│ 2. Clasificar archivo:                            │
│    classification = classifier.classify_detailed( │
│        file_path, source_code, tree               │
│    )                                              │
│    file_type = classification.file_type           │
│                                                   │
│ 3. Si verbose: imprimir clasificación + frameworks│
│    "[Clasificación] test_login.py → ui            │
│     (frameworks: playwright)"                     │
│                                                   │
│ 4. Pasar file_type a cada checker:                │
│    checker.check(file_path, tree, file_type=...)  │
│                                                   │
│ DefinitionChecker:                                │
│   file_type == "api" → return []                  │
│   file_type == "ui"  → análisis normal            │
│   file_type == "unknown" → análisis normal        │
│                                                   │
│ Otros checkers:                                   │
│   Reciben file_type pero no lo usan (aún)         │
└───────────────────────────────────────────────────┘
```

### Cambios en _discover_python_files()

```
_discover_python_files()
    │
    ▼
┌───────────────────────────────────────────────────┐
│ Para cada .py en project_path.rglob("*.py"):      │
│                                                   │
│ 1. ¿En directorio excluido?                       │
│    (venv, .git, __pycache__, etc.)                │
│    └── Sí → skip                                  │
│                                                   │
│ 2. ¿Matches config.ignore_paths?        ← NUEVO  │
│    fnmatch(relative_path, pattern)                │
│    Ej: "tests/legacy/**" excluye legacy tests     │
│    └── Sí → skip                                  │
│                                                   │
│ 3. Añadir a lista de archivos                     │
└───────────────────────────────────────────────────┘
```

---

## 6. Integración en el Análisis Semántico (LLM)

### SemanticAnalyzer

`semantic_analyzer.py`

```
SemanticAnalyzer.analyze(report)
    │
    ▼
┌───────────────────────────────────────────────────────┐
│ Para cada archivo Python:                              │
│                                                        │
│ 1. Clasificar con classify_detailed()                  │
│    classification = classifier.classify_detailed(...)   │
│    file_type = classification.file_type                │
│    has_auto_wait = classification.has_auto_wait        │
│                                                        │
│ 2. Pasar ambos al cliente LLM:                         │
│    llm_client.analyze_file(                            │
│        content, file_str,                              │
│        file_type=file_type,                            │
│        has_auto_wait=has_auto_wait    ← NUEVO          │
│    )                                                   │
└───────────────────────────────────────────────────────┘
```

### MockLLMClient

`client.py:20-45`

```
MockLLMClient.analyze_file(content, path, file_type, has_auto_wait)
    │
    ├── ¿Es archivo de test?
    │   ├── _check_unclear_test_purpose()
    │   ├── _check_implicit_test_dependency()
    │   └── _check_missing_aaa_structure()
    │
    └── ¿Es Page Object?
        ├── _check_page_object_too_much()
        ├── ¿file_type != "api" AND NOT has_auto_wait?   ← FASE 7
        │   ├── Sí → _check_missing_wait_strategy()
        │   └── No → skip (API o Playwright)
        └── _check_mixed_abstraction_level()

Antes (Fase 6):
    if file_type != "api":
        _check_missing_wait_strategy()

Después (Fase 7):
    if file_type != "api" and not has_auto_wait:
        _check_missing_wait_strategy()
```

### GeminiLLMClient + Prompts

`gemini_client.py` / `prompts.py`

```
GeminiLLMClient.analyze_file(content, path, file_type, has_auto_wait)
    │
    ▼
┌───────────────────────────────────────────────────────┐
│ prompt = ANALYZE_FILE_PROMPT.format(                   │
│     file_path=file_path,                               │
│     file_content=file_content,                         │
│     file_type=file_type,                               │
│     has_auto_wait="sí" if has_auto_wait else "no",     │
│ )                                                      │
└───────────────────────────────────────────────────────┘

ANALYZE_FILE_PROMPT (extracto):
┌───────────────────────────────────────────────────────┐
│ **Clasificación del archivo**: {file_type}             │
│ **Auto-wait del framework**: {has_auto_wait}           │
│                                                        │
│ **IMPORTANTE**:                                        │
│ - Si "api" → NO reportes MISSING_WAIT_STRATEGY         │
│ - Si auto-wait = sí → NO reportes MISSING_WAIT_STRATEGY│
└───────────────────────────────────────────────────────┘
```

---

## 7. Auto-wait de Playwright

### Problema

```
Playwright tiene auto-wait nativo:
    page.click("#submit")
    │
    └── Internamente, Playwright espera:
        1. Elemento visible
        2. Elemento estable (no animando)
        3. Elemento habilitado
        4. Elemento no obstruido
        → NO necesita wait explícito

Selenium NO tiene auto-wait:
    driver.find_element(By.ID, "submit").click()
    │
    └── Si el elemento no existe → NoSuchElementException
        → Necesita WebDriverWait explícito
```

### Solución: detección automática

```
┌─────────────────────────────────────────────────────────┐
│ AUTO_WAIT_FRAMEWORKS = {"playwright"}                    │
│                                                         │
│ FileClassifier detecta framework via imports (AST):     │
│                                                         │
│   from playwright.sync_api import Page                  │
│   → ui_imports = {"playwright"}                         │
│   → ClassificationResult.frameworks = {"playwright"}    │
│   → has_auto_wait = True                                │
│                                                         │
│   from selenium import webdriver                        │
│   → ui_imports = {"selenium"}                           │
│   → ClassificationResult.frameworks = {"selenium"}      │
│   → has_auto_wait = False                               │
│                                                         │
│ Resultado:                                              │
│   Playwright → MISSING_WAIT_STRATEGY se salta           │
│   Selenium   → MISSING_WAIT_STRATEGY se aplica          │
│   API test   → MISSING_WAIT_STRATEGY se salta           │
│                                                         │
│ Sin necesidad de .gtaa.yaml para este caso.             │
│ .gtaa.yaml se reserva para frameworks custom.           │
└─────────────────────────────────────────────────────────┘
```

### ¿Por qué automático y no solo YAML?

```
Automático (Playwright):
  → Es un hecho del framework, no una decisión del equipo
  → Siempre correcto, sin configuración

YAML (frameworks custom):
  → Cada framework custom es diferente
  → El equipo decide qué excluir
  → No se puede inferir automáticamente

Ambos coexisten:
  1. Primero: detección automática de frameworks conocidos
  2. Segundo: .gtaa.yaml para casos atípicos
```

---

## 8. CLI: Opción --config

`__main__.py`

```
@click.option('--config', type=click.Path(exists=True), default=None,
              help='Ruta al archivo de configuración .gtaa.yaml')

Flujo:
    python -m gtaa_validator /path/project --config /path/.gtaa.yaml
        │
        ▼
    Si --config proporcionado:
        config = load_config(Path(config_path).parent)
    Sino:
        config = load_config(project_path)  ← busca .gtaa.yaml en proyecto

    StaticAnalyzer(project_path, config=config)
```

---

## 9. Mapa de Violaciones Actualizado

### Violaciones filtradas por file_type

```
┌──────────────────────────────────┬───────┬──────┬─────────┐
│ Violación                        │ API   │ UI   │ Unknown │
├──────────────────────────────────┼───────┼──────┼─────────┤
│ ADAPTATION_IN_DEFINITION         │ SKIP  │ ✓    │ ✓       │
│ MISSING_WAIT_STRATEGY            │ SKIP  │ ✓*   │ ✓       │
│                                  │       │      │         │
│ MISSING_LAYER_STRUCTURE          │ ✓     │ ✓    │ ✓       │
│ HARDCODED_TEST_DATA              │ ✓     │ ✓    │ ✓       │
│ ASSERTION_IN_POM                 │ ✓     │ ✓    │ ✓       │
│ FORBIDDEN_IMPORT                 │ ✓     │ ✓    │ ✓       │
│ BUSINESS_LOGIC_IN_POM            │ ✓     │ ✓    │ ✓       │
│ DUPLICATE_LOCATOR                │ ✓     │ ✓    │ ✓       │
│ LONG_TEST_FUNCTION               │ ✓     │ ✓    │ ✓       │
│ POOR_TEST_NAMING                 │ ✓     │ ✓    │ ✓       │
│ BROAD_EXCEPTION_HANDLING         │ ✓     │ ✓    │ ✓       │
│ HARDCODED_CONFIGURATION          │ ✓     │ ✓    │ ✓       │
│ SHARED_MUTABLE_STATE             │ ✓     │ ✓    │ ✓       │
│ UNCLEAR_TEST_PURPOSE             │ ✓     │ ✓    │ ✓       │
│ PAGE_OBJECT_DOES_TOO_MUCH        │ ✓     │ ✓    │ ✓       │
│ IMPLICIT_TEST_DEPENDENCY         │ ✓     │ ✓    │ ✓       │
│ MISSING_AAA_STRUCTURE            │ ✓     │ ✓    │ ✓       │
│ MIXED_ABSTRACTION_LEVEL          │ ✓     │ ✓    │ ✓       │
└──────────────────────────────────┴───────┴──────┴─────────┘

* MISSING_WAIT_STRATEGY se salta también si has_auto_wait=True
  (Playwright detectado), independientemente del file_type.

SKIP = la violación no se ejecuta para ese tipo de archivo
✓    = la violación se ejecuta normalmente
```

### Dónde se filtra cada violación

```
ADAPTATION_IN_DEFINITION:
  └── DefinitionChecker.check(): if file_type == "api": return []
      (Capa estática)

MISSING_WAIT_STRATEGY:
  ├── MockLLMClient: if file_type != "api" and not has_auto_wait
  ├── GeminiLLMClient: instrucción en el prompt
  └── (Capa semántica — LLM)
```

---

## 10. Mapa de Tests

### Tests nuevos — FileClassifier (23 tests)

```
tests/unit/test_classifier.py

TestAPIDetection (7 tests):
├── test_requests_import            ← import requests → "api"
├── test_httpx_import               ← import httpx → "api"
├── test_aiohttp_import             ← import aiohttp → "api"
├── test_from_requests_import       ← from requests import Session → "api"
├── test_fastapi_import             ← from fastapi.testclient → "api"
├── test_flask_import               ← from flask import Flask → "api"
└── test_rest_framework_import      ← from rest_framework → "api"

TestAPICodePatterns (4 tests):
├── test_status_code_pattern        ← response.status_code → "api"
├── test_json_call_pattern          ← response.json() → "api"
├── test_http_method_pattern        ← client.get('/api/...') → "api"
└── test_status_code_comparison     ← status_code == 200 → "api"

TestAPIPathPatterns (3 tests):
├── test_api_directory              ← tests/api/test_users.py → "api"
├── test_test_api_prefix            ← test_api_users.py → "api"
└── test_api_test_suffix            ← users_api_test.py → "api"

TestUIDetection (2 tests):
├── test_selenium_import            ← from selenium → "ui"
└── test_playwright_import          ← from playwright → "ui"

TestMixedDetection (2 tests):
├── test_mixed_imports_ui_wins      ← requests + selenium → "ui"
└── test_api_patterns_plus_ui_import ← selenium + status_code → "ui"

TestUnknownDetection (2 tests):
├── test_no_signals                 ← def test_something → "unknown"
└── test_unrelated_imports          ← import os, json → "unknown"

TestClassifyDetailed (6 tests):                           ← FASE 7 auto-wait
├── test_playwright_detected_as_framework  ← frameworks={"playwright"}
├── test_playwright_has_auto_wait          ← has_auto_wait=True
├── test_selenium_no_auto_wait             ← has_auto_wait=False
├── test_api_no_auto_wait                  ← has_auto_wait=False
├── test_unknown_no_auto_wait              ← has_auto_wait=False
└── test_mixed_playwright_and_selenium     ← has_auto_wait=True
```

### Tests nuevos — ProjectConfig (8 tests)

```
tests/unit/test_config.py

TestProjectConfigDefaults (3 tests):
├── test_default_exclude_checks     ← exclude_checks == []
├── test_default_ignore_paths       ← ignore_paths == []
└── test_default_api_test_patterns  ← api_test_patterns == []

TestLoadConfig (5 tests):
├── test_no_config_file_returns_defaults  ← sin .gtaa.yaml → defaults
├── test_valid_config_file                ← YAML completo → carga OK
├── test_empty_yaml_returns_defaults      ← YAML vacío → defaults
├── test_invalid_yaml_returns_defaults    ← YAML malformado → defaults
├── test_yaml_with_null_values            ← campos null → listas vacías
├── test_yaml_not_dict_returns_defaults   ← YAML con lista → defaults
└── test_partial_config                   ← solo exclude_checks → resto defaults
```

### Tests modificados — DefinitionChecker (+4 tests)

```
tests/unit/test_definition_checker.py

TestFileTypeFiltering (4 tests):                          ← NUEVO
├── test_api_file_returns_empty          ← file_type="api" → []
├── test_ui_file_returns_violations      ← file_type="ui" → violaciones
├── test_unknown_file_returns_violations ← file_type="unknown" → violaciones
└── test_default_file_type_returns_violations ← sin file_type → violaciones
```

### Resumen de tests

```
┌──────────────────────────────────────┬──────┬──────┐
│ Módulo                               │ F6   │ F7   │
├──────────────────────────────────────┼──────┼──────┤
│ tests/unit/test_classifier           │ -    │ +23  │
│ tests/unit/test_config               │ -    │ +8   │
│ tests/unit/test_definition_checker   │ -    │ +4   │
│ (otros tests existentes sin cambios) │      │ +5*  │
├──────────────────────────────────────┼──────┼──────┤
│ Total nuevos                         │      │ +40  │
│ Total proyecto                       │ 234  │ 274  │
└──────────────────────────────────────┴──────┴──────┘

* Tests existentes que pasan sin modificación gracias
  a backward compatibility (file_type="unknown" por defecto)
```

---

## 11. Decisiones Arquitectónicas

### ADR-22: Clasificación a nivel de archivo vs proyecto

**Decisión**: Clasificar cada archivo individualmente, no el proyecto completo.

**Alternativas evaluadas:**
- A) Clasificar el proyecto como "API" o "UI" globalmente
- B) Clasificar cada archivo individualmente ← **Elegida**

**Justificación**: Un proyecto real puede tener `tests/api/` con tests de API y `tests/ui/` con tests de UI. Clasificar el proyecto entero como "API" perdería violaciones UI. La clasificación per-file es más precisa.

### ADR-23: Scoring ponderado para clasificación

**Decisión**: Usar scoring con pesos (imports=5, code=2, path=3) en vez de reglas binarias.

**Justificación**: Un archivo puede tener solo un patrón de código `response.status_code` sin imports API. Con scoring, la señal débil (peso 2) clasifica como API. Con reglas binarias, necesitaríamos reglas complejas con OR/AND.

### ADR-24: UI siempre gana en archivos mixtos

**Decisión**: Si hay señales UI y API, clasificar como "ui".

**Justificación**: Conservador — es mejor un falso positivo (reportar una violación que no aplica) que un falso negativo (no reportar una violación real). Los tests de UI son más propensos a violaciones gTAA.

### ADR-25: Auto-wait automático vs solo YAML

**Decisión**: Detectar Playwright automáticamente, reservar YAML para frameworks custom.

**Justificación**: Playwright siempre tiene auto-wait — es un hecho del framework, no una decisión del equipo. Requerir YAML para esto sería fricción innecesaria. Los frameworks custom sí necesitan YAML porque no se pueden inferir.

### ADR-26: .gtaa.yaml vs .env para configuración

**Decisión**: Archivo YAML separado (`.gtaa.yaml`) para configuración de reglas.

**Alternativas evaluadas:**
- A) `.env` — para secretos, no se commitea
- B) `.gtaa.yaml` — configuración de equipo ← **Elegida**
- C) `pyproject.toml` [tool.gtaa] — acoplado a Python

**Justificación**: Las exclusiones de reglas son decisiones de equipo que deben commitearse y compartirse. `.env` es para secretos (API keys). `.gtaa.yaml` es semántico y autocontenido.

### ADR-27: PyYAML con degradación elegante

**Decisión**: Si `.gtaa.yaml` no existe o es inválido, usar defaults vacíos sin error.

**Justificación**: El validador debe funcionar sin configuración. `.gtaa.yaml` es opcional. Errores de configuración no deben bloquear el análisis.

---

*Última actualización: 2 de febrero de 2026*
