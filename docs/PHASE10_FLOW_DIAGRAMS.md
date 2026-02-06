# Fase 10 - Optimización de la Capa LLM

## Resumen General

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
|  - llm_client: Union[MockLLMClient, APILLMClient]                 |
|  - max_llm_calls: Optional[int]                                   |
|  - _initial_provider: str                                         |
|  - _current_provider: str                                         |
|  - _fallback_occurred: bool                                       |
|  - _llm_call_count: int                                           |
+------------------------------------------------------------------+
```

### 1.2 Jerarquía de Clases de Cliente LLM

```
                    +-------------------+
                    |   Protocolo LLM   |  (Duck typing)
                    |                   |
                    | + analyze_file()  |
                    | + enrich_violation() |
                    +-------------------+
                            ^
                            |
           +----------------+----------------+
           |                                 |
+-------------------+            +-------------------+
|  MockLLMClient    |            |  APILLMClient     |
|                   |            |                   |
| Basado en         |            | Basado en API     |
| heurísticas       |            | Gemini            |
| Sin llamadas API  |            | Requiere API key  |
| Siempre disponible|            | Con rate limit    |
+-------------------+            +-------------------+
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

def create_llm_client(provider: str = None) -> Union[MockLLMClient, APILLMClient]:
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
│   │                        #          RateLimitError, create_llm_client
│   ├── client.py            # MockLLMClient (heurísticas)
│   ├── api_client.py        # APILLMClient + RateLimitError
│   ├── factory.py           # create_llm_client(), get_available_providers()
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

*Última actualización: 5 de febrero de 2026*
