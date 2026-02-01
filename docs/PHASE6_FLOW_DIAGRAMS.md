# Fase 6 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Fase 6](#1-visión-general-de-la-fase-6)
2. [Nuevas Violaciones: Mapa Completo](#2-nuevas-violaciones-mapa-completo)
3. [Violaciones Estáticas Nuevas (QualityChecker)](#3-violaciones-estáticas-nuevas-qualitychecker)
4. [Violaciones Semánticas Nuevas (LLM)](#4-violaciones-semánticas-nuevas-llm)
5. [Ampliación del MockLLMClient](#5-ampliación-del-mockllmclient)
6. [Ampliación del GeminiLLMClient y Prompts](#6-ampliación-del-geminillmclient-y-prompts)
7. [Mapa Completo de 18 Violaciones](#7-mapa-completo-de-18-violaciones)
8. [Mapa de Tests](#8-mapa-de-tests)
9. [Consideraciones sobre Falsos Positivos](#9-consideraciones-sobre-falsos-positivos)

---

## 1. Visión General de la Fase 6

La Fase 6 amplía la cobertura de detección de violaciones de 13 a 18 tipos. Se añaden 5 nuevas violaciones basadas en el catálogo ISTQB CT-TAE: 3 estáticas (AST/regex) y 2 semánticas (LLM). Además, se amplían las heurísticas del MockLLMClient para las 2 nuevas violaciones semánticas.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Fase 6: Ampliación                          │
│                                                                     │
│  Fase 5 (13 violaciones)              Fase 6 (18 violaciones)      │
│  ├── 9 estáticas                      ├── 12 estáticas (+3)        │
│  └── 4 semánticas                     └── 6 semánticas (+2)        │
│                                                                     │
│  Nuevas violaciones:                                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ESTÁTICAS (QualityChecker):                                  │   │
│  │  1. BROAD_EXCEPTION_HANDLING   — AST (ExceptHandler)         │   │
│  │  2. HARDCODED_CONFIGURATION    — Regex (localhost, sleep)    │   │
│  │  3. SHARED_MUTABLE_STATE       — AST (Assign + Global)      │   │
│  │                                                              │   │
│  │ SEMÁNTICAS (LLM):                                            │   │
│  │  4. MISSING_AAA_STRUCTURE      — LLM + MockLLM heurística   │   │
│  │  5. MIXED_ABSTRACTION_LEVEL    — LLM + MockLLM heurística   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Archivos modificados:                                              │
│  ├── models.py              — 5 nuevos ViolationType               │
│  ├── quality_checker.py     — 3 nuevos métodos de detección        │
│  ├── prompts.py             — 2 nuevos tipos en ANALYZE_FILE_PROMPT│
│  ├── gemini_client.py       — VALID_TYPES ampliado (4 → 6)        │
│  ├── client.py              — 2 nuevas heurísticas en MockLLMClient│
│  └── tests/                 — 25 nuevos tests (209 → 234)         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Nuevas Violaciones: Mapa Completo

```
┌─────────────────────────────┬───────────┬────────────┬──────────────────┐
│ Violación                   │ Severidad │ Técnica    │ Catálogo CT-TAE  │
├─────────────────────────────┼───────────┼────────────┼──────────────────┤
│ BROAD_EXCEPTION_HANDLING    │ MEDIUM    │ AST        │ V-COD-004        │
│ HARDCODED_CONFIGURATION     │ HIGH      │ Regex      │ V-CAP-003        │
│ SHARED_MUTABLE_STATE        │ HIGH      │ AST        │ V-DAT-006        │
│ MISSING_AAA_STRUCTURE       │ MEDIUM    │ LLM        │ V-MAN-004        │
│ MIXED_ABSTRACTION_LEVEL     │ MEDIUM    │ LLM        │ V-CAP-004        │
└─────────────────────────────┴───────────┴────────────┴──────────────────┘
```

### Relación con capas gTAA

```
Capa de Definición (tests/):
├── BROAD_EXCEPTION_HANDLING    — try/except genérico oculta fallos
├── HARDCODED_CONFIGURATION     — URLs, sleeps, paths en código
├── SHARED_MUTABLE_STATE        — estado compartido entre tests
└── MISSING_AAA_STRUCTURE       — test sin Arrange-Act-Assert

Capa de Adaptación (pages/):
└── MIXED_ABSTRACTION_LEVEL     — selectores UI en métodos de negocio
```

---

## 3. Violaciones Estáticas Nuevas (QualityChecker)

Las tres nuevas violaciones estáticas se implementan como métodos adicionales en `QualityChecker`, siguiendo el mismo patrón de los métodos existentes.

### 3.1 BROAD_EXCEPTION_HANDLING — AST

`quality_checker.py:173-206`

Detecta `except:` (bare) y `except Exception:` que ocultan errores reales en tests.

```
_check_broad_exception_handling(file_path, tree)
    │
    ▼
┌──────────────────────────────────────────┐
│ Para cada nodo en ast.walk(tree):        │
│                                          │
│   ¿isinstance(node, ast.ExceptHandler)?  │
│   └── No → continue                     │
│                                          │
│   ¿node.type is None?    ← except:      │
│   └── Sí → VIOLACIÓN (bare except)      │
│                                          │
│   ¿node.type es ast.Name                │
│    y node.type.id == "Exception"?        │
│   └── Sí → VIOLACIÓN (except Exception) │
│                                          │
│   Cualquier otro tipo específico:        │
│   except ValueError, TypeError, etc.     │
│   └── OK, no es violación               │
└──────────────────────────────────────────┘

Ejemplo detectado:
    try:
        result = do_something()
    except Exception:        ← VIOLACIÓN
        result = None

    try:
        do_stuff()
    except:                  ← VIOLACIÓN (bare except)
        pass

No detectado (correcto):
    try:
        do_stuff()
    except ValueError:       ← OK, excepción específica
        handle_error()
```

### 3.2 HARDCODED_CONFIGURATION — Regex

`quality_checker.py:208-256`

Detecta configuración embebida directamente en el código de test.

```
_check_hardcoded_configuration(file_path, source_code)
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 3 patrones compilados como constantes de clase:  │
│                                                  │
│ LOCALHOST_PATTERN:                               │
│   https?://localhost[:\d/]                       │
│   https?://127\.0\.0\.1[:\d/]                    │
│                                                  │
│ SLEEP_PATTERN:                                   │
│   time\.sleep\s*\(\s*\d                          │
│                                                  │
│ ABSOLUTE_PATH_PATTERN:                           │
│   ["\'][A-Z]:\\    (Windows)                     │
│   ["\']/home/     (Linux)                        │
│   ["\']/usr/      (Linux)                        │
│   ["\']/tmp/      (Linux)                        │
│                                                  │
│ Para cada línea del source_code:                 │
│ ├── ¿Empieza con #? → skip (comentario)         │
│ ├── ¿Match LOCALHOST_PATTERN? → VIOLACIÓN        │
│ ├── ¿Match SLEEP_PATTERN? → VIOLACIÓN            │
│ └── ¿Match ABSOLUTE_PATH_PATTERN? → VIOLACIÓN    │
└──────────────────────────────────────────────────┘

Ejemplo detectado:
    base_url = "http://localhost:8080/api"    ← VIOLACIÓN
    time.sleep(3)                              ← VIOLACIÓN
    path = "/home/user/data/test.csv"          ← VIOLACIÓN

No detectado (correcto):
    # http://localhost:8080 is the base URL   ← Comentario, ignorado
    BASE_URL = config.get("base_url")          ← Externalizado, OK
```

### 3.3 SHARED_MUTABLE_STATE — AST

`quality_checker.py:258-319`

Detección en dos fases: variables mutables a nivel de módulo y uso de `global` en tests.

```
_check_shared_mutable_state(file_path, tree)
    │
    ▼
┌────────────────────────────────────────────────┐
│ FASE 1: Variables mutables a nivel de módulo   │
│                                                │
│ Para cada ast.Assign en ast.iter_child_nodes:  │
│ (solo hijos directos del módulo)               │
│                                                │
│   ¿target es ast.Name?                         │
│   ├── ¿MAYÚSCULAS? → skip (constante)         │
│   ├── ¿Empieza con _? → skip (privada)        │
│   └── ¿Valor es mutable?                      │
│       ├── ast.List   []                        │
│       ├── ast.Dict   {}                        │
│       ├── ast.Set    set()                     │
│       └── ast.Call con func in (list,dict,set) │
│           └── Sí → VIOLACIÓN                   │
│                                                │
│ FASE 2: Keyword `global` en funciones de test  │
│                                                │
│ Para cada ast.FunctionDef con test_* :         │
│   Para cada ast.Global en el cuerpo:           │
│     Para cada nombre en global.names:          │
│       → VIOLACIÓN                              │
└────────────────────────────────────────────────┘

Ejemplo detectado:
    shared_data = []           ← VIOLACIÓN (módulo-level mutable)
    cache = {}                 ← VIOLACIÓN (módulo-level mutable)

    def test_increment():
        global counter         ← VIOLACIÓN (global en test)
        counter += 1

No detectado (correcto):
    DEFAULTS = []              ← OK (MAYÚSCULAS = constante)
    _internal = {}             ← OK (privada)
    base_url = "https://..."   ← OK (string, no mutable)
```

### Flujo integrado en QualityChecker.check()

```
QualityChecker.check(file_path, tree)
    │
    ├── _check_hardcoded_data()          ← Fase 3 (existente)
    ├── _check_long_functions()          ← Fase 3 (existente)
    ├── _check_test_naming()             ← Fase 3 (existente)
    ├── _check_broad_exception_handling() ← FASE 6 (nuevo)
    ├── _check_hardcoded_configuration()  ← FASE 6 (nuevo)
    └── _check_shared_mutable_state()     ← FASE 6 (nuevo)
```

---

## 4. Violaciones Semánticas Nuevas (LLM)

### 4.1 MISSING_AAA_STRUCTURE

Test que no sigue la estructura Arrange-Act-Assert. La LLM evalúa si el código mezcla preparación, acción y verificación sin separación clara.

```
Detección por LLM (Gemini Flash):
┌─────────────────────────────────────────────────────────┐
│ El prompt pide al modelo detectar tests donde:          │
│                                                         │
│ - No hay separación clara entre Arrange, Act y Assert   │
│ - La preparación y la verificación están entremezcladas │
│ - No se identifican las 3 fases del patrón AAA          │
│                                                         │
│ Ejemplo problemático:                                    │
│   def test_checkout():                                   │
│       page.click("#add")      ← ¿Act o Arrange?        │
│       assert page.count == 1  ← Assert mezclado        │
│       page.click("#buy")      ← Otro Act después       │
│       assert page.done        ← Otro Assert             │
│                                                         │
│ Ejemplo correcto:                                        │
│   def test_checkout():                                   │
│       # Arrange                                          │
│       page.add_item("widget")                            │
│       # Act                                              │
│       page.checkout()                                    │
│       # Assert                                           │
│       assert page.order_confirmed                        │
└─────────────────────────────────────────────────────────┘
```

### 4.2 MIXED_ABSTRACTION_LEVEL

Método de Page Object que mezcla keywords de negocio con selectores de UI directos.

```
Detección por LLM (Gemini Flash):
┌─────────────────────────────────────────────────────────┐
│ El prompt pide al modelo detectar métodos donde:        │
│                                                         │
│ - El nombre sugiere operación de negocio (login, buy)   │
│ - Pero contiene selectores XPath, CSS, By.* directos    │
│                                                         │
│ Ejemplo problemático:                                    │
│   class LoginPage:                                       │
│       def login(self, user, pwd):                        │
│           self.driver.find_element(                      │
│               By.XPATH, "//input[@name='user']"          │
│           ).send_keys(user)        ← Selector directo   │
│                                                         │
│ Ejemplo correcto:                                        │
│   class LoginPage:                                       │
│       _USERNAME = (By.XPATH, "//input[@name='user']")    │
│       def login(self, user, pwd):                        │
│           self._fill(self._USERNAME, user)               │
│           ← Selector en propiedad privada               │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Ampliación del MockLLMClient

El MockLLMClient añade 2 nuevas heurísticas deterministas para simular la detección LLM sin API.

```
MockLLMClient.analyze_file() — Fase 6
    │
    ├── ¿Es archivo de test?
    │   ├── _check_unclear_test_purpose()          ← Fase 5
    │   ├── _check_implicit_test_dependency()      ← Fase 5
    │   └── _check_missing_aaa_structure()         ← FASE 6 (nuevo)
    │
    └── ¿Es Page Object?
        ├── _check_page_object_too_much()          ← Fase 5
        ├── _check_missing_wait_strategy()         ← Fase 5
        └── _check_mixed_abstraction_level()       ← FASE 6 (nuevo)
```

### _check_missing_aaa_structure()

`client.py:230-265`

```
_check_missing_aaa_structure(tree, source)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ assert_keywords = {"assert", "assertEqual",          │
│   "assertTrue", "assertFalse", "assertIn",           │
│   "assertRaises", "assertIsNone", "assertIsNotNone", │
│   "assert_called", "assert_called_once",             │
│   "assert_called_with"}                              │
│                                                      │
│ Para cada FunctionDef con test_*:                    │
│   func_source = source[lineno:end_lineno]            │
│   has_assert = any(kw in func_source                 │
│                    for kw in assert_keywords)         │
│   └── ¿No tiene assert? → VIOLACIÓN                 │
└──────────────────────────────────────────────────────┘
```

### _check_mixed_abstraction_level()

`client.py:267-306`

```
_check_mixed_abstraction_level(tree, source)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ selector_patterns = [                                │
│   r'//[\w\[\]@=\'"]+',       # XPath                │
│   r'css=',                     # CSS selector prefix │
│   r'By\.\w+',                  # Selenium By.*       │
│   r'\[data-[\w-]+',            # data attributes     │
│   r'#[\w-]+',                  # CSS id selector     │
│ ]                                                    │
│                                                      │
│ Para cada ClassDef en el AST:                        │
│   Para cada método público (no _):                   │
│     func_source = source del método                  │
│     ¿selector_regex.search(func_source)?             │
│     └── Sí → VIOLACIÓN                              │
└──────────────────────────────────────────────────────┘
```

### enrich_violation() ampliado

`client.py:44-97` — Se añaden templates para las 2 nuevas violaciones y las 3 estáticas:

```
enrichments = {
    ...                                    ← 9 tipos existentes
    "MISSING_AAA_STRUCTURE": "...",         ← FASE 6
    "MIXED_ABSTRACTION_LEVEL": "...",       ← FASE 6
}
```

---

## 6. Ampliación del GeminiLLMClient y Prompts

### VALID_TYPES ampliado (4 → 6)

`gemini_client.py:29-36`

```
VALID_TYPES = {
    "UNCLEAR_TEST_PURPOSE",          ← Fase 5
    "PAGE_OBJECT_DOES_TOO_MUCH",     ← Fase 5
    "IMPLICIT_TEST_DEPENDENCY",      ← Fase 5
    "MISSING_WAIT_STRATEGY",         ← Fase 5
    "MISSING_AAA_STRUCTURE",         ← FASE 6 (nuevo)
    "MIXED_ABSTRACTION_LEVEL",       ← FASE 6 (nuevo)
}
```

### ANALYZE_FILE_PROMPT ampliado

`prompts.py:30-36` — El prompt ahora lista 6 tipos de violación (antes 4):

```
Busca SOLO estos tipos de violaciones:
├── UNCLEAR_TEST_PURPOSE               ← Fase 5
├── PAGE_OBJECT_DOES_TOO_MUCH          ← Fase 5
├── IMPLICIT_TEST_DEPENDENCY           ← Fase 5
├── MISSING_WAIT_STRATEGY              ← Fase 5
├── MISSING_AAA_STRUCTURE              ← FASE 6 (nuevo)
└── MIXED_ABSTRACTION_LEVEL            ← FASE 6 (nuevo)
```

### Flujo de validación doble

```
Gemini responde con JSON
    │
    ▼
_parse_violations()
    │
    ├── Filtrar por VALID_TYPES (6 tipos)     ← Primera validación
    │
    ▼
SemanticAnalyzer._convert_violation()
    │
    └── ViolationType(vtype_name)             ← Segunda validación (Enum)
```

---

## 7. Mapa Completo de 18 Violaciones

```
ESTÁTICAS (12 tipos — 4 Checkers):

  DefinitionChecker (1):
  └── ADAPTATION_IN_DEFINITION        CRITICAL    AST (BrowserAPICallVisitor)

  StructureChecker (1):
  └── MISSING_LAYER_STRUCTURE         CRITICAL    Filesystem

  AdaptationChecker (4):
  ├── ASSERTION_IN_POM                HIGH        AST (AssertionVisitor)
  ├── FORBIDDEN_IMPORT                HIGH        AST (ast.Import)
  ├── BUSINESS_LOGIC_IN_POM           MEDIUM      AST (BusinessLogicVisitor)
  └── DUPLICATE_LOCATOR               MEDIUM      Regex + Estado cross-file

  QualityChecker (6):
  ├── HARDCODED_TEST_DATA             HIGH        AST (HardcodedDataVisitor)
  ├── LONG_TEST_FUNCTION              MEDIUM      AST (FunctionDef.end_lineno)
  ├── POOR_TEST_NAMING                LOW         Regex
  ├── BROAD_EXCEPTION_HANDLING        MEDIUM      AST (ExceptHandler)        ← FASE 6
  ├── HARDCODED_CONFIGURATION         HIGH        Regex (3 patrones)         ← FASE 6
  └── SHARED_MUTABLE_STATE            HIGH        AST (Assign + Global)      ← FASE 6


SEMÁNTICAS (6 tipos — LLM):

  Fase 5 (4):
  ├── UNCLEAR_TEST_PURPOSE            MEDIUM      LLM / MockLLM
  ├── PAGE_OBJECT_DOES_TOO_MUCH       HIGH        LLM / MockLLM
  ├── IMPLICIT_TEST_DEPENDENCY        HIGH        LLM / MockLLM
  └── MISSING_WAIT_STRATEGY           MEDIUM      LLM / MockLLM

  Fase 6 (2):                                                                ← NUEVAS
  ├── MISSING_AAA_STRUCTURE           MEDIUM      LLM / MockLLM
  └── MIXED_ABSTRACTION_LEVEL         MEDIUM      LLM / MockLLM


TOTALES POR SEVERIDAD:
  CRITICAL: 2
  HIGH:     6
  MEDIUM:   8
  LOW:      1
  ─────────────
  Total:   18 (repartidos: 12 estáticas, 6 semánticas)
```

### Distribución por capa gTAA

```
┌─────────────────────────────┬────────────────────────────────────┐
│ Capa gTAA                   │ Violaciones                        │
├─────────────────────────────┼────────────────────────────────────┤
│ Definición (tests/)         │ ADAPTATION_IN_DEFINITION           │
│                             │ HARDCODED_TEST_DATA                │
│                             │ LONG_TEST_FUNCTION                 │
│                             │ POOR_TEST_NAMING                   │
│                             │ BROAD_EXCEPTION_HANDLING     (F6)  │
│                             │ HARDCODED_CONFIGURATION      (F6)  │
│                             │ SHARED_MUTABLE_STATE         (F6)  │
│                             │ UNCLEAR_TEST_PURPOSE               │
│                             │ IMPLICIT_TEST_DEPENDENCY           │
│                             │ MISSING_AAA_STRUCTURE        (F6)  │
├─────────────────────────────┼────────────────────────────────────┤
│ Adaptación (pages/)         │ ASSERTION_IN_POM                   │
│                             │ FORBIDDEN_IMPORT                   │
│                             │ BUSINESS_LOGIC_IN_POM              │
│                             │ DUPLICATE_LOCATOR                  │
│                             │ PAGE_OBJECT_DOES_TOO_MUCH          │
│                             │ MISSING_WAIT_STRATEGY              │
│                             │ MIXED_ABSTRACTION_LEVEL      (F6)  │
├─────────────────────────────┼────────────────────────────────────┤
│ Estructura (proyecto)       │ MISSING_LAYER_STRUCTURE            │
└─────────────────────────────┴────────────────────────────────────┘
```

---

## 8. Mapa de Tests

### Tests nuevos — QualityChecker (15 tests)

```
tests/unit/test_quality_checker.py

TestBroadExceptionHandling (4 tests):
├── test_bare_except_detected             ← except: → VIOLACIÓN
├── test_except_exception_detected        ← except Exception: → VIOLACIÓN
├── test_specific_except_ok               ← except ValueError: → OK
└── test_multiple_specific_except_ok      ← except (TypeError, KeyError): → OK

TestHardcodedConfiguration (5 tests):
├── test_localhost_url_detected           ← http://localhost:8080 → VIOLACIÓN
├── test_sleep_detected                   ← time.sleep(5) → VIOLACIÓN
├── test_absolute_path_detected           ← /home/user/data → VIOLACIÓN
├── test_comment_ignored                  ← # http://localhost → OK
└── test_no_config_no_violation           ← assert 2+2==4 → OK

TestSharedMutableState (6 tests):
├── test_module_level_list_detected       ← shared_data = [] → VIOLACIÓN
├── test_module_level_dict_detected       ← cache = {} → VIOLACIÓN
├── test_uppercase_constant_ok            ← DEFAULTS = [] → OK
├── test_private_var_ok                   ← _internal = {} → OK
├── test_global_keyword_in_test_detected  ← global counter → VIOLACIÓN
└── test_string_assignment_ok             ← base_url = "..." → OK
```

### Tests nuevos — MockLLMClient (7 tests)

```
tests/unit/test_llm_client.py

TestMissingAAAStructure (3 tests):
├── test_test_without_assert_detected     ← test sin assert → VIOLACIÓN
├── test_test_with_assert_ok              ← test con assert → OK
└── test_non_test_function_ignored        ← helper sin assert → OK

TestMixedAbstractionLevel (4 tests):
├── test_xpath_in_public_method_detected  ← "//input" en método público → VIOLACIÓN
├── test_by_in_public_method_detected     ← By.ID en método público → VIOLACIÓN
├── test_private_method_ok                ← "//input" en _método → OK
└── test_no_selector_ok                   ← método sin selectores → OK
```

### Tests nuevos — GeminiLLMClient (3 tests)

```
tests/unit/test_gemini_client.py

TestGeminiValidTypes (1 test):
└── test_valid_types_has_six_entries      ← VALID_TYPES tiene 6 tipos

TestGeminiClientInit (fix):
└── test_con_api_key_crea_cliente         ← model == "gemini-2.5-flash-lite"
```

### Resumen de tests

```
┌─────────────────────────────────┬──────┬──────┐
│ Módulo                          │ F5   │ F6   │
├─────────────────────────────────┼──────┼──────┤
│ tests/unit/test_quality_checker │ -    │ +15  │
│ tests/unit/test_llm_client      │ -    │ +7   │
│ tests/unit/test_gemini_client   │ -    │ +3   │
├─────────────────────────────────┼──────┼──────┤
│ Total nuevos                    │      │ +25  │
│ Total proyecto                  │ 209  │ 234  │
└─────────────────────────────────┴──────┴──────┘
```

---

## 9. Consideraciones sobre Falsos Positivos

### Frameworks con auto-wait (Playwright)

Playwright implementa auto-wait en todas las acciones de UI. La violación `MISSING_WAIT_STRATEGY` puede generar falsos positivos en proyectos Playwright, ya que no requiere waits explícitos antes de `click()` o `fill()`.

```
Selenium (requiere wait explícito):
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(locator)
    )
    driver.click()            ← OK, wait previo

Playwright (auto-wait integrado):
    page.click("#submit")     ← Falso positivo: Playwright ya espera
```

### API Testing

En proyectos con capa de tests de API, algunas violaciones pueden no aplicar:

```
┌──────────────────────────────┬──────────────────────────────────┐
│ Violación                    │ Riesgo de falso positivo en API  │
├──────────────────────────────┼──────────────────────────────────┤
│ HARDCODED_CONFIGURATION      │ ALTO — URLs base son legítimas   │
│                              │ en fixtures/conftest             │
│ MISSING_WAIT_STRATEGY        │ MEDIO — API calls no necesitan   │
│                              │ waits (son síncronos)            │
│ ADAPTATION_IN_DEFINITION     │ MEDIO — page.request.get() se    │
│                              │ detectaría como Playwright API   │
│ Resto de violaciones         │ BAJO — aplican igual a API tests │
└──────────────────────────────┴──────────────────────────────────┘
```

### Mitigaciones actuales

- `HARDCODED_CONFIGURATION` ignora comentarios (`#`)
- `SHARED_MUTABLE_STATE` ignora constantes (`MAYÚSCULAS`) y privadas (`_var`)
- `BROAD_EXCEPTION_HANDLING` detecta solo `except:` y `except Exception:`, no tipos específicos
- `MISSING_WAIT_STRATEGY` (MockLLM) verifica 5 líneas previas buscando keywords de espera

### Mitigaciones futuras (propuestas)

- Clasificador `_is_api_test_file()` para desactivar checks de UI en `tests/api/`
- Fichero de configuración `.gtaa.yaml` para exclusiones por proyecto
- Whitelists por checker configurable

---

*Última actualización: 1 de febrero de 2026*
