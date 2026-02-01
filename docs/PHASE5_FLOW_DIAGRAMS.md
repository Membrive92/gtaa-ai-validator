# Fase 5 — Diagramas de Flujo e Implementación

## Índice

1. [Visión General de la Fase 5](#1-visión-general-de-la-fase-5)
2. [Arquitectura del Módulo LLM](#2-arquitectura-del-módulo-llm)
3. [Flujo Principal: Análisis Semántico con AI](#3-flujo-principal-análisis-semántico-con-ai)
4. [Selección de Cliente LLM en el CLI](#4-selección-de-cliente-llm-en-el-cli)
5. [GeminiLLMClient — API Real](#5-geminillmclient--api-real)
6. [MockLLMClient — Heurísticas Deterministas](#6-mockllmclient--heurísticas-deterministas)
7. [Prompt Engineering](#7-prompt-engineering)
8. [SemanticAnalyzer — Orquestación](#8-semanticanalyzer--orquestación)
9. [Fase 1: Detección de Violaciones Semánticas](#9-fase-1-detección-de-violaciones-semánticas)
10. [Fase 2: Enriquecimiento con Sugerencias AI](#10-fase-2-enriquecimiento-con-sugerencias-ai)
11. [Parsing Robusto de Respuestas LLM](#11-parsing-robusto-de-respuestas-llm)
12. [Mapa Completo de Violaciones Semánticas](#12-mapa-completo-de-violaciones-semánticas)
13. [Configuración: API Key y .env](#13-configuración-api-key-y-env)
14. [Mapa de Tests](#14-mapa-de-tests)

---

## 1. Visión General de la Fase 5

La Fase 5 añade análisis semántico con inteligencia artificial al validador. Un LLM (Gemini Flash) analiza el código de test automation para detectar violaciones que el análisis estático (AST) no puede captar, y enriquece las violaciones existentes con sugerencias contextuales.

```
┌─────────────────────────────────────────────────────────────────┐
│                      __main__.py (CLI)                           │
│                                                                 │
│  python -m gtaa_validator /path --ai --html report.html         │
│                                                                 │
│  1. StaticAnalyzer.analyze() ──────────► Report (35 violaciones)│
│                                            │                    │
│  2. ¿--ai activado?                       │                    │
│     │                                      │                    │
│     ├── Sí + GEMINI_API_KEY ──► GeminiLLMClient (API real)     │
│     ├── Sí + sin key ────────► MockLLMClient (heurísticas)     │
│     └── No ──────────────────► Saltar análisis semántico       │
│                                            │                    │
│  3. SemanticAnalyzer.analyze(report)       │                    │
│     ├── Fase 1: Detectar nuevas violaciones semánticas          │
│     └── Fase 2: Enriquecer TODAS con sugerencias AI             │
│                                            │                    │
│  4. Report final (35 estáticas + N semánticas + sugerencias AI) │
│                                                                 │
│  5. Exportar: texto + --json + --html                           │
└─────────────────────────────────────────────────────────────────┘
```

**Principio clave:** el flag `--ai` es completamente opcional. Sin él, el validador funciona exactamente como en las Fases 1-4 (solo análisis estático).

---

## 2. Arquitectura del Módulo LLM

```
gtaa_validator/llm/
├── __init__.py          ← Re-exporta MockLLMClient y GeminiLLMClient
├── client.py            ← MockLLMClient (heurísticas AST + regex)
├── gemini_client.py     ← GeminiLLMClient (Gemini Flash API real)
└── prompts.py           ← Templates de prompts para el modelo

Dependencias externas:
  google-genai ≥ 1.0.0   ← SDK nativo de Google para Gemini
  python-dotenv ≥ 1.0.0  ← Carga de variables de entorno desde .env
```

```
Ambos clientes implementan la misma interfaz (duck typing):

  ┌──────────────────────────────────────┐
  │           Interfaz LLM Client        │
  │                                      │
  │  analyze_file(content, path)         │
  │     → List[dict]                     │
  │                                      │
  │  enrich_violation(violation, content) │
  │     → str                            │
  └──────────────────────────────────────┘
           ▲                ▲
           │                │
  ┌────────┴──────┐  ┌─────┴──────────┐
  │ MockLLMClient │  │ GeminiLLMClient│
  │               │  │                │
  │ AST + regex   │  │ Gemini Flash   │
  │ Determinista  │  │ API (google-   │
  │ Sin API key   │  │ genai SDK)     │
  └───────────────┘  └────────────────┘
```

**Decisión de diseño:** No se usa una clase base abstracta (`ABC`) porque solo hay dos implementaciones y Python soporta duck typing. Si en el futuro se añaden más clientes (OpenAI, Claude, Ollama), se formalizaría con un `BaseLLMClient`.

---

## 3. Flujo Principal: Análisis Semántico con AI

```
__main__.py: main()
    │
    ▼
┌──────────────────────┐
│ StaticAnalyzer        │
│ .analyze()            │──────► Report (violaciones estáticas)
└──────────┬───────────┘
           │
           ▼
      ¿Flag --ai?
     ┌────┴────┐
     │ No      │ Sí
     │         │
     ▼         ▼
  (saltar)   ┌────────────────────┐
             │ ¿GEMINI_API_KEY?   │
             ├────┬───────────────┤
             │ Sí │      No       │
             ▼    │               ▼
    GeminiLLM│    │     MockLLMClient()
    Client() │    │     + mensaje informativo
             ▼    │               │
             └────┴───────────────┘
                      │
                      ▼
             ┌──────────────────────┐
             │  SemanticAnalyzer     │
             │  .analyze(report)     │
             │                       │
             │  Fase 1: Detección    │
             │  Fase 2: Enriquecim.  │
             │  Recalcular score     │
             └──────────┬───────────┘
                        │
                        ▼
               Report enriquecido
              (estáticas + semánticas
               + sugerencias AI)
```

---

## 4. Selección de Cliente LLM en el CLI

`__main__.py:62-72`

```python
if ai:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        click.echo("Usando Gemini Flash API para análisis semántico...")
        llm_client = GeminiLLMClient(api_key)
    else:
        click.echo("GEMINI_API_KEY no configurada, usando análisis mock...")
        llm_client = MockLLMClient()
    semantic = SemanticAnalyzer(project_path, llm_client, verbose=verbose)
    report = semantic.analyze(report)
```

```
Flujo de decisión:

  ┌───────────────────┐
  │ os.environ.get    │
  │ ("GEMINI_API_KEY")│
  └────────┬──────────┘
           │
     ¿api_key truthy?
     ┌────┴────┐
     │ Sí      │ No (vacío o ausente)
     ▼         ▼
  Gemini     MockLLM
  LLMClient  Client
  (API real) (heurísticas)
     │         │
     └────┬────┘
          ▼
  SemanticAnalyzer(project_path, llm_client)
```

**La carga de la variable de entorno** ocurre en `__main__.py:19-21`:

```python
from dotenv import load_dotenv
load_dotenv()  # Carga .env del directorio actual
```

`load_dotenv()` se ejecuta ANTES de los imports de módulos del proyecto, asegurando que `GEMINI_API_KEY` esté disponible en `os.environ`.

---

## 5. GeminiLLMClient — API Real

`gemini_client.py` — Cliente que envía código al modelo Gemini y recibe análisis semántico.

```
┌─────────────────────────────────────────────────────────────┐
│                    GeminiLLMClient                            │
│                                                             │
│  __init__(api_key, model="gemini-2.5-flash-lite")           │
│     │                                                       │
│     ├── Validar api_key (ValueError si vacía)               │
│     └── self.client = genai.Client(api_key=api_key)         │
│                                                             │
│  VALID_TYPES = {                                            │
│     "UNCLEAR_TEST_PURPOSE",                                 │
│     "PAGE_OBJECT_DOES_TOO_MUCH",                            │
│     "IMPLICIT_TEST_DEPENDENCY",                             │
│     "MISSING_WAIT_STRATEGY"                                 │
│  }                                                          │
│                                                             │
│  analyze_file(file_content, file_path) → List[dict]         │
│     │                                                       │
│     ├── 1. Construir prompt con ANALYZE_FILE_PROMPT         │
│     ├── 2. Enviar a Gemini con SYSTEM_PROMPT                │
│     ├── 3. Parsear respuesta JSON (_parse_violations)       │
│     └── 4. Filtrar por VALID_TYPES                          │
│                                                             │
│  enrich_violation(violation, file_content) → str            │
│     │                                                       │
│     ├── 1. Construir prompt con ENRICH_VIOLATION_PROMPT     │
│     ├── 2. Enviar a Gemini con SYSTEM_PROMPT                │
│     └── 3. Retornar texto limpio (strip)                    │
│                                                             │
│  _parse_violations(text) → List[dict]  (privado)            │
│     │                                                       │
│     ├── 1. Regex: extraer JSON array del texto              │
│     ├── 2. json.loads() con fallback                        │
│     ├── 3. Filtrar items válidos por VALID_TYPES            │
│     └── 4. Normalizar estructura de cada violación          │
└─────────────────────────────────────────────────────────────┘
```

### Llamada a la API de Gemini

Cada llamada usa `client.models.generate_content()` del SDK `google-genai`:

```
┌────────────────────────┐
│ client.models           │
│ .generate_content(      │
│   model="gemini-2.5-    │
│         flash-lite",    │
│   contents=prompt,      │
│   config=Config(        │
│     system_instruction  │
│       =SYSTEM_PROMPT,   │
│     temperature=0.1     │  ← analyze_file (determinismo)
│              ó 0.2      │  ← enrich_violation (algo más creativo)
│   )                     │
│ )                       │
└────────┬───────────────┘
         │
         ▼
    response.text ──► String con JSON o texto libre
```

### Manejo de errores

```
try:
    response = client.models.generate_content(...)
    return self._parse_violations(response.text)
except Exception:    ← Captura CUALQUIER error (red, API, rate limit)
    return []        ← Silencioso: no rompe el flujo

Errores posibles:
  ├── 429 RESOURCE_EXHAUSTED (rate limit)
  ├── 403 PERMISSION_DENIED (API key inválida)
  ├── 500 INTERNAL (error del servidor)
  ├── Timeout de red
  └── Respuesta malformada
```

**Decisión:** Los errores se silencian (`return []` / `return ""`) para que un fallo de la API no rompa el análisis estático que ya completó su trabajo.

---

## 6. MockLLMClient — Heurísticas Deterministas

`client.py` — Cliente mock que usa AST + regex para simular análisis LLM sin API.

```
┌─────────────────────────────────────────────────────────┐
│                    MockLLMClient                         │
│                                                         │
│  analyze_file(file_content, file_path) → List[dict]     │
│     │                                                   │
│     ├── ast.parse(file_content)                         │
│     ├── ¿Es archivo de test?                            │
│     │   ├── _check_unclear_test_purpose()               │
│     │   └── _check_implicit_test_dependency()           │
│     └── ¿Es Page Object?                                │
│         ├── _check_page_object_too_much()               │
│         └── _check_missing_wait_strategy()              │
│                                                         │
│  enrich_violation(violation, file_content) → str        │
│     └── Mapeo estático: tipo → sugerencia predefinida   │
│                                                         │
│  Heurísticas de detección:                              │
│  ┌──────────────────────────────────────────────┐       │
│  │ UNCLEAR_TEST_PURPOSE:                        │       │
│  │   test sin docstring + nombre < 20 chars     │       │
│  │                                              │       │
│  │ PAGE_OBJECT_DOES_TOO_MUCH:                   │       │
│  │   clase con > 10 métodos públicos            │       │
│  │                                              │       │
│  │ IMPLICIT_TEST_DEPENDENCY:                    │       │
│  │   variable mutable a nivel de módulo         │       │
│  │                                              │       │
│  │ MISSING_WAIT_STRATEGY:                       │       │
│  │   click/fill/send_keys sin wait en 5 líneas  │       │
│  │   anteriores                                 │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  Clasificación de archivos:                             │
│  ┌──────────────────────────────────────────────┐       │
│  │ _is_test_file():                             │       │
│  │   test_*.py | *_test.py | /tests/ | /test/   │       │
│  │                                              │       │
│  │ _is_page_object():                           │       │
│  │   *_page.py | *_pom.py | /pages/ | /pom/     │       │
│  └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

**Diferencia clave Mock vs Gemini:**

| Aspecto | MockLLMClient | GeminiLLMClient |
|---------|---------------|-----------------|
| Detección | Reglas fijas (AST + regex) | Comprensión semántica real |
| Sugerencias | Templates predefinidos | Contextuales al código |
| API key | No requiere | Requiere GEMINI_API_KEY |
| Determinismo | 100% reproducible | Varía entre ejecuciones |
| Coste | Gratuito | Gratuito (free tier) |
| Modelo | N/A | gemini-2.5-flash-lite |

---

## 7. Prompt Engineering

`prompts.py` — Tres templates que definen el contrato con el modelo.

### SYSTEM_PROMPT

Define el contexto experto del modelo:

```
┌──────────────────────────────────────────────────────┐
│                   SYSTEM_PROMPT                       │
│                                                      │
│  Rol: Experto en test automation y gTAA              │
│                                                      │
│  Contexto gTAA:                                      │
│  ├── Capa de Definición (tests/) → Tests             │
│  ├── Capa de Adaptación (pages/) → Page Objects      │
│  └── Capa de Ejecución → Framework (pytest/Selenium) │
│                                                      │
│  Principios:                                         │
│  ├── Tests independientes, claros, mantenibles       │
│  └── Page Objects con responsabilidad única           │
└──────────────────────────────────────────────────────┘
```

### ANALYZE_FILE_PROMPT

Template para detección de violaciones (`analyze_file()`):

```
┌──────────────────────────────────────────────────────┐
│               ANALYZE_FILE_PROMPT                     │
│                                                      │
│  Input:                                              │
│  ├── {file_path}    → Ruta del archivo               │
│  └── {file_content} → Código Python completo         │
│                                                      │
│  Instrucciones:                                      │
│  ├── Buscar SOLO 4 tipos de violación                │
│  ├── Responder SOLO con JSON array                   │
│  └── [] si no hay violaciones                        │
│                                                      │
│  Formato de salida esperado:                         │
│  [                                                   │
│    {                                                 │
│      "type": "TIPO_DE_VIOLACION",                    │
│      "line": 42,                                     │
│      "message": "Descripción en español",            │
│      "code_snippet": "línea problemática"            │
│    }                                                 │
│  ]                                                   │
│                                                      │
│  4 tipos válidos:                                    │
│  ├── UNCLEAR_TEST_PURPOSE                            │
│  ├── PAGE_OBJECT_DOES_TOO_MUCH                       │
│  ├── IMPLICIT_TEST_DEPENDENCY                        │
│  └── MISSING_WAIT_STRATEGY                           │
└──────────────────────────────────────────────────────┘
```

### ENRICH_VIOLATION_PROMPT

Template para enriquecimiento de violaciones (`enrich_violation()`):

```
┌──────────────────────────────────────────────────────┐
│              ENRICH_VIOLATION_PROMPT                   │
│                                                      │
│  Input:                                              │
│  ├── {violation_type}    → Tipo de violación         │
│  ├── {violation_message} → Mensaje descriptivo       │
│  ├── {file_path}         → Ruta del archivo          │
│  ├── {line_number}       → Número de línea           │
│  ├── {code_snippet}      → Fragmento de código       │
│  └── {file_content}      → Código completo           │
│                                                      │
│  Instrucciones:                                      │
│  ├── Sugerencia breve (2-3 frases)                   │
│  ├── En español                                      │
│  ├── Explicar POR QUÉ es problema en gTAA            │
│  ├── Explicar CÓMO corregirlo en este contexto       │
│  └── Sin formato markdown ni prefijos                │
└──────────────────────────────────────────────────────┘
```

### Flujo de datos Prompt → Respuesta

```
analyze_file():

  ANALYZE_FILE_PROMPT.format(          SYSTEM_PROMPT
    file_path=path,                         │
    file_content=code                       │
  )                                         │
    │                                       │
    └──────────┬───────────────────────────┘
               ▼
    ┌─────────────────────┐
    │   Gemini Flash API   │
    │  temperature = 0.1   │  ← Bajo para respuestas deterministas
    └──────────┬──────────┘
               │
               ▼
    '```json\n[{"type":..., "line":..., "message":..., "code_snippet":...}]\n```'
               │
               ▼
    _parse_violations() ──► List[dict] filtrado y validado


enrich_violation():

  ENRICH_VIOLATION_PROMPT.format(      SYSTEM_PROMPT
    violation_type=...,                     │
    violation_message=...,                  │
    file_path=...,                          │
    line_number=...,                        │
    code_snippet=...,                       │
    file_content=code                       │
  )                                         │
    │                                       │
    └──────────┬───────────────────────────┘
               ▼
    ┌─────────────────────┐
    │   Gemini Flash API   │
    │  temperature = 0.2   │  ← Algo más creativo para sugerencias
    └──────────┬──────────┘
               │
               ▼
    "Este test no describe claramente qué comportamiento valida.
     Renómbralo a test_login_con_credenciales_invalidas_muestra_error
     para que su propósito sea evidente sin leer el código."
```

---

## 8. SemanticAnalyzer — Orquestación

`semantic_analyzer.py` — Orquesta las dos fases del análisis semántico.

```
┌─────────────────────────────────────────────────────────────┐
│                    SemanticAnalyzer                           │
│                                                             │
│  __init__(project_path, llm_client, verbose)                │
│     ├── self.project_path = Path                            │
│     ├── self.llm_client = MockLLM ó GeminiLLM              │
│     └── self.verbose = bool                                 │
│                                                             │
│  analyze(report) → Report                                   │
│     │                                                       │
│     ├── 1. _discover_python_files()                         │
│     │      └── rglob("*.py") excluyendo EXCLUDED_DIRS       │
│     │                                                       │
│     ├── 2. Fase 1: Detección semántica                      │
│     │      └── Para cada .py → llm_client.analyze_file()    │
│     │                                                       │
│     ├── 3. Fase 2: Enriquecimiento                          │
│     │      └── Para cada violación → llm_client.enrich()    │
│     │                                                       │
│     └── 4. report.calculate_score()                         │
│                                                             │
│  _discover_python_files() → List[Path]                      │
│     └── Excluye: venv, env, .venv, .env, .git,             │
│         __pycache__, node_modules, .pytest_cache,           │
│         build, dist                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Fase 1: Detección de Violaciones Semánticas

`semantic_analyzer.py:59-84`

```
Fase 1: Detección
    │
    ▼
┌──────────────────────────────────┐
│ Para cada archivo Python:        │
│                                  │
│  file_path.read_text("utf-8")   │
│         │                        │
│         ▼                        │
│  llm_client.analyze_file(        │
│    content, str(file_path)       │
│  )                               │
│         │                        │
│         ▼                        │
│  List[dict] raw_violations       │
│         │                        │
│  Para cada raw violation:        │
│  ┌─────────────────────────────┐ │
│  │ vtype_name = raw["type"]    │ │
│  │         │                   │ │
│  │ ViolationType(vtype_name)   │ │
│  │    ¿ValueError? → continue  │ │
│  │         │                   │ │
│  │ Violation(                  │ │
│  │   type = vtype,             │ │
│  │   severity = vtype          │ │
│  │     .get_severity(),        │ │
│  │   file_path = file_path,   │ │
│  │   line_number = raw["line"],│ │
│  │   message = raw["message"], │ │
│  │   code_snippet = raw[       │ │
│  │     "code_snippet"]         │ │
│  │ )                           │ │
│  │         │                   │ │
│  │ report.violations.append()  │ │
│  └─────────────────────────────┘ │
└──────────────────────────────────┘
```

**Punto clave:** `ViolationType(vtype_name)` actúa como segunda validación. Aunque `GeminiLLMClient` ya filtra por `VALID_TYPES`, el `SemanticAnalyzer` verifica que el tipo exista como `Enum` en el modelo. Esto protege contra inconsistencias si se añaden nuevos tipos en el futuro.

---

## 10. Fase 2: Enriquecimiento con Sugerencias AI

`semantic_analyzer.py:86-100`

```
Fase 2: Enriquecimiento
    │
    ▼
┌───────────────────────────────────────┐
│ Para CADA violación en report:        │
│ (estáticas + semánticas recién        │
│  detectadas en Fase 1)                │
│                                       │
│  ¿violation.ai_suggestion?            │
│  ├── Sí → continue (ya enriquecida)  │
│  └── No ↓                            │
│                                       │
│  file_path.read_text("utf-8")        │
│         │                             │
│         ▼                             │
│  llm_client.enrich_violation(         │
│    violation.to_dict(),               │
│    file_content                       │
│  )                                    │
│         │                             │
│         ▼                             │
│  ¿suggestion truthy?                  │
│  ├── Sí → violation.ai_suggestion =  │
│  │        suggestion                  │
│  └── No → (sin cambio)               │
└───────────────────────────────────────┘
```

**Impacto en llamadas API:**

```
Ejemplo con bad_project (6 archivos Python):

  Fase 1: 6 llamadas a analyze_file()
          └── Detecta ~24 violaciones semánticas nuevas

  Fase 2: 35 estáticas + 24 semánticas = 59 llamadas a enrich_violation()

  Total: ~65 llamadas API por ejecución
```

Con `gemini-2.5-flash-lite` (free tier: 1000 req/día, 15 RPM), esto permite ~15 ejecuciones diarias sin coste.

---

## 11. Parsing Robusto de Respuestas LLM

`gemini_client.py:87-119` — El parser maneja las variaciones de formato del modelo.

```
_parse_violations(text)
    │
    ▼
┌──────────────────────────────────────┐
│ ¿text vacío?                         │
│ └── Sí → return []                   │
│                                      │
│ Regex: re.search(r'\[.*\]', text,    │
│                   re.DOTALL)         │
│ └── ¿No match? → return []          │
│                                      │
│ json.loads(match.group())            │
│ └── ¿JSONDecodeError? → return []    │
│                                      │
│ ¿isinstance(data, list)?             │
│ └── No → return []                   │
│                                      │
│ Para cada item en data:              │
│ ├── ¿isinstance(item, dict)?         │
│ │   └── No → continue                │
│ ├── vtype = item["type"]             │
│ ├── ¿vtype in VALID_TYPES?           │
│ │   └── No → continue                │
│ └── Añadir a violations:             │
│     {type, line, message,            │
│      code_snippet}                   │
│                                      │
│ return violations                    │
└──────────────────────────────────────┘
```

### Casos que maneja el parser

```
Caso 1: JSON limpio
  Input:  [{"type": "UNCLEAR_TEST_PURPOSE", ...}]
  Output: [{"type": "UNCLEAR_TEST_PURPOSE", ...}]     ✓

Caso 2: JSON envuelto en markdown
  Input:  ```json\n[{"type": ...}]\n```
  Output: [{"type": ...}]                             ✓
  (el regex \[.*\] extrae el array del bloque markdown)

Caso 3: Texto libre sin JSON
  Input:  "No encontré violaciones en este archivo."
  Output: []                                          ✓
  (regex no encuentra \[.*\], retorna [])

Caso 4: JSON con tipos inventados
  Input:  [{"type": "TIPO_INVENTADO", ...}]
  Output: []                                          ✓
  (VALID_TYPES filtra tipos no reconocidos)

Caso 5: JSON malformado
  Input:  [{type: UNCLEAR sin comillas}]
  Output: []                                          ✓
  (json.loads lanza JSONDecodeError, se captura)

Caso 6: Array vacío
  Input:  []
  Output: []                                          ✓

Caso 7: Respuesta None/vacía
  Input:  None o ""
  Output: []                                          ✓
```

---

## 12. Mapa Completo de Violaciones Semánticas

La Fase 5 introduce 4 tipos de violación semántica, complementando los 9 tipos estáticos de las Fases 2-3:

```
┌────────────────────────────────┬──────────┬────────────────────────────┐
│ Tipo                           │ Severidad│ Detección                  │
├────────────────────────────────┼──────────┼────────────────────────────┤
│ UNCLEAR_TEST_PURPOSE           │ MEDIUM   │ LLM: nombre/docstring      │
│                                │          │ no describe comportamiento │
│                                │          │                            │
│ PAGE_OBJECT_DOES_TOO_MUCH      │ MEDIUM   │ LLM: demasiadas            │
│                                │          │ responsabilidades en POM   │
│                                │          │                            │
│ IMPLICIT_TEST_DEPENDENCY       │ HIGH     │ LLM: tests comparten       │
│                                │          │ estado mutable             │
│                                │          │                            │
│ MISSING_WAIT_STRATEGY          │ MEDIUM   │ LLM: interacción UI        │
│                                │          │ sin espera explícita       │
└────────────────────────────────┴──────────┴────────────────────────────┘
```

### Mapa completo: 13 tipos de violación (Fases 2-5)

```
Estáticas (Fases 2-3):                    Semánticas (Fase 5):
┌────────────────────────────────┐        ┌────────────────────────────────┐
│ ADAPTATION_IN_DEFINITION  CRIT │        │ UNCLEAR_TEST_PURPOSE      MED  │
│ MISSING_LAYER_STRUCTURE   CRIT │        │ PAGE_OBJECT_DOES_TOO_MUCH MED  │
│ ASSERTION_IN_POM          HIGH │        │ IMPLICIT_TEST_DEPENDENCY  HIGH │
│ FORBIDDEN_IMPORT          HIGH │        │ MISSING_WAIT_STRATEGY     MED  │
│ HARDCODED_TEST_DATA       HIGH │        └────────────────────────────────┘
│ BUSINESS_LOGIC_IN_POM     MED  │
│ DUPLICATE_LOCATOR         MED  │        Detectados por:
│ LONG_TEST_FUNCTION        MED  │        ├── GeminiLLMClient (comprensión
│ POOR_TEST_NAMING          LOW  │        │   semántica del código)
└────────────────────────────────┘        └── MockLLMClient (heurísticas
                                              AST + regex como fallback)
Detectados por:
├── DefinitionChecker (AST)
├── StructureChecker (filesystem)
├── AdaptationChecker (AST + visitors)
└── QualityChecker (AST + regex)
```

---

## 13. Configuración: API Key y .env

### Estructura de configuración

```
Proyecto raíz/
├── .env              ← API key real (gitignored)
├── .env.example      ← Template para usuarios (tracked)
└── .gitignore        ← Contiene ".env"
```

### Flujo de carga de configuración

```
┌─────────────────────────────┐
│ __main__.py                  │
│                              │
│ from dotenv import load_dotenv│
│ load_dotenv()                │ ← Lee .env y carga en os.environ
│                              │
│ ...                          │
│ api_key = os.environ.get(    │
│   "GEMINI_API_KEY", ""       │
│ )                            │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │  Orden de búsqueda  │
    │                     │
    │  1. os.environ      │ ← Variable de entorno del sistema
    │  2. .env archivo    │ ← Cargado por load_dotenv()
    │  3. "" (fallback)   │ ← Sin key → MockLLMClient
    └─────────────────────┘
```

### .env.example

```
# API Key de Gemini para análisis semántico AI
# Obtener en: https://aistudio.google.com/api-keys
GEMINI_API_KEY=tu_key_aqui
```

### Elección del modelo

```
Modelo: gemini-2.5-flash-lite

Free tier:
├── 15 RPM (requests per minute)
├── 1000 RPD (requests per day)
├── 1M TPM (tokens per minute)
└── Coste: $0

Alternativas evaluadas:
├── gemini-2.0-flash → Rate limit más restrictivo, retirado marzo 2026
├── gemini-2.5-flash → Más potente pero menor cuota gratuita
└── gemini-2.5-flash-lite → Mejor relación cuota/capacidad para PoC ✓
```

---

## 14. Mapa de Tests

### Tests Unitarios — GeminiLLMClient (12 tests)

```
tests/unit/test_gemini_client.py

TestGeminiClientInit (3 tests):
├── test_sin_api_key_lanza_error         ← ValueError con key ""
├── test_sin_api_key_none_lanza_error    ← ValueError con key None
└── test_con_api_key_crea_cliente        ← Instancia correcta

TestGeminiAnalyzeFile (6 tests):
├── test_parse_respuesta_json_valida     ← JSON → List[dict]
├── test_parse_json_envuelto_en_markdown ← ```json...``` → List[dict]
├── test_filtra_tipos_invalidos          ← Tipo desconocido → []
├── test_respuesta_vacia_retorna_lista   ← "[]" → []
├── test_respuesta_no_json_retorna_lista ← Texto libre → []
└── test_error_api_retorna_lista_vacia   ← Exception → []

TestGeminiEnrichViolation (3 tests):
├── test_retorna_sugerencia              ← Texto del modelo
├── test_error_api_retorna_string_vacio  ← Exception → ""
└── test_respuesta_vacia_retorna_string  ← "   " → ""
```

### Tests existentes — MockLLMClient y SemanticAnalyzer

```
tests/unit/test_llm_client.py          ← Tests del MockLLMClient
tests/unit/test_semantic_analyzer.py   ← Tests del SemanticAnalyzer
tests/integration/test_semantic.py     ← Tests E2E con mock
```

### Estrategia de testing

```
┌────────────────────────────────────────────────────────┐
│  Todos los tests de GeminiLLMClient usan               │
│  @patch("...genai.Client") para mockear la API.        │
│                                                        │
│  Esto asegura:                                         │
│  ├── Tests deterministas (sin llamadas reales)         │
│  ├── Sin coste de API en CI/CD                         │
│  ├── Sin dependencia de red                            │
│  └── Velocidad (~0.01s por test)                       │
│                                                        │
│  Cobertura:                                            │
│  ├── Inicialización (validación de API key)            │
│  ├── Parsing de respuestas (JSON, markdown, basura)    │
│  ├── Filtrado de tipos (VALID_TYPES)                   │
│  ├── Manejo de errores (silencioso)                    │
│  └── Enriquecimiento (texto, vacío, error)             │
└────────────────────────────────────────────────────────┘

Total tests del proyecto: 209 (197 existentes + 12 nuevos)
```

---

*Última actualización: 1 de febrero de 2026*
