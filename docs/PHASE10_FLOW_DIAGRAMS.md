# Fase 10 - Optimización LLM + Logging y Métricas

## Resumen General

La Fase 10 se divide en diez sub-fases documentadas:

- **Fase 10.1**: Optimización de la capa LLM (fallback, factory, tracking)
- **Fase 10.2**: Sistema de logging profesional + métricas de rendimiento en reportes
- **Fase 10.3**: Optimizaciones de proyecto (packaging, dead code, tests, LSP, PEP 8)
- **Fase 10.4**: Despliegue (Docker, GitHub Actions CI, reusable action)
- **Fase 10.5**: Cobertura de código: 84% a 93% (667 tests)
- **Fase 10.6**: Tests de regresión de seguridad (34 tests, SEC-01 a SEC-09)
- **Fase 10.7**: Refactor quality_checker + Reportes Allure-style + HTML redesign
- **Fase 10.8**: Refactor SOLID/DRY del codebase completo
- **Fase 10.9**: Auditoría QA de tests (+92 tests, -11 redundantes, 761 total)
- **Fase 10.10**: Auditoría de documentación (51 hallazgos corregidos)

### Fase 10.1

La Fase 10.1 se centra en optimizar la capa LLM para manejar las limitaciones de la API de forma elegante. Las mejoras principales son:

1. **Manejo de Rate Limit**: Fallback automático de Gemini API a MockLLMClient cuando se alcanza el límite (429)
2. **Limitación de Llamadas**: Opción `--max-llm-calls` para limitar llamadas API antes del fallback automático
3. **Tracking de Proveedor**: Registrar qué proveedor LLM se usó y mostrarlo en los reportes
4. **Patrón Factory**: Creación centralizada de clientes LLM con detección automática del proveedor

---

## 1. Arquitectura de la Capa LLM

### 1.1 Vista General de Componentes

```
+------------------------------------------------------------------+
|                         CLI (__main__.py)                         |
|                                                                    |
|  --ai --provider=[gemini|mock] --max-llm-calls=N                  |
+----------------------------------+-------------------------------+
                                   |
                                   v
+------------------------------------------------------------------+
|                    create_llm_client() [Factory]                  |
|                                                                    |
|  1. Verificar parámetro provider                                   |
|  2. Si 'gemini' o None: verificar GEMINI_API_KEY                  |
|  3. Si existe key: retornar APILLMClient                          |
|  4. Si no: retornar MockLLMClient                                 |
+----------------------------------+-------------------------------+
                                   |
                                   v
+------------------------------------------------------------------+
|                      SemanticAnalyzer                             |
|                                                                    |
|  - llm_client: LLMClientProtocol                                  |
|  - max_llm_calls: Optional[int]                                   |
|  - _initial_provider: str                                         |
|  - _current_provider: str                                         |
|  - _fallback_occurred: bool                                       |
|  - _llm_call_count: int                                           |
+------------------------------------------------------------------+
```

### 1.2 Jerarquía de Clases de Cliente LLM

```
                    +---------------------------+
                    |   LLMClientProtocol        |  (typing.Protocol, PEP 544)
                    |   @runtime_checkable       |
                    |                            |
                    | + usage: TokenUsage        |
                    | + analyze_file()           |
                    | + enrich_violation()       |
                    | + get_usage_summary()      |
                    | + get_usage_dict()         |
                    +---------------------------+
                              ^
                              | (duck typing estructural)
                              |
              +───────────────┴───────────────+
              |                               |
    +─────────────────+            +─────────────────+
    |  MockLLMClient  |            |  APILLMClient    |
    |                 |            |                  |
    | TokenUsage()    |            | TokenUsage(      |
    | (coste = 0)     |            |   input=0.075,   |
    | Heurísticas     |            |   output=0.30)   |
    | Siempre         |            | Gemini API       |
    | disponible      |            | Con rate limit   |
    +─────────────────+            +─────────────────+
```

---

## 2. Patrón Factory para Creación de Clientes LLM

### 2.1 Flujo de la Función Factory

```
                    create_llm_client(provider=None)
                                |
                                v
                    +------------------------+
                    | provider == 'mock' ?   |
                    +------------------------+
                           |           |
                          Sí          No
                           |           |
                           v           v
              +----------------+   +------------------------+
              | MockLLMClient  |   | provider == 'gemini'   |
              +----------------+   | o provider == None ?   |
                                   +------------------------+
                                          |           |
                                         Sí          No
                                          |           |
                                          v           v
                              +--------------------+  Error
                              | GEMINI_API_KEY    |
                              | existe en env?    |
                              +--------------------+
                                    |          |
                                   Sí         No
                                    |          |
                                    v          v
                          +----------------+  +----------------+
                          | APILLMClient   |  | MockLLMClient  |
                          | (con API key)  |  | (fallback)     |
                          +----------------+  +----------------+
```

### 2.2 Estructura del Código Factory

```python
# gtaa_validator/llm/factory.py

def create_llm_client(provider: str = None) -> LLMClientProtocol:
    """
    Crea cliente LLM según configuración.

    Selección de proveedor:
    - 'mock': Siempre usa MockLLMClient (heurísticas)
    - 'gemini': Usa APILLMClient si hay API key, sino Mock
    - None: Auto-detecta (gemini si hay key, sino mock)
    """
    if provider == "mock":
        return MockLLMClient()

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        return APILLMClient(api_key=api_key)
    else:
        return MockLLMClient()


def get_available_providers() -> dict:
    """Retorna proveedores disponibles y su estado."""
    return {
        "mock": {"available": True, "reason": "Siempre disponible"},
        "gemini": {
            "available": bool(os.getenv("GEMINI_API_KEY")),
            "reason": "GEMINI_API_KEY" if os.getenv("GEMINI_API_KEY") else "Falta API key"
        }
    }
```

---

## 3. Manejo de Rate Limit y Fallback Automático

### 3.1 Vista General del Mecanismo de Fallback

```
                      SemanticAnalyzer.analyze()
                                |
                                v
                    +------------------------+
                    | Para cada archivo      |
                    | candidato              |
                    +------------------------+
                                |
                                v
                    +------------------------+
                    | _check_call_limit()    |
                    | (si max_llm_calls set) |
                    +------------------------+
                                |
                    +-----------+-----------+
                    |                       |
              Límite OK            Límite Excedido
                    |                       |
                    v                       v
          +------------------+    +---------------------+
          | llm_client       |    | _fallback_to_mock() |
          | .analyze_file()  |    +---------------------+
          +------------------+              |
                    |                       v
          +---------+---------+   +------------------+
          |                   |   | Continuar con    |
      Éxito           RateLimitError | MockLLMClient   |
          |                   |   +------------------+
          v                   v
    +------------+    +---------------------+
    | Continuar  |    | _fallback_to_mock() |
    +------------+    +---------------------+
                              |
                              v
                    +------------------+
                    | Reintentar con   |
                    | MockLLMClient    |
                    +------------------+
```

### 3.2 Detección de RateLimitError

```python
# gtaa_validator/llm/api_client.py

class RateLimitError(Exception):
    """Error cuando se alcanza el límite de rate/cuota de la API."""
    pass

class APILLMClient:
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Detecta si el error es rate limit (429) o quota exceeded."""
        error_str = str(error).lower()
        return (
            "429" in error_str
            or "rate limit" in error_str
            or "quota" in error_str
            or "resource exhausted" in error_str
        )

    def analyze_file(self, content, file_path, **kwargs):
        try:
            # ... llamada API ...
            return self._parse_violations(response.text)
        except Exception as e:
            if self._is_rate_limit_error(e):
                raise RateLimitError(f"Rate limit: {e}") from e
            return []
```

### 3.3 Implementación del Fallback

```python
# gtaa_validator/analyzers/semantic_analyzer.py

class SemanticAnalyzer:
    def _fallback_to_mock(self, reason: str) -> None:
        """Cambia a MockLLMClient como fallback."""
        if self._fallback_occurred:
            return  # Ya en modo fallback

        self._fallback_occurred = True
        self._current_provider = "mock"
        self.llm_client = MockLLMClient()

        if self.verbose:
            print(f"\n[FALLBACK] {reason}")
            print("[FALLBACK] Continuando con MockLLMClient...")
```

---

## 4. Limitación de Llamadas con --max-llm-calls

### 4.1 Flujo de Límite de Llamadas

```
                    analyze() inicia
                          |
                          v
              +----------------------+
              | _llm_call_count = 0  |
              +----------------------+
                          |
                          v
              +----------------------+
              | Para cada operación  |
              | (analyze_file o      |
              |  enrich_violation)   |
              +----------------------+
                          |
                          v
              +----------------------+
              | _check_call_limit()  |
              +----------------------+
                          |
              +-----------+-----------+
              |                       |
        max_llm_calls           max_llm_calls
           es None                está definido
              |                       |
              v                       v
        +-----------+     +------------------------+
        | Sin límite|     | _llm_call_count += 1   |
        | Continuar |     +------------------------+
        +-----------+               |
                          +---------+---------+
                          |                   |
                    count <= max        count > max
                          |                   |
                          v                   v
                    +-----------+    +------------------+
                    | Continuar |    | _fallback_to_mock|
                    | con API   |    | ("Límite alcanzado")|
                    +-----------+    +------------------+
```

### 4.2 Implementación del Límite de Llamadas

```python
# gtaa_validator/analyzers/semantic_analyzer.py

def _check_call_limit(self) -> None:
    """Verifica si se alcanzó el límite, hace fallback si es necesario."""
    if self.max_llm_calls is None:
        return  # Sin límite
    if self._fallback_occurred:
        return  # Ya en fallback

    self._llm_call_count += 1
    if self._llm_call_count > self.max_llm_calls:
        self._fallback_to_mock(
            f"Límite de {self.max_llm_calls} llamadas LLM alcanzado"
        )
```

### 4.3 Integración con CLI

```bash
# Limitar a 5 llamadas API, luego fallback a mock
python -m gtaa_validator ./proyecto --ai --max-llm-calls 5

# Sin límite de llamadas API (por defecto)
python -m gtaa_validator ./proyecto --ai

# Forzar proveedor mock (sin llamadas API)
python -m gtaa_validator ./proyecto --ai --provider mock
```

---

## 5. Tracking de Proveedor

### 5.1 Estructura de Información del Proveedor

```python
{
    "initial_provider": "gemini",    # Proveedor configurado al inicio
    "current_provider": "mock",      # Proveedor usado actualmente
    "fallback_occurred": True,       # True si hubo cambio desde inicial
    "llm_calls": 5,                  # Llamadas hechas antes del fallback (si limitado)
    "max_llm_calls": 5               # Límite configurado (si aplica)
}
```

### 5.2 Flujo de Tracking del Proveedor

```
            SemanticAnalyzer.__init__()
                        |
                        v
            +---------------------------+
            | _initial_provider =       |
            |   _get_provider_name()    |
            | _current_provider =       |
            |   _initial_provider       |
            | _fallback_occurred = False|
            +---------------------------+
                        |
                        v
            Ejecución de analyze()
                        |
            +-----------+-----------+
            |                       |
      Sin fallback            Ocurre fallback
            |                       |
            v                       v
    +----------------+    +------------------+
    | current =      |    | current = "mock" |
    |   initial      |    | fallback = True  |
    +----------------+    +------------------+
                        |
                        v
            +---------------------------+
            | report.llm_provider_info  |
            |   = get_provider_info()   |
            +---------------------------+
```

### 5.3 Visualización del Proveedor en Reportes

**Salida CLI:**
```
[!] Fallback activado: gemini -> mock
```

**Reporte HTML:**
```html
<span>LLM: <strong>Gemini &rarr; Mock</strong> (fallback)</span>
```

**Reporte JSON:**
```json
{
    "metadata": {
        "llm_provider": {
            "initial_provider": "gemini",
            "current_provider": "mock",
            "fallback_occurred": true
        }
    }
}
```

---

## 6. Flujo Completo de Análisis con Fallback

### 6.1 Diagrama de Secuencia Completo

```
Usuario       CLI           Factory      SemanticAnalyzer    APILLMClient    MockLLMClient
  |            |               |                |                 |               |
  |--ai------->|               |                |                 |               |
  |            |--crear------->|                |                 |               |
  |            |               |--new---------->|                 |               |
  |            |               |<--APIClient----|                 |               |
  |            |<--cliente-----|                |                 |               |
  |            |                                |                 |               |
  |            |--analyze(report)-------------->|                 |               |
  |            |                                |                 |               |
  |            |                                |--analyze_file-->|               |
  |            |                                |<--RateLimitError|               |
  |            |                                |                 |               |
  |            |                                |--_fallback_to_mock()            |
  |            |                                |                                 |
  |            |                                |--analyze_file------------------>|
  |            |                                |<--violations--------------------|
  |            |                                |                                 |
  |            |<--report (con provider info)---|                                 |
  |<--mostrar--|                                |                                 |
```

### 6.2 Matriz de Manejo de Errores

| Tipo de Error | Detección | Acción | Visible al Usuario |
|---------------|-----------|--------|-------------------|
| 429 Rate Limit | `"429"` en error | Fallback a Mock | `[FALLBACK] Rate limit...` |
| Quota Exceeded | `"quota"` en error | Fallback a Mock | `[FALLBACK] Quota...` |
| Resource Exhausted | `"resource exhausted"` | Fallback a Mock | `[FALLBACK] Resource...` |
| Max Calls Reached | `_llm_call_count > max` | Fallback a Mock | `[FALLBACK] Límite...` |
| Otro Error API | Cualquier excepción | Retorna `[]` (silencioso) | Ninguno |
| Sin API Key | Falta env var | Usa Mock desde inicio | Provider: mock |

---

## 7. Estructura de Archivos Después de Fase 10.1

```
gtaa_validator/
├── llm/
│   ├── __init__.py          # Exports: MockLLMClient, APILLMClient,
│   │                        #          RateLimitError, LLMClientProtocol,
│   │                        #          TokenUsage, create_llm_client
│   ├── protocol.py          # LLMClientProtocol + TokenUsage unificado (Fase 10.8)
│   ├── client.py            # MockLLMClient (heurísticas)
│   ├── api_client.py        # APILLMClient + RateLimitError
│   ├── factory.py           # create_llm_client() → LLMClientProtocol
│   └── prompts.py           # Prompts optimizados para Fase 10
│
├── analyzers/
│   └── semantic_analyzer.py # Lógica de fallback, tracking de proveedor
│
├── models.py                # Campo Report.llm_provider_info
│
├── reporters/
│   └── html_reporter.py     # Badge de proveedor
│
└── __main__.py              # Opción --max-llm-calls

tests/unit/
├── test_api_client.py       # Tests para APILLMClient + RateLimitError
├── test_llm_factory.py      # Tests para funciones factory
└── test_semantic_analyzer.py # Tests para fallback + tracking de proveedor
```

---

## 8. Opciones de Configuración

### 8.1 Variables de Entorno

```bash
# Archivo .env
GEMINI_API_KEY=tu-api-key-aqui
```

### 8.2 Opciones CLI

| Opción | Tipo | Defecto | Descripción |
|--------|------|---------|-------------|
| `--ai` | flag | False | Activar análisis semántico con LLM |
| `--provider` | choice | auto | Proveedor LLM: `gemini`, `mock` |
| `--max-llm-calls` | int | None | Máx llamadas API antes de fallback |

### 8.3 Ejemplos de Uso

```bash
# Auto-detectar proveedor (gemini si hay key, sino mock)
python -m gtaa_validator ./proyecto --ai

# Forzar gemini (falla si no hay key)
python -m gtaa_validator ./proyecto --ai --provider gemini

# Forzar mock (sin llamadas API)
python -m gtaa_validator ./proyecto --ai --provider mock

# Limitar llamadas API a 10
python -m gtaa_validator ./proyecto --ai --max-llm-calls 10

# Salida verbose muestra fallback
python -m gtaa_validator ./proyecto --ai -v --max-llm-calls 5
```

---

## 9. Beneficios de las Optimizaciones de Fase 10.1

| Optimización | Beneficio |
|--------------|-----------|
| **Fallback Automático** | El análisis completa incluso si la API no está disponible |
| **Limitación de Llamadas** | Control de costos de API en tier gratuito (10 req/min) |
| **Tracking de Proveedor** | Transparencia sobre qué método de análisis se usó |
| **Patrón Factory** | Creación centralizada y testeable de clientes |
| **RateLimitError** | Distinción clara entre rate limits y otros errores |
| **Degradación Elegante** | Análisis estático siempre ejecuta, semántico es opcional |

---

## 10. Commits en Fase 10.1

| Commit | Tipo | Descripción |
|--------|------|-------------|
| `4479444` | refactor | Renombrar GeminiLLMClient -> APILLMClient |
| `0f6baa8` | feat | Añadir patrón factory para creación de clientes LLM |
| `b12f830` | feat | Añadir fallback por rate limit y tracking de proveedor |
| `673ddde` | feat | Mostrar proveedor LLM en reportes y CLI |
| `8732f7b` | chore | Actualizar .env.example con documentación |

---

### Fase 10.2

## 11. Sistema de Logging

### 11.1 Arquitectura del Sistema de Logging

```
                    setup_logging(verbose, log_file)
                              │
                              v
                  ┌──────────────────────┐
                  │  Logger raíz          │
                  │  "gtaa_validator"     │
                  │  level: DEBUG         │
                  └──────┬───────────────┘
                         │
              ┌──────────┴──────────┐
              v                     v
    ┌──────────────────┐  ┌──────────────────┐
    │ Console Handler  │  │  File Handler    │
    │ (stderr)         │  │  (opcional)      │
    │                  │  │                  │
    │ verbose=True:    │  │ Siempre DEBUG    │
    │   level=DEBUG    │  │ Formato ISO:     │
    │ verbose=False:   │  │ %(asctime)s      │
    │   level=WARNING  │  │ [%(levelname)s]  │
    └──────────────────┘  │ %(name)s:        │
                          │ %(message)s      │
                          └──────────────────┘
```

### 11.2 Jerarquía de Loggers

```
gtaa_validator                    <- Logger raíz (configurado en setup_logging)
├── gtaa_validator.analyzers.static_analyzer   <- 10 mensajes (debug/info/warning)
├── gtaa_validator.analyzers.semantic_analyzer  <- 3 mensajes (warning/info)
└── gtaa_validator.llm.factory                  <- 2 mensajes (info/warning)
```

Todos heredan la configuración del logger raíz `gtaa_validator`.

### 11.3 Migración print() → logging

| Módulo | print() eliminados | Niveles usados |
|--------|-------------------|----------------|
| `static_analyzer.py` | 10 | DEBUG (7), INFO (2), WARNING (1) |
| `semantic_analyzer.py` | 3 | INFO (2), WARNING (1) |
| `llm/factory.py` | 2 | INFO (1), WARNING (1) |
| **Total** | **15** | — |

### 11.4 Comportamiento del Log File

```
┌─────────────────────────────────┐
│          Flags CLI              │
├──────────┬──────────────────────┤
│ --verbose│ --log-file           │
├──────────┼──────────────────────┤
│    No    │    No                │  →  Solo consola (WARNING+), sin fichero
│    Sí    │    No                │  →  Consola (DEBUG+) + logs/gtaa_debug.log
│    No    │    custom.log        │  →  Consola (WARNING+) + custom.log
│    Sí    │    custom.log        │  →  Consola (DEBUG+) + custom.log (override)
└──────────┴──────────────────────┘
```

El directorio `logs/` se crea automáticamente y está en `.gitignore`.

---

## 12. AnalysisMetrics — Métricas de Rendimiento

### 12.1 Estructura del Dataclass

```python
@dataclass
class AnalysisMetrics:
    # Timing por fase
    static_analysis_seconds: float = 0.0
    semantic_analysis_seconds: float = 0.0
    report_generation_seconds: float = 0.0
    total_seconds: float = 0.0
    files_per_second: float = 0.0

    # Métricas LLM (condicionales)
    llm_api_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_total_tokens: int = 0
    llm_estimated_cost_usd: float = 0.0
```

### 12.2 Flujo de Instrumentación en CLI

```
__main__.py:

t0 = time.time()
├── StaticAnalyzer.analyze()
t1 = time.time()
├── SemanticAnalyzer.analyze()    (si --ai)
t2 = time.time()
├── JsonReporter.generate()       (si --json)
├── HtmlReporter.generate()       (si --html)
t3 = time.time()

metrics = AnalysisMetrics(
    static_analysis_seconds  = t1 - t0,
    semantic_analysis_seconds = t2 - t1,    # 0.0 si no --ai
    report_generation_seconds = t3 - t2,
    total_seconds = t3 - t0,
    files_per_second = files / (t1 - t0),
)

# Si --ai: poblar métricas LLM desde SemanticAnalyzer
if semantic:
    token_usage = semantic.get_token_usage()
    metrics.llm_api_calls = token_usage['total_calls']
    metrics.llm_total_tokens = token_usage['total_tokens']
    ...
```

### 12.3 Serialización Condicional

```python
def to_dict(self) -> dict:
    result = {
        "timing": {
            "static_analysis_seconds": ...,
            "total_seconds": ...,
            "files_per_second": ...,
        }
    }
    # Solo incluir sección LLM si hubo llamadas API
    if self.llm_api_calls > 0:
        result["llm"] = {
            "api_calls": ...,
            "total_tokens": ...,
            "estimated_cost_usd": ...,
        }
    return result
```

### 12.4 Visualización en Reportes

**HTML — Tarjetas de métricas:**

```
┌──────────────────────────────────────────────────────────┐
│  Métricas de Rendimiento                                 │
├──────────────┬───────────────┬───────────────────────────┤
│ 0.45s        │ 2.10s         │ 11.1                     │
│ Análisis     │ Análisis      │ Archivos/                │
│ Estático     │ Semántico     │ segundo                  │
├──────────────┼───────────────┼───────────────────────────┤
│ 3            │ 2,000         │ $0.0030                  │
│ Llamadas API │ Tokens        │ Costo                    │
│  (LLM)      │ Totales (LLM) │ Estimado (LLM)           │
└──────────────┴───────────────┴───────────────────────────┘
```

Las tarjetas LLM (borde morado) solo aparecen cuando `llm_api_calls > 0`.

**JSON — En metadata:**

```json
{
    "metadata": {
        "metrics": {
            "timing": {
                "static_analysis_seconds": 0.45,
                "semantic_analysis_seconds": 2.10,
                "total_seconds": 2.55,
                "files_per_second": 11.1
            },
            "llm": {
                "api_calls": 3,
                "total_tokens": 2000,
                "estimated_cost_usd": 0.003
            }
        }
    }
}
```

---

## 13. Estructura de Archivos Después de Fase 10.2

```
gtaa_validator/
├── logging_config.py          # NUEVO: setup_logging() centralizado
├── models.py                  # MODIFICADO: +AnalysisMetrics, Report.metrics
├── __main__.py                # MODIFICADO: timing, --log-file, default log path
│
├── analyzers/
│   ├── static_analyzer.py     # MODIFICADO: print() → logging (10 sentencias)
│   └── semantic_analyzer.py   # MODIFICADO: print() → logging (3 sentencias)
│
├── llm/
│   └── factory.py             # MODIFICADO: print() → logging (2 sentencias)
│
└── reporters/
    ├── html_reporter.py       # MODIFICADO: +sección métricas de rendimiento
    └── json_reporter.py       # Sin cambios (ya serializa Report.to_dict())

tests/unit/
├── test_logging_config.py     # NUEVO: 9 tests para logging
├── test_models.py             # MODIFICADO: +9 tests para AnalysisMetrics
├── test_html_reporter.py      # MODIFICADO: +4 tests para métricas HTML
└── test_json_reporter.py      # MODIFICADO: +2 tests para métricas JSON
```

---

## 14. Opciones CLI Actualizadas (Fase 10.1 + 10.2)

| Opción | Tipo | Defecto | Descripción |
|--------|------|---------|-------------|
| `--ai` | flag | False | Activar análisis semántico con LLM |
| `--provider` | choice | auto | Proveedor LLM: `gemini`, `mock` |
| `--max-llm-calls` | int | None | Máx llamadas API antes de fallback |
| `--verbose` / `-v` | flag | False | Salida detallada + log a `logs/gtaa_debug.log` |
| `--log-file` | path | None | Ruta personalizada para log (override del default) |

### Ejemplos de Uso

```bash
# Análisis básico (sin logs a fichero)
python -m gtaa_validator ./proyecto

# Verbose: consola DEBUG + logs/gtaa_debug.log automático
python -m gtaa_validator ./proyecto --verbose

# Log a fichero personalizado
python -m gtaa_validator ./proyecto --log-file output/analysis.log

# Análisis AI con métricas completas
python -m gtaa_validator ./proyecto --ai --verbose --html report.html --json report.json
```

---

## 15. Commits en Fase 10.2

| Commit | Tipo | Descripción |
|--------|------|-------------|
| `136c6a4` | feat | Añadir logging_config.py y dataclass AnalysisMetrics |
| `080970a` | refactor | Reemplazar 15 print() con logging en módulos internos |
| `789b5dc` | feat | Poblar métricas y mostrar en reportes HTML/JSON |

---

## 16. Fase 10.3 — Optimizaciones de Proyecto

### Contexto

Auditoría completa del proyecto como arquitecto de software Python y evaluador de TFMs. Se identificaron 37 hallazgos en 4 niveles de severidad. La Fase 10.3 corrige los problemas críticos y altos.

---

## 17. Versión Single Source of Truth

```
┌─────────────────────────────────────┐
│  gtaa_validator/__init__.py         │
│  __version__ = "0.10.3"  ← ÚNICA   │
└─────────────┬───────────────────────┘
              │
    ┌─────────┼─────────┬──────────────┐
    ▼         ▼         ▼              ▼
 setup.py  models.py  pyproject.toml  tests/
 (regex)   (import)   (dynamic attr)  (import)
```

---

## 18. Estructura pyproject.toml

```
pyproject.toml
├── [build-system]          → setuptools>=61.0
├── [project]
│   ├── dependencies        → click, PyYAML (core mínimo)
│   └── optional-dependencies
│       ├── ai              → google-genai, python-dotenv
│       ├── parsers         → tree-sitter-language-pack, tree-sitter-c-sharp
│       └── all             → ai + parsers
├── [tool.pytest.ini_options]
│   └── testpaths, markers
└── [tool.coverage]
    ├── run.source          → ["gtaa_validator"]
    └── report.show_missing → true
```

**Instalación:**

| Comando | Dependencias |
|---------|--------------|
| `pip install .` | click + PyYAML |
| `pip install ".[ai]"` | + google-genai + python-dotenv |
| `pip install ".[parsers]"` | + tree-sitter |
| `pip install ".[all]"` | Todo |

---

## 19. Código Muerto Eliminado

| Artefacto | Fichero | Líneas | Reemplazado por |
|-----------|---------|--------|-----------------|
| `BrowserAPICallVisitor` | definition_checker.py | 64 | `_check_browser_calls()` con ParseResult |
| `add_violation()` | definition_checker.py | 33 | Construcción directa de `Violation()` |
| `_HardcodedDataVisitor` | quality_checker.py | 62 | `_check_hardcoded_data()` con ParseResult |
| **Total** | | **159** | |

Además, `checkers/__init__.py` actualizado de 2 → 6 exports:

```python
# Antes (Fase 2):
__all__ = ["BaseChecker", "DefinitionChecker"]

# Después (Fase 10.3):
__all__ = ["BaseChecker", "DefinitionChecker", "StructureChecker",
           "AdaptationChecker", "QualityChecker", "BDDChecker"]
```

---

## 20. Excepciones con Logging

| Fichero | Línea | Nivel | Mensaje |
|---------|-------|-------|---------|
| config.py | 56 | WARNING | Error leyendo config |
| api_client.py | 197 | DEBUG | Error tracking tokens |
| definition_checker.py | 201 | DEBUG | Error checking file |
| quality_checker.py | 174 | DEBUG | Error checking file |
| adaptation_checker.py | 171 | DEBUG | Error checking file |
| bdd_checker.py | 145 | DEBUG | Error reading feature |
| bdd_checker.py | 213 | DEBUG | Error reading step def |
| bdd_checker.py | 342 | DEBUG | Error parsing step patterns |
| gherkin_parser.py | 181 | DEBUG | Error parsing gherkin file |

**Impacto**: Solo observabilidad. El comportamiento funcional (retornar `[]` o `None`) no cambia.

---

## 21. Tests Añadidos en Fase 10.3

| Fichero | Tests | Módulo cubierto | Herramienta |
|---------|-------|-----------------|-------------|
| `test_cli.py` | 6 | `__main__.py` | Click CliRunner |
| `test_prompts.py` | 8 | `llm/prompts.py` | pytest directo |
| **Total** | **14** | | |

Tests totales: 402 → 416

---

## 22. Commits en Fase 10.3

| Commit | Tipo | Descripción |
|--------|------|-------------|
| `b8440d6` | fix | Version bump a 0.10.3 con single source of truth |
| `304dd62` | refactor | pyproject.toml y modernización de packaging |
| `1456bc8` | refactor | Eliminar 159 líneas de código muerto, actualizar exports |
| `21a2ac3` | fix | Logging en 10 bloques de excepciones silenciosas |
| `49cd9fd` | fix | Eliminar ast.Str deprecado, alinear LSP en BaseChecker |
| `93815f4` | test | 14 tests nuevos para CLI y prompts |
| `a254026` | docs | ADRs 45-50, diagramas de flujo, actualización README |
| `4f8c213` | style | PEP 8 E402 import order, docstrings consistentes |

---

## 23. Correcciones PEP 8 E402 y Docstrings

Ficheros corregidos para cumplimiento PEP 8 E402 (logger entre imports):

| Fichero | Antes | Después |
|---------|-------|---------|
| `static_analyzer.py` | `logger` entre `models` y `checkers` imports | `logger` después de todos los imports |
| `semantic_analyzer.py` | `logger` entre `models` y `llm` imports | `logger` después de todos los imports |
| `bdd_checker.py` | `logger` entre `typing` y `checkers` imports | `logger` después de todos los imports |
| `api_client.py` | `logger` + `RateLimitError` entre imports | Ambos después de todos los imports |

Correcciones de docstrings y referencias:

| Fichero | Cambio |
|---------|--------|
| `analyzers/__init__.py` | Docstring inglés → español |
| `checkers/base.py` | Eliminadas refs "Fase 2/3", añadido BDDChecker |
| `static_analyzer.py` | "archivos Python" → "archivos del proyecto (Python, Java, JS/TS, C#, Gherkin)" |
| `__main__.py` | Cabecera CLI sin referencia a fase específica |

---

## 24. Fase 10.4 — Despliegue

La Fase 10.4 añade tres vectores de distribución al proyecto, permitiendo su uso como paquete pip, contenedor Docker o GitHub Action reutilizable.

## 25. Docker Multistage Build

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKERFILE MULTISTAGE                         │
└─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  STAGE 1: builder (python:3.12-slim)                        │
  │                                                             │
  │  1. apt-get install gcc build-essential                     │
  │     └── Necesario para compilar tree-sitter (C nativo)      │
  │                                                             │
  │  2. pip install build wheel                                 │
  │                                                             │
  │  3. COPY pyproject.toml setup.py gtaa_validator/            │
  │                                                             │
  │  4. pip wheel --wheel-dir /wheels ".[all]"                  │
  │     └── Genera .whl para: click, PyYAML, google-genai,     │
  │         python-dotenv, tree-sitter-language-pack,           │
  │         tree-sitter-c-sharp, gtaa-ai-validator              │
  │                                                             │
  │  Resultado: /wheels/*.whl (todas las dependencias)          │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             │ COPY --from=builder /wheels
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STAGE 2: runtime (python:3.12-slim)                        │
  │                                                             │
  │  1. pip install /tmp/wheels/*                               │
  │     └── Instala todos los wheels (sin gcc, sin cache)       │
  │                                                             │
  │  2. ENV GEMINI_API_KEY=""                                   │
  │     └── Pasar en runtime: docker run -e GEMINI_API_KEY=key  │
  │                                                             │
  │  3. WORKDIR /project                                        │
  │     └── Punto de montaje del proyecto del usuario           │
  │                                                             │
  │  4. ENTRYPOINT ["gtaa-validator"]                           │
  │  5. CMD ["."]                                               │
  │     └── Analiza /project (volumen montado) por defecto      │
  │                                                             │
  │  Imagen final: ~150MB (sin gcc, sin build tools)            │
  └─────────────────────────────────────────────────────────────┘

  Uso:
  ┌─────────────────────────────────────────────────────────────┐
  │  docker build -t gtaa-validator .                           │
  │  docker run -v ./mi-proyecto:/project gtaa-validator        │
  │  docker run -v ./mi-proyecto:/project gtaa-validator \      │
  │      . --verbose --ai --provider mock                       │
  │  docker run -e GEMINI_API_KEY=key \                         │
  │      -v ./mi-proyecto:/project gtaa-validator . --ai        │
  └─────────────────────────────────────────────────────────────┘
```

## 26. GitHub Actions CI + Reusable Action

```
┌─────────────────────────────────────────────────────────────────┐
│              CI PIPELINE (.github/workflows/ci.yml)              │
└─────────────────────────────────────────────────────────────────┘

  push/PR a main
       │
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Matrix: Python 3.10, 3.11, 3.12                            │
  │  runs-on: ubuntu-latest                                     │
  │                                                             │
  │  1. actions/checkout@v4                                     │
  │  2. actions/setup-python@v5 (con cache pip)                 │
  │  3. pip install -e ".[all,dev]"                             │
  │  4. pytest tests/ -v --tb=short                             │
  │  5. gtaa-validator examples/bad_project --json              │
  │  6. gtaa-validator examples/good_project --json             │
  │  7. python -m build (solo Python 3.12)                      │
  └─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│           REUSABLE ACTION (action.yml — composite)              │
└─────────────────────────────────────────────────────────────────┘

  Proyecto externo
       │
       │  uses: Membrive92/gtaa-ai-validator@main
       │  with:
       │    project_path: ./tests
       │    verbose: true
       │
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  1. setup-python (versión configurable)                     │
  │  2. pip install "${{ github.action_path }}[all]"            │
  │  3. gtaa-validator $project --json --html                   │
  │     └── Opciones condicionales: --verbose, --ai, --provider │
  │  4. Extraer score del JSON:                                 │
  │     └── data['summary']['score']                            │
  │     └── data['summary']['total_violations']                 │
  │  5. Upload artifacts (JSON + HTML, 30 días)                 │
  └─────────────────────────────────────────────────────────────┘
       │
       ▼
  Outputs: score (0-100), violations (int), report_json (path)
```

## 27. Comparativa de Vectores de Despliegue

| Vector | Comando | Dependencias | Caso de uso |
|--------|---------|-------------|-------------|
| **pip install** | `pip install gtaa-ai-validator[all]` | Python 3.10+ | Desarrollo local, uso directo |
| **Docker** | `docker run -v ./proyecto:/project gtaa-validator` | Docker | Entorno aislado, sin Python |
| **GitHub Action** | `uses: Membrive92/gtaa-ai-validator@main` | Ninguna (action instala) | CI/CD automatizado |

## 28. Commits en Fase 10.4

| Commit | Tipo | Descripción |
|--------|------|-------------|
| `a20ff12` | feat | Dockerfile multistage + .dockerignore + fix build-backend |
| `0717d34` | feat | GitHub Actions CI + reusable composite action |

---

## 29. Fase 10.8 — Refactor SOLID/DRY

### Contexto

Auditoría completa del codebase como arquitecto Python identificó duplicaciones críticas, violaciones SOLID y código muerto. La Fase 10.8 corrige estos problemas en 6 commits independientes (5 de código + 1 de documentación).

---

## 30. Utilidades Compartidas (DRY)

### 30.1 Antes: Duplicación en 3 Conceptos

```
┌──────────────────────────────────────────────────────────┐
│  DUPLICACIÓN 1: get_score_label()                         │
├──────────────────────────────────────────────────────────┤
│  __main__.py      →  if/elif inline (~8 líneas)          │
│  html_reporter.py →  _get_score_label() privado (~8 lín) │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  DUPLICACIÓN 2: safe_relative_path()                      │
├──────────────────────────────────────────────────────────┤
│  models.py:Violation.to_dict()  →  try/except inline     │
│  __main__.py:_display_results() →  try/except inline     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  DUPLICACIÓN 3: EXCLUDED_DIRS                             │
├──────────────────────────────────────────────────────────┤
│  static_analyzer.py   →  11 entradas (parcial)           │
│  semantic_analyzer.py →   9 entradas (parcial)           │
│  Superset real:       →  14 entradas                     │
└──────────────────────────────────────────────────────────┘
```

### 30.2 Después: Single Source of Truth

```
┌─────────────────────────────────────────────────────────────┐
│                  UBICACIÓN CENTRALIZADA                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  models.py                                                   │
│  └── get_score_label(score) → str                           │
│      ├── Importado en __main__.py                           │
│      └── Importado en html_reporter.py                      │
│                                                             │
│  file_utils.py                                               │
│  └── safe_relative_path(file_path, base_path) → Path        │
│      ├── Importado en models.py:Violation.to_dict()         │
│      └── Importado en __main__.py:_display_results()        │
│                                                             │
│  config.py                                                   │
│  └── EXCLUDED_DIRS: Set[str]  (14 entradas, superset)       │
│      ├── Importado en static_analyzer.py                    │
│      └── Importado en semantic_analyzer.py                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 31. Código Muerto Eliminado (Fase 10.8)

```
┌──────────────────────────────────────────────────────────────┐
│  ARTEFACTOS ELIMINADOS                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  file_classifier.py                                           │
│  └── _analyze_imports()          ~24 líneas (legacy Fase 9)  │
│                                                              │
│  definition_checker.py                                        │
│  └── self.violations             campo no usado              │
│  └── self.current_file           campo no usado              │
│                                                              │
│  treesitter_base.py                                           │
│  └── ParsedFunction.body_node    campo no usado              │
│  └── import Set                  import no usado             │
│                                                              │
│  java_parser.py / js_parser.py / csharp_parser.py            │
│  └── body_node=...              asignaciones al campo muerto │
│                                                              │
│  test_classifier.py                                           │
│  └── TestLegacyAnalyzeImports   3 tests de método eliminado  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Resultado: 672 tests → 669 tests (3 legacy eliminados)      │
└──────────────────────────────────────────────────────────────┘
```

---

## 32. Métodos Compartidos en BaseChecker

### 32.1 Antes: Duplicación en Checkers

```
┌─────────────────────────────────────────────────────────────┐
│  DefinitionChecker                                           │
│  ├── _is_test_file()          ~25 líneas                    │
│  ├── _is_test_function()      ~15 líneas                    │
│  ├── _get_browser_methods()   if/elif (4 ramas)             │
│  └── _get_browser_objects()   if/elif (4 ramas)             │
├─────────────────────────────────────────────────────────────┤
│  QualityChecker                                              │
│  ├── _is_test_file()          ~25 líneas (DUPLICADO)        │
│  ├── _is_test_function()      ~15 líneas (DUPLICADO)        │
│  └── _get_generic_name_pattern() if/elif (4 ramas)          │
├─────────────────────────────────────────────────────────────┤
│  AdaptationChecker                                           │
│  ├── _get_forbidden_modules()  if/elif (4 ramas)            │
│  └── _get_assertion_methods()  if/elif (4 ramas)            │
├─────────────────────────────────────────────────────────────┤
│  TOTAL duplicación: ~100 líneas redundantes                  │
└─────────────────────────────────────────────────────────────┘
```

### 32.2 Después: Herencia con Template Method

```
┌─────────────────────────────────────────────────────────────┐
│  BaseChecker (clase base)                                    │
│  ├── _JS_EXTENSIONS = frozenset({".js", ".ts", ...})        │
│  ├── _SUPPORTED_EXTENSIONS = frozenset({".py", ".java", ..})│
│  ├── _is_test_file(file_path) → bool                        │
│  ├── _is_test_function(func, extension) → bool              │
│  └── _get_config_for_extension(ext, config_map) → value     │
├─────────────────────────────────────────────────────────────┤
│  DefinitionChecker(BaseChecker)                              │
│  ├── can_check() → self._is_test_file()   (delega)         │
│  ├── _get_browser_methods() → _get_config_for_extension()   │
│  └── _get_browser_objects() → _get_config_for_extension()   │
├─────────────────────────────────────────────────────────────┤
│  QualityChecker(BaseChecker)                                 │
│  ├── can_check() → self._is_test_file()   (delega)         │
│  └── _get_generic_name_pattern() → _get_config_for_extension│
├─────────────────────────────────────────────────────────────┤
│  AdaptationChecker(BaseChecker)                              │
│  ├── can_check()  (lógica propia — Page Objects)            │
│  ├── _get_forbidden_modules() → _get_config_for_extension() │
│  └── _get_assertion_methods() → _get_config_for_extension() │
└─────────────────────────────────────────────────────────────┘
```

### 32.3 Patrón _get_config_for_extension

```
_get_config_for_extension(".ts", config_map)
                    │
                    ▼
        ┌──────────────────────┐
        │ ext = "ts"           │
        │ → normalizar a "js"  │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ config_map = {       │
        │   "py":   PYTHON_SET │
        │   "java": JAVA_SET   │
        │   "js":   JS_SET     │
        │   "cs":   CSHARP_SET │
        │ }                    │
        └──────────┬───────────┘
                   │
                   ▼
            return JS_SET
```

---

## 33. LLMClientProtocol y TokenUsage Unificado

### 33.1 Antes: Duplicación en Capa LLM

```
┌─────────────────────────────────────────────────────────────┐
│  client.py (MockLLMClient)                                   │
│  └── class MockTokenUsage:                                   │
│      ├── input_tokens, output_tokens                        │
│      ├── total_calls                                         │
│      ├── estimated_cost_usd = 0.0  (hardcoded)              │
│      └── to_dict(), __str__()                                │
├─────────────────────────────────────────────────────────────┤
│  api_client.py (APILLMClient)                                │
│  └── class TokenUsage:                                       │
│      ├── input_tokens, output_tokens                        │
│      ├── total_calls                                         │
│      ├── estimated_cost_usd  (calculado con precios)        │
│      └── to_dict(), __str__()                                │
├─────────────────────────────────────────────────────────────┤
│  factory.py                                                  │
│  └── return type: Union[MockLLMClient, APILLMClient]        │
├─────────────────────────────────────────────────────────────┤
│  semantic_analyzer.py                                        │
│  ├── try: llm_client.analyze_file(...)                      │
│  │   except RateLimitError: _fallback_to_mock()             │
│  │   → llm_client.analyze_file(...)        (DUPLICADO)      │
│  └── try: llm_client.enrich_violation(...)                  │
│      except RateLimitError: _fallback_to_mock()             │
│      → llm_client.enrich_violation(...)    (DUPLICADO)      │
└─────────────────────────────────────────────────────────────┘
```

### 33.2 Después: Protocol + TokenUsage Unificado

```
┌─────────────────────────────────────────────────────────────┐
│  protocol.py (NUEVO)                                         │
│  ├── @dataclass TokenUsage:                                  │
│  │   ├── input_tokens, output_tokens, total_calls           │
│  │   ├── cost_per_million_input: float = 0.0                │
│  │   ├── cost_per_million_output: float = 0.0               │
│  │   └── to_dict(), __str__(), add(), properties            │
│  │                                                           │
│  └── @runtime_checkable                                      │
│      class LLMClientProtocol(Protocol):                      │
│          usage: TokenUsage                                    │
│          def analyze_file(...) → List[dict]                  │
│          def enrich_violation(...) → str                     │
│          def get_usage_summary() → str                       │
│          def get_usage_dict() → dict                         │
├─────────────────────────────────────────────────────────────┤
│  client.py                                                   │
│  └── MockLLMClient:                                          │
│      └── self.usage = TokenUsage()  (coste 0 por defecto)   │
├─────────────────────────────────────────────────────────────┤
│  api_client.py                                               │
│  └── APILLMClient:                                           │
│      └── self.usage = TokenUsage(                            │
│              cost_per_million_input=0.075,                   │
│              cost_per_million_output=0.30)                   │
├─────────────────────────────────────────────────────────────┤
│  factory.py                                                  │
│  └── return type: LLMClientProtocol  (no Union)             │
├─────────────────────────────────────────────────────────────┤
│  semantic_analyzer.py                                        │
│  └── _call_with_fallback(method_name, *args, **kwargs):     │
│      try: getattr(llm_client, method_name)(*args, **kwargs) │
│      except RateLimitError: _fallback_to_mock(); retry      │
└─────────────────────────────────────────────────────────────┘
```

### 33.3 Jerarquía de Clases Actualizada

```
                    ┌─────────────────────────┐
                    │  LLMClientProtocol       │  (typing.Protocol)
                    │  @runtime_checkable      │
                    │                          │
                    │  + usage: TokenUsage     │
                    │  + analyze_file()        │
                    │  + enrich_violation()    │
                    │  + get_usage_summary()   │
                    │  + get_usage_dict()      │
                    └─────────────────────────┘
                              ▲
                              │ (duck typing estructural)
                              │
              ┌───────────────┴───────────────┐
              │                               │
    ┌─────────────────┐            ┌─────────────────┐
    │  MockLLMClient  │            │  APILLMClient    │
    │                 │            │                  │
    │  TokenUsage()   │            │  TokenUsage(     │
    │  (coste = 0)    │            │    input=0.075,  │
    │                 │            │    output=0.30)  │
    └─────────────────┘            └─────────────────┘
```

---

## 34. Descomposición del CLI

### 34.1 Antes: main() Monolítico (~200 líneas)

```
def main(project_path, verbose, json_path, html_path, ai, provider, ...):
    ┌────────────────────────────────┐
    │  Setup (logging, config)       │  ~15 líneas
    ├────────────────────────────────┤
    │  Análisis estático             │  ~10 líneas
    ├────────────────────────────────┤
    │  Análisis semántico AI         │  ~20 líneas
    ├────────────────────────────────┤
    │  Display de resultados         │  ~40 líneas
    ├────────────────────────────────┤
    │  Cálculo de métricas           │  ~20 líneas
    ├────────────────────────────────┤
    │  Generación de reportes        │  ~30 líneas
    ├────────────────────────────────┤
    │  Display de resumen LLM        │  ~20 líneas
    ├────────────────────────────────┤
    │  Resumen final + exit code     │  ~10 líneas
    └────────────────────────────────┘
    TOTAL: ~200 líneas, 6 responsabilidades mezcladas
```

### 34.2 Después: main() como Orquestador (~50 líneas)

```
__main__.py:

┌──────────────────────────────────────────────────────────────┐
│  _run_static_analysis(project_path, verbose, config)         │
│  → (report, elapsed_seconds)                                 │
├──────────────────────────────────────────────────────────────┤
│  _run_semantic_analysis(project_path, report, provider,      │
│                         verbose, max_llm_calls)              │
│  → (report, semantic, elapsed_seconds)                       │
├──────────────────────────────────────────────────────────────┤
│  _display_results(report, project_path, verbose)             │
│  → severity_counts                                           │
├──────────────────────────────────────────────────────────────┤
│  _build_metrics(report, semantic, static_secs,               │
│                 semantic_secs, total_start)                   │
│  → AnalysisMetrics                                           │
├──────────────────────────────────────────────────────────────┤
│  _generate_reports(report, metrics, json_path, html_path,    │
│                    output_dir, no_report, project_path)       │
│  → (json_path, html_path)                                    │
├──────────────────────────────────────────────────────────────┤
│  _display_llm_summary(report, semantic)                      │
│  → None                                                      │
└──────────────────────────────────────────────────────────────┘

main() orquestador (~50 líneas):
    setup → _run_static_analysis → _run_semantic_analysis (si --ai)
         → _display_results → _build_metrics → _generate_reports
         → _display_llm_summary → exit code
```

### 34.3 Flujo E2E con Funciones Extraídas

```
python -m gtaa_validator ./proyecto --ai --verbose
                    │
                    ▼
            main() [orquestador]
                    │
        ┌───────────┴───────────┐
        │ setup_logging()       │
        │ load_config()         │
        └───────────┬───────────┘
                    │
                    ▼
    ┌──────────────────────────────┐
    │ _run_static_analysis()       │
    │  └── StaticAnalyzer.analyze()│
    │  → (report, 0.45s)          │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ _run_semantic_analysis()     │
    │  ├── create_llm_client()    │
    │  └── SemanticAnalyzer       │
    │      .analyze(report)       │
    │  → (report, semantic, 2.1s) │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ _display_results()           │
    │  └── Mostrar violaciones     │
    │  → severity_counts           │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ _build_metrics()             │
    │  └── AnalysisMetrics(...)    │
    │  → metrics                   │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ _generate_reports()          │
    │  ├── JsonReporter.generate() │
    │  └── HtmlReporter.generate() │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ _display_llm_summary()       │
    │  └── Tokens, costo, provider │
    └──────────────┬───────────────┘
                   │
                   ▼
            exit code (0 o 1)
```

---

## 35. Estructura de Archivos Después de Fase 10.8

```
gtaa_validator/
├── __main__.py                # MODIFICADO: 6 funciones extraídas de main()
├── models.py                  # MODIFICADO: +get_score_label(), usa safe_relative_path
├── file_utils.py              # MODIFICADO: +safe_relative_path()
├── config.py                  # MODIFICADO: +EXCLUDED_DIRS centralizado
│
├── analyzers/
│   ├── static_analyzer.py     # MODIFICADO: importa EXCLUDED_DIRS de config
│   └── semantic_analyzer.py   # MODIFICADO: +_call_with_fallback(), importa EXCLUDED_DIRS,
│                              #             tipo LLMClientProtocol
│
├── checkers/
│   ├── base.py                # MODIFICADO: +_is_test_file(), +_is_test_function(),
│   │                          #             +_get_config_for_extension()
│   ├── definition_checker.py  # MODIFICADO: usa BaseChecker methods, -self.violations
│   ├── quality_checker.py     # MODIFICADO: usa BaseChecker methods
│   └── adaptation_checker.py  # MODIFICADO: usa _get_config_for_extension()
│
├── llm/
│   ├── __init__.py            # MODIFICADO: exporta LLMClientProtocol, TokenUsage
│   ├── protocol.py            # NUEVO: TokenUsage unificado, LLMClientProtocol
│   ├── client.py              # MODIFICADO: usa TokenUsage de protocol
│   ├── api_client.py          # MODIFICADO: usa TokenUsage de protocol
│   └── factory.py             # MODIFICADO: retorna LLMClientProtocol
│
├── parsers/
│   ├── treesitter_base.py     # MODIFICADO: -body_node, -import Set
│   ├── java_parser.py         # MODIFICADO: -body_node assignments
│   ├── js_parser.py           # MODIFICADO: -body_node assignments
│   └── csharp_parser.py       # MODIFICADO: -body_node assignments
│
└── reporters/
    └── html_reporter.py       # MODIFICADO: importa get_score_label
```

---

## 36. Resumen de Principios Aplicados en Fase 10.8

| Principio | Aplicación | Resultado |
|-----------|-----------|-----------|
| **DRY** | Extraer utilidades compartidas, unificar TokenUsage | Eliminar duplicación en 6+ módulos |
| **SRP** | Descomponer main() en 6 funciones | Cada función, una responsabilidad |
| **DIP** | LLMClientProtocol (Protocol) | Factory retorna abstracción, no tipos concretos |
| **OCP** | _get_config_for_extension con dict | Añadir lenguaje sin modificar método |
| **Template Method** | Métodos concretos en BaseChecker | Subclases delegan detección de tests a la base |
| **Extract Method** | 6 funciones de main(), _call_with_fallback | Código más legible y testeable |
| **Dead Code Elimination** | 65 líneas + 3 tests eliminados | Codebase más limpio y mantenible |

---

## 37. Commits en Fase 10.8

| Commit | Tipo | Descripción |
|--------|------|-------------|
| `fe51635` | refactor | Extraer utilidades compartidas (score label, relative path, excluded dirs) |
| `b8ed7b5` | refactor | Eliminar código muerto e imports no usados |
| `1de91be` | refactor | Extraer métodos compartidos a BaseChecker |
| `0799bbe` | refactor | Añadir Protocol, unificar TokenUsage, extraer fallback helper |
| `24a9720` | refactor | Descomponer main() en funciones auxiliares |
| `ec834fb` | docs | Actualizar README con Fase 10.8 |

Tests totales: 672 → 669 (3 legacy eliminados, todos pasan).

> **Nota**: Tras la Fase 10.9 (auditoría QA), el total pasó a **761 tests**. Ver [TEST_AUDIT_REPORT.md](TEST_AUDIT_REPORT.md) para el detalle.

---

*Última actualización: 10 de febrero de 2026 (Fase 10 Completa — UAT Completado)*
