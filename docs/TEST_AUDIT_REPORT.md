# Auditoría QA — Suite de Tests gTAA AI Validator

> **Fase 10.9** | Fecha: 2026-02-06
> **Metodología**: Auditoría white-box completa
> **Auditor**: QA Specialist (caja blanca, casos límite, integración, E2E)

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos de test | 32 |
| Tests totales | 670 (pytest --co) |
| Tests a eliminar | 11 (redundantes/muertos) |
| Funciones con zero cobertura | 8 (críticas) |
| Tests a añadir | ~86+ (priorizados) |
| Issues de calidad | 81 (aserciones débiles) |
| Fixtures duplicadas | 6 |
| Helpers duplicados | 3 (misma función en 3 ficheros) |

### Distribución actual por fichero

| Fichero | Tests |
|---------|-------|
| `tests/unit/test_classifier.py` | 85 |
| `tests/unit/test_quality_checker.py` | 61 |
| `tests/unit/test_definition_checker.py` | 54 |
| `tests/unit/test_python_parser.py` | 54 |
| `tests/unit/test_js_checker.py` | 52 |
| `tests/unit/test_csharp_checker.py` | 37 |
| `tests/unit/test_llm_client.py` | 36 |
| `tests/unit/test_security.py` | 34 |
| `tests/unit/test_models.py` | 32 |
| `tests/unit/test_java_checker.py` | 30 |
| `tests/unit/test_bdd_checker.py` | 28 |
| `tests/unit/test_cli.py` | 25 |
| `tests/unit/test_adaptation_checker.py` | 25 |
| `tests/unit/test_api_client.py` | 19 |
| `tests/unit/test_semantic_analyzer.py` | 19 |
| `tests/unit/test_html_reporter.py` | 18 |
| `tests/unit/test_llm_factory.py` | 16 |
| `tests/unit/test_gherkin_parser.py` | 15 |
| `tests/unit/test_structure_checker.py` | 11 |
| `tests/unit/test_prompts.py` | 10 |
| `tests/unit/test_config.py` | 10 |
| `tests/unit/test_json_reporter.py` | 9 |
| `tests/unit/test_logging_config.py` | 9 |
| `tests/unit/test_base_checker.py` | 6 |
| `tests/unit/test_file_utils.py` | 6 |
| `tests/integration/test_static_analyzer.py` | 18 |
| `tests/integration/test_semantic_integration.py` | 6 |
| `tests/integration/test_reporters.py` | 4 |

---

## 2. Tests a Eliminar (11)

### 2.1 Tests redundantes

| # | Fichero | Test | Razón |
|---|---------|------|-------|
| 1 | `test_models.py` | `test_sorting_severities` | Duplica lógica ya cubierta por `test_ordering_preserves_severity` |
| 2 | `test_file_utils.py` | `test_default_max_size_is_10mb` | Verifica constante — no es comportamiento, es implementación |
| 3 | `test_cli.py` | `test_score_displayed` | Subconjunto de `test_output_format` que ya verifica score |
| 4 | `test_base_checker.py` | `test_str_format` | Duplica `test_repr_format` (ambos cubren `__str__`/`__repr__`) |
| 5 | `test_definition_checker.py` | `test_default_file_type_detects_violations` | Idéntico a `test_unknown_file_detects_violations` — mismo input/output |
| 6 | `test_definition_checker.py` | `test_unknown_file_detects_violations` | Duplicado del anterior |
| 7 | `test_api_client.py` | `test_valid_types_includes_aaa` | Verifica contenido de constante, no comportamiento |
| 8 | `test_api_client.py` | `test_valid_types_includes_mixed_abstraction` | Verifica contenido de constante, no comportamiento |
| 9 | `test_llm_factory.py` | `test_env_provider_used` | Duplica `test_mock_from_env` con setup casi idéntico |
| 10 | `test_llm_factory.py` | `test_invalid_provider_lists_options` | Near-duplicate de `test_invalid_provider_raises` |
| 11 | `test_js_checker.py` | `test_detects_expect_in_page` | Dead code — `@pytest.mark.skip` permanente (línea 217) |

### 2.2 Criterios de eliminación

- **Redundancia**: Test A y Test B ejercitan exactamente el mismo path de código
- **Verificación de constantes**: Testear que una constante tiene un valor fijo no aporta valor
- **Dead code**: Tests permanentemente deshabilitados con `@pytest.mark.skip` sin plan de habilitación

---

## 3. Funciones con Zero Cobertura (8 Críticas)

### 3.1 CRITICAL — Lógica de negocio compartida sin tests

| # | Módulo | Función/Método | Líneas | Impacto |
|---|--------|----------------|--------|---------|
| 1 | `checkers/base.py:121-155` | `_is_test_file()` | 35 | Determina si un archivo es test. Usado por DefinitionChecker y QualityChecker. Soporta 4 lenguajes (Python, Java, JS/TS, C#). **Sin ningún test directo.** |
| 2 | `checkers/base.py:157-169` | `_is_test_function()` | 12 | Identifica funciones de test por convenciones de cada lenguaje. **Sin ningún test directo.** |
| 3 | `checkers/base.py:171-185` | `_get_config_for_extension()` | 6 | Dispatch de extensión a configuración. Mapea JS/TS variantes a "js". **Sin ningún test directo.** |
| 4 | `file_utils.py:47-62` | `safe_relative_path()` | 15 | Relativiza rutas de forma segura (SEC-03). Catch de ValueError. **Sin ningún test.** |
| 5 | `llm/protocol.py:12-62` | `TokenUsage` (dataclass completa) | 50 | Tracking de consumo de tokens LLM. Métodos: `add()`, `total_tokens`, `estimated_cost_usd`, `to_dict()`, `__str__()`. **Fichero entero sin tests.** |
| 6 | `llm/protocol.py:65-84` | `LLMClientProtocol` | 20 | Protocol `@runtime_checkable`. Define interfaz del cliente LLM. **Sin tests de conformancia.** |
| 7 | `llm/client.py:365-412` | `_check_step_def_direct_browser()` | 48 | Detecta llamadas directas a browser en step definitions BDD. **~48 líneas de producción sin ningún test.** |
| 8 | `llm/client.py:415-454` | `_check_step_def_too_complex()` | 40 | Detecta step definitions que exceden 15 líneas. **~40 líneas de producción sin ningún test.** |

### 3.2 Análisis de riesgo

- `_is_test_file()` y `_is_test_function()` son **la base de la clasificación** — un bug aquí causa falsos negativos en todos los checkers
- `safe_relative_path()` es relevante para **seguridad (SEC-03)** — path traversal
- `TokenUsage` es el **tracking financiero** de uso de API — errores en `estimated_cost_usd` causan reportes de costos incorrectos
- Los métodos BDD representan **~88 líneas de heurísticas** completamente sin verificar

---

## 4. Tests a Añadir (Priorizados)

### 4.1 CRITICAL — Zero coverage a covered (~43 tests)

#### `tests/unit/test_base_checker.py` — ~25 tests nuevos

**`TestIsTestFile`** (14 tests):
| Input | Extension | Esperado | Branch |
|-------|-----------|----------|--------|
| `test_login.py` | `.py` | `True` | `filename.startswith("test_")` |
| `login_test.py` | `.py` | `True` | `filename.endswith("_test.py")` |
| `tests/helpers.py` | `.py` | `True` | `"tests" in parts` |
| `utils/helper.py` | `.py` | `False` | Ningún patrón match |
| `LoginTest.java` | `.java` | `True` | `"test" in filename` |
| `Login.java` | `.java` | `False` | No contiene "test" |
| `login.spec.ts` | `.ts` | `True` | `".spec." in filename` |
| `login.test.js` | `.js` | `True` | `".test." in filename` |
| `__tests__/helper.js` | `.js` | `True` | `"__tests__" in parts` |
| `app.js` | `.js` | `False` | Ningún patrón match |
| `LoginTest.cs` | `.cs` | `True` | `"test" in filename` |
| `Login.cs` | `.cs` | `False` | No contiene "test" |
| `script.rb` | `.rb` | `False` | Extension no soportada |
| `README.md` | `.md` | `False` | Extension no soportada |

**`TestIsTestFunction`** (7 tests):
| Función | Extension | Esperado | Branch |
|---------|-----------|----------|--------|
| `test_foo` | `.py` | `True` | `name.startswith("test_")` |
| `helper_func` | `.py` | `False` | No empieza con "test_" |
| `@Test method` | `.java` | `True` | `"Test" in decorators` |
| `@Override method` | `.java` | `False` | No es annotation de test |
| `@Fact method` | `.cs` | `True` | `"Fact" in decorators` |
| `@Theory method` | `.cs` | `True` | `"Theory" in decorators` |
| `it("should...")` | `.js` | `True` | `name in {"it", "test"}` |

**`TestGetConfigForExtension`** (4 tests):
| Extension | config_map | Esperado |
|-----------|-----------|----------|
| `.py` | `{"py": "val"}` | `"val"` |
| `.ts` | `{"js": "val"}` | `"val"` (normalizado) |
| `.java` | `{"java": "val"}` | `"val"` |
| `.unknown` | `{"default": "d"}` | `"d"` |
| `.unknown` | `{}` (sin default) | `set()` |

**`test_cannot_instantiate_base_directly`** — `TypeError` al instanciar ABC

#### `tests/unit/test_file_utils.py` — ~6 tests nuevos

| Test | Descripción | Branch cubierto |
|------|-------------|-----------------|
| `test_path_within_base` | `safe_relative_path(base/sub/f.py, base)` → `sub/f.py` | Happy path |
| `test_path_outside_base` | `safe_relative_path(/other/f.py, /base)` → `/other/f.py` | `except ValueError` |
| `test_identical_paths` | `safe_relative_path(base, base)` → `.` | Edge case |
| `test_file_at_exact_size_limit` | Archivo de exactamente `MAX_FILE_SIZE_BYTES` | Boundary `>` (no `>=`) |
| `test_nonexistent_file_returns_empty` | Ruta que no existe → `""` | `except OSError` en `open()` |
| `test_unicode_file_content` | Contenido con caracteres no-ASCII | `errors="replace"` |

#### `tests/unit/test_llm_protocol.py` — NUEVO (~12 tests)

| Test | Descripción |
|------|-------------|
| `test_token_usage_defaults` | Todos los campos inician en 0 |
| `test_add_increments_tokens` | `add(10, 20)` → `input=10, output=20, calls=1` |
| `test_add_multiple_accumulates` | 3x `add()` → suma correcta, `calls=3` |
| `test_total_tokens_property` | `input + output` |
| `test_estimated_cost_zero_pricing` | `cost_per_million = 0` → `$0.0` |
| `test_estimated_cost_api_pricing` | Cálculo con precios reales de Gemini |
| `test_to_dict_keys` | Contiene todas las claves esperadas |
| `test_to_dict_values` | Valores coinciden con estado interno |
| `test_str_mock_format` | `total_calls=0` → formato sin costo |
| `test_str_api_format` | `total_calls>0` → formato con costo |
| `test_protocol_mock_client` | `isinstance(MockLLMClient(), LLMClientProtocol)` → `True` |
| `test_protocol_api_client` | `isinstance(APILLMClient(key), LLMClientProtocol)` → `True` |

---

### 4.2 HIGH — Lógica de negocio con cobertura parcial (~30 tests)

#### `tests/unit/test_models.py` — ~10 tests

| Test | Descripción |
|------|-------------|
| `test_score_label_100` | `get_score_label(100)` → `"EXCELENTE"` |
| `test_score_label_90` | `get_score_label(90)` → `"EXCELENTE"` (boundary) |
| `test_score_label_89_9` | `get_score_label(89.9)` → `"BUENO"` (boundary) |
| `test_score_label_75` | `get_score_label(75)` → `"BUENO"` (boundary) |
| `test_score_label_74_9` | `get_score_label(74.9)` → `"NECESITA MEJORAS"` (boundary) |
| `test_score_label_50` | `get_score_label(50)` → `"NECESITA MEJORAS"` (boundary) |
| `test_score_label_49_9` | `get_score_label(49.9)` → `"PROBLEMAS CRÍTICOS"` (boundary) |
| `test_score_label_0` | `get_score_label(0)` → `"PROBLEMAS CRÍTICOS"` |
| `test_violation_to_dict_with_project_path` | `to_dict(project_path=...)` relativiza ruta |
| `test_report_to_dict_llm_provider` | Incluye `llm_provider` en dict |

#### `tests/unit/test_api_client.py` — ~6 tests

| Test | Descripción |
|------|-------------|
| `test_rate_limit_error_on_429` | `analyze_file()` con 429 → `RateLimitError` |
| `test_rate_limit_error_on_enrich` | `enrich_violation()` con 429 → `RateLimitError` |
| `test_is_rate_limit_429_pattern` | `"429"` en error → `True` |
| `test_is_rate_limit_quota_pattern` | `"quota"` en error → `True` |
| `test_is_rate_limit_resource_exhausted` | `"resource exhausted"` → `True` |
| `test_repr_no_exposes_api_key` | `repr(client)` no contiene la key (SEC-04) |

#### `tests/unit/test_llm_client.py` — ~8 tests

| Test | Descripción |
|------|-------------|
| `test_step_def_direct_browser_detected` | Step con `page.click()` → violación |
| `test_step_def_direct_browser_clean` | Step sin browser calls → sin violación |
| `test_step_def_too_complex_detected` | Step >15 líneas → violación |
| `test_step_def_too_complex_clean` | Step ≤15 líneas → sin violación |
| `test_page_object_boundary_10_methods` | POM con 10 métodos → sin violación |
| `test_page_object_boundary_11_methods` | POM con 11 métodos → violación |
| `test_unclear_purpose_boundary_20_chars` | Nombre de 20 chars → sin violación |
| `test_usage_tracking_after_analyze` | `usage.total_calls` incrementa tras análisis |

#### `tests/unit/test_gherkin_parser.py` — ~3 tests

| Test | Descripción |
|------|-------------|
| `test_parse_file_normal` | Archivo `.feature` válido → `GherkinFeature` |
| `test_parse_file_empty` | Archivo vacío → resultado vacío/sin crash |
| `test_parse_file_nonexistent` | Ruta inexistente → error manejado |

#### `tests/unit/test_html_reporter.py` — ~3 tests

| Test | Descripción |
|------|-------------|
| `test_xss_in_code_snippet` | `<script>alert(1)</script>` en snippet → escaped |
| `test_ai_suggestion_rendering` | Sugerencia AI presente en HTML output |
| `test_score_zero_svg` | Score=0 renderiza SVG correctamente |

---

### 4.3 MEDIUM — Completitud y edge cases (~15 tests)

#### `tests/unit/test_semantic_analyzer.py` — 2 tests
- `test_excluded_dirs_filtering` — Directorios excluidos no se analizan
- `test_call_with_fallback_retry_results` — Retry tras fallo retorna resultado

#### `tests/unit/test_json_reporter.py` — 2 tests
- `test_ai_suggestion_in_json_output` — Campo `ai_suggestion` presente en JSON
- `test_llm_provider_in_metadata` — Campo `llm_provider` en metadata

#### `tests/unit/test_definition_checker.py` — 1 test
- `test_nested_browser_call_in_class_method` — Browser call anidado en método de clase

#### `tests/unit/test_quality_checker.py` — 2 tests
- `test_long_function_boundary_50_lines` — Exactamente 50 líneas → sin violación
- `test_long_function_boundary_51_lines` — 51 líneas → violación (boundary)

#### `tests/unit/test_bdd_checker.py` — 3 tests
- `test_detect_css_id_selector_in_feature` — Selector `#id` en `.feature`
- `test_background_implementation_detail` — Detalle de implementación en Background
- `test_empty_feature_file` — Archivo `.feature` vacío

#### `tests/unit/test_static_analyzer.py` — 1 test
- `test_discovers_java_files` — Descubrimiento de archivos `.java`

---

## 5. Issues de Calidad Sistemáticos

### 5.1 Aserciones débiles (40+ tests afectados)

**Patrón**: Usar `assert len(violations) >= 1` en lugar de `assert len(violations) == 1`

**Riesgo**: No detecta regresiones donde un cambio de código introduce violaciones duplicadas o extra.

**Ficheros afectados**:

| Fichero | Tests con `>= 1` o `> 0` | Corrección |
|---------|--------------------------|------------|
| `test_quality_checker.py` | ~15 tests (hardcoded, email, url, phone, password, business logic) | `== 1` con verificación de `violation_type` |
| `test_definition_checker.py` | ~8 tests (find_elements, legacy_find, page_click, page_fill, wait_for) | `== N` con verificación de `violation_type` |
| `test_adaptation_checker.py` | ~5 tests | `== 1` con verificación de `violation_type` |
| `test_java_checker.py` | ~5 tests | `== N` con `violation_type` |
| `test_js_checker.py` | ~4 tests | `== N` con `violation_type` |
| `test_csharp_checker.py` | ~3 tests | `== N` con `violation_type` |

### 5.2 Aserciones débiles — Verificaciones de tipo

**Patrón**: Verificar solo el conteo sin verificar el tipo de violación.

```python
# DÉBIL
assert len(violations) >= 1

# FUERTE
assert len(violations) == 1
assert violations[0].violation_type == ViolationType.HARDCODED_DATA
```

### 5.3 Aserciones débiles — Timestamps y formatos

**Fichero**: `test_models.py`

```python
# DÉBIL
assert "T" in report.timestamp or "-" in report.timestamp

# FUERTE
from datetime import datetime
datetime.fromisoformat(report.timestamp)  # Lanza ValueError si es inválido
```

### 5.4 Aserciones débiles — Poblado automático

**Fichero**: `test_models.py`

```python
# DÉBIL
assert len(violation.message) > 0

# FUERTE
assert violation.message == ViolationType.HARDCODED_DATA.get_description()
```

### 5.5 Missing severity assertions

**Fichero**: `test_bdd_checker.py` — Ningún test verifica `violation.severity`

**Fichero**: `test_structure_checker.py` — `test_missing_page_dir` y `test_missing_both` no verifican el tipo de violación encontrada

---

## 6. Duplicaciones a Limpiar

### 6.1 Fixtures duplicadas

| Fixture | Definida en | También en | Acción |
|---------|-------------|-----------|--------|
| `bad_project_path` | `tests/conftest.py:24` | `test_reporters.py:19`, `test_semantic_integration.py:20` | Eliminar locales, usar conftest |
| `good_project_path` | `tests/conftest.py:30` | `test_reporters.py:25`, `test_semantic_integration.py:26` | Eliminar locales, usar conftest |
| `write_test_file` | — | `test_quality_checker.py:23` | Renombrar a `write_py_file` (usar conftest) |

### 6.2 Helper duplicado `parse_and_check()`

**Definido idénticamente en 3 ficheros**:

| Fichero | Líneas |
|---------|--------|
| `tests/unit/test_java_checker.py` | 29-35 |
| `tests/unit/test_js_checker.py` | 28-34 |
| `tests/unit/test_csharp_checker.py` | 30-36 |

**Acción**: Extraer a `tests/conftest.py` como fixture o helper compartido.

```python
# tests/conftest.py
def parse_and_check(checker, file_path: Path):
    """Helper compartido para parsear archivo y ejecutar checker."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    parser = get_parser_for_file(file_path)
    parse_result = parser.parse(source) if parser else None
    return checker.check(file_path, parse_result)
```

---

## 7. Gaps Cross-Cutting

### 7.1 Security regression tests

| ID | Descripción | Estado |
|----|-------------|--------|
| SEC-03 | `safe_relative_path()` — path traversal | **Sin tests** |
| SEC-04 | `__repr__` de APIClient no expone API key | **Sin tests** |
| SEC-05 | `read_file_safe()` — límite de tamaño | Parcialmente cubierto |
| XSS | HTML reporter escapa `code_snippet` malicioso | **Sin tests** |

### 7.2 Boundary testing ausente

| Función | Threshold | Test boundary |
|---------|-----------|---------------|
| `get_score_label()` | 90, 75, 50 | **Sin tests en los límites** |
| `read_file_safe()` | `MAX_FILE_SIZE_BYTES` | Sin test para `==` vs `>` |
| `_check_step_def_too_complex()` | 15 líneas | **Sin tests** |
| `_check_page_object_does_too_much()` | 10 métodos | **Sin tests** |
| `_check_unclear_test_purpose()` | 20 chars | **Sin tests** |
| Long function detection | 50 líneas | **Sin tests boundary** |

### 7.3 Error handling paths

| Módulo | Error path | Estado |
|--------|------------|--------|
| `api_client.py` | HTTP 429 → `RateLimitError` | **Sin tests** |
| `api_client.py` | `_is_rate_limit_error()` patterns | **Sin tests** |
| `gherkin_parser.py` | `parse_file()` con archivo inexistente | **Sin tests** |
| `gherkin_parser.py` | `parse_file()` con archivo vacío | **Sin tests** |

---

## 8. Plan de Corrección

### Commit 2: Eliminar 11 tests redundantes + limpiar fixtures
- Resultado esperado: 659 tests (670 - 11)

### Commit 3: Tests CRITICAL (~43 tests nuevos)
- `test_base_checker.py`: +25 (TestIsTestFile, TestIsTestFunction, TestGetConfigForExtension)
- `test_file_utils.py`: +6 (safe_relative_path, boundaries)
- `test_llm_protocol.py` (NUEVO): +12 (TokenUsage, LLMClientProtocol)
- Resultado esperado: ~702 tests

### Commit 4: Tests HIGH (~30 tests nuevos)
- `test_models.py`: +10 (get_score_label boundaries, to_dict)
- `test_api_client.py`: +6 (rate limit, SEC-04)
- `test_llm_client.py`: +8 (BDD heuristics, boundaries)
- `test_gherkin_parser.py`: +3 (parse_file)
- `test_html_reporter.py`: +3 (XSS, AI suggestion, SVG)
- Resultado esperado: ~732 tests

### Commit 5: Reforzar aserciones débiles
- 40+ tests modificados (mismo conteo, aserciones más fuertes)
- Resultado esperado: ~732 tests (sin cambio en conteo)

### Commit 6: Tests MEDIUM + helpers compartidos
- +11 tests nuevos
- Extracción de `parse_and_check` a conftest
- Resultado esperado: ~745+ tests

---

## 9. Impacto Estimado Final

| Métrica | Antes | Después |
|---------|-------|---------|
| Tests totales | 670 | ~745+ |
| Tests eliminados | — | -11 |
| Tests añadidos | — | ~86+ |
| Funciones zero coverage | 8 | 0 |
| Aserciones débiles | 40+ | 0 |
| Fixtures duplicadas | 6 | 0 |
| Helpers duplicados | 3 | 0 (compartido) |
| Security regression tests | parcial | completo |
| Boundary tests | 0 | 12+ |
