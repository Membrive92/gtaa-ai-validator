# Auditoría de Documentación — gTAA AI Validator

> **Fase 10.10** | Fecha: 2026-02-08
> **Metodología**: Auditoría white-box completa de documentación
> **Auditor**: Revisión exhaustiva con enfoque de evaluador TFM

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Documentos auditados | 6 + 4 reports (sexta pasada) |
| Hallazgos totales | 51 |
| Hallazgos CRITICAL | 16 (errores factuales) |
| Hallazgos HIGH | 15 (datos desactualizados) |
| Hallazgos MEDIUM | 16 (inconsistencias menores) |
| Hallazgos LOW | 4 (inconsistencias menores entre reports) |
| Estado | **51/51 Corregidos** |

### Documentos Auditados

| Documento | Tamaño | Hallazgos |
|-----------|--------|-----------|
| `README.md` (raíz) | 1205 líneas | 19 |
| `docs/README.md` | 747 líneas | 15 |
| `docs/PHASE2_FLOW_DIAGRAMS.md` | ~700 líneas | 1 |
| `docs/PHASE9_FLOW_DIAGRAMS.md` | ~850 líneas | 1 |
| `docs/PHASE10_FLOW_DIAGRAMS.md` | 1540 líneas | 3 |
| `docs/TEST_AUDIT_REPORT.md` | 445 líneas | 1 |
| `docs/SECURITY_AUDIT_REPORT.md` | 574 líneas | 0 (renombrado) |
| `docs/ARCHITECTURE_DECISIONS.md` | ~3600 líneas | 0 |

---

## 2. Metodología

La auditoría se realizó cruzando la documentación con:

- **Código fuente**: Verificación de fórmulas, tipos de violación, nombres de parsers
- **Tests**: Conteo real con `pytest --co` (761 tests confirmados)
- **ADRs**: Conteo real de headings `## N.` en ARCHITECTURE_DECISIONS.md (60 ADRs)
- **Ejecución real**: Validación de outputs del CLI contra lo documentado

### Categorías de hallazgos

| Categoría | Descripción | Criterio |
|-----------|-------------|----------|
| **CRITICAL** | Error factual: dato documentado contradice el código fuente | La documentación dice algo que el código NO hace |
| **HIGH** | Dato desactualizado: era correcto pero ya no lo es tras una fase posterior | Fase 10.9+ cambió valores que no se propagaron |
| **MEDIUM** | Inconsistencia menor o ruido: no impacta comprensión pero resta profesionalismo | Redundancias, conteos ligeramente diferentes |

---

## 3. Hallazgos CRITICAL (6) — Errores Factuales

### DOC-01 — Fórmula de scoring contradictoria [CRITICAL]

**Fichero**: `docs/README.md` (diagrama E2E, línea ~282)

**Descripción**: El diagrama E2E en `docs/README.md` mostraba la fórmula de scoring como:
```
CRITICAL=-15, HIGH=-10, MEDIUM=-5, LOW=-2
```

Sin embargo, el código real en `models.py` y la tabla de scoring en el README raíz usan:
```
CRITICAL=-10, HIGH=-5, MEDIUM=-2, LOW=-1
```

**Impacto**: Un evaluador que lea la documentación técnica obtendrá una comprensión incorrecta del sistema de scoring. Los números no cuadran con los resultados reales del validador.

**Estado**: ✅ **CORREGIDO** — Diagrama actualizado con los valores reales.

---

### DOC-02 — Tipos de violación BDD inexistentes en diagrama E2E [CRITICAL]

**Fichero**: `docs/README.md` (diagrama E2E, línea ~341)

**Descripción**: El diagrama E2E listaba los siguientes tipos de violación BDD:
```
- MISSING_TAGS
- EMPTY_SCENARIO
- MISSING_STEPS
```

Estos tipos **no existen** en el código. Los 5 tipos reales de violación BDD son:
```
- GHERKIN_IMPLEMENTATION_DETAIL
- STEP_DEF_DIRECT_BROWSER_CALL
- STEP_DEF_TOO_COMPLEX
- MISSING_THEN_STEP
- DUPLICATE_STEP_PATTERN
```

**Impacto**: Tres tipos de violación completamente fabricados en un diagrama técnico. Un evaluador que busque estos tipos en el código no los encontrará.

**Estado**: ✅ **CORREGIDO** — Diagrama actualizado con los 5 tipos reales.

---

### DOC-03 — Parser Gherkin mal identificado como "gherkin-official" [CRITICAL]

**Fichero**: `docs/README.md` (tabla de parsers, línea ~554 y ~570)

**Descripción**: La tabla de tecnologías de parsing y las descripciones del parser Gherkin lo identificaban como `gherkin-official`, que es un paquete npm/pip existente. El parser real es **regex-based, implementado desde cero sin dependencias externas** (decisión documentada en ADR 28).

**Impacto**: Un evaluador podría pensar que se usa una dependencia externa cuando en realidad es código propio del proyecto. Esto afecta la evaluación de la contribución técnica.

**Estado**: ✅ **CORREGIDO** — Cambiado a "regex propio (sin dependencias)".

---

### DOC-04 — "3 técnicas de IA" cuando son 2 [CRITICAL]

**Fichero**: `README.md` (línea ~168)

**Descripción**: El README raíz mencionaba "3 técnicas de IA" en la sección de solución propuesta, pero solo listaba 2:
1. Análisis Estático (AST + regex)
2. Análisis Semántico (LLM)

No hay una tercera técnica. AST y regex son la misma técnica de análisis estático.

**Impacto**: Inconsistencia numérica que podría confundir a un evaluador.

**Estado**: ✅ **CORREGIDO** — Cambiado a "2 técnicas complementarias".

---

### DOC-05 — "4 Checkers" en diagrama de arquitectura cuando son 5 [CRITICAL]

**Fichero**: `README.md` (diagrama de arquitectura, línea ~213)

**Descripción**: El diagrama de arquitectura del sistema mostraba "4 Checkers" en la rama estática, pero desde la Fase 8 existen 5 checkers:
1. DefinitionChecker
2. StructureChecker
3. AdaptationChecker
4. QualityChecker
5. BDDChecker

**Estado**: ✅ **CORREGIDO** — Cambiado a "5 Checkers".

---

### DOC-06 — Conteo de violaciones BDD incorrecto [CRITICAL]

**Fichero**: `docs/README.md` (línea ~564-567)

**Descripción**: La descripción de la Fase 8 mencionaba "6 tipos de violaciones BDD" cuando en realidad son 5.

**Estado**: ✅ **CORREGIDO** — Cambiado a "5 tipos de violaciones BDD".

---

## 4. Hallazgos HIGH (12) — Datos Desactualizados

### DOC-07 — Test count desactualizado: 669 → 761 [HIGH]

**Ficheros**: `README.md` (4 ubicaciones), múltiples badges y menciones

**Descripción**: Tras la Fase 10.9 (auditoría QA), el conteo de tests pasó de 669 a 761. El número 669 aparecía en 4 ubicaciones del README raíz:
- Badge (línea 11)
- Tabla de funcionalidades (línea 63)
- Sección de comandos (línea 343)
- Estructura de tests (línea 682)

**Estado**: ✅ **CORREGIDO** — Todas las ocurrencias actualizadas a 761.

---

### DOC-08 — ADR count desactualizado: 55 → 60 [HIGH]

**Ficheros**: `README.md` (3 ubicaciones), `docs/README.md` (1 ubicación)

**Descripción**: Tras las fases 10.5-10.8 se añadieron ADRs 38-60. Las referencias seguían indicando "55 ADRs".

**Estado**: ✅ **CORREGIDO** — Todas las ocurrencias actualizadas a 60.

---

### DOC-09 — Badge de fase desactualizado: 10.8 → 10.9 [HIGH]

**Fichero**: `README.md` (línea 8)

**Descripción**: El badge de fase mostraba "10.8/10" cuando la Fase 10.9 ya estaba completada.

**Estado**: ✅ **CORREGIDO** — Badge actualizado a "10.9/10".

---

### DOC-10 — Cabecera de estado desactualizada [HIGH]

**Fichero**: `README.md` (línea 19)

**Descripción**: "Estado: Fase 10.8/10 Completa | Última actualización: 7 Febrero 2026"

**Estado**: ✅ **CORREGIDO** — Actualizado a "Fase 10.9/10 | 8 Febrero 2026".

---

### DOC-11 — Falta fila de Fase 10.9 en tabla [HIGH]

**Fichero**: `README.md` (tabla de fases, línea ~42-50)

**Descripción**: La tabla de estado de implementación por fases no incluía la Fase 10.9.

**Estado**: ✅ **CORREGIDO** — Añadida fila para Fase 10.9.

---

### DOC-12 — Título "Funcionalidad ACTUAL (Fase 10.8)" desactualizado [HIGH]

**Fichero**: `README.md` (línea ~303)

**Descripción**: El título de la sección de funcionalidad actual referenciaba Fase 10.8.

**Estado**: ✅ **CORREGIDO** — Actualizado a "Fase 10.9".

---

### DOC-13 — Sección "Funcionalidad FUTURA" ya implementada [HIGH]

**Fichero**: `README.md` (línea ~619-624)

**Descripción**: La sección de funcionalidad futura listaba "Integración CI/CD (--min-score)" como pendiente, pero CI/CD ya está implementado con GitHub Actions (Fase 10.4).

**Estado**: ✅ **CORREGIDO** — Eliminado ítem ya implementado.

---

### DOC-14 — "Fase 8/10" en contexto académico [HIGH]

**Fichero**: `README.md` (línea ~831)

**Descripción**: La sección de objetivos del TFM decía "Fase 8/10 completa".

**Estado**: ✅ **CORREGIDO** — Actualizado a "Fase 10.9/10".

---

### DOC-15 — Fases 10.2-10.4 y 10.9 ausentes en metodología [HIGH]

**Fichero**: `README.md` (línea ~856)

**Descripción**: La lista de metodología solo incluía 10.1, 10.5, 10.6, 10.7, 10.8, faltando 10.2, 10.3, 10.4 y 10.9.

**Estado**: ✅ **CORREGIDO** — Añadidas todas las sub-fases.

---

### DOC-16 — Falta historial de Fase 10.9 [HIGH]

**Fichero**: `README.md` (sección de historial, línea ~1192)

**Descripción**: No había entrada de historial para la Versión 0.10.9 (Fase 10.9).

**Estado**: ✅ **CORREGIDO** — Añadida sección de historial.

---

### DOC-17 — Footer desactualizado [HIGH]

**Fichero**: `README.md` (línea ~1203)

**Descripción**: El footer mostraba "Fase 10.8/10 | 669 tests".

**Estado**: ✅ **CORREGIDO** — Actualizado a "Fase 10.9/10 | 761 tests".

---

### DOC-18 — Fecha desactualizada en docs/README.md [HIGH]

**Fichero**: `docs/README.md` (línea 691)

**Descripción**: "Última actualización: 6 Febrero 2026 (Fase 10.4)"

**Estado**: ✅ **CORREGIDO** — Actualizado a "8 Febrero 2026 (Fase 10.10)".

---

## 5. Hallazgos MEDIUM (10) — Inconsistencias Menores

### DOC-19 — "Fase 5" hardcodeada en ejemplo CLI [MEDIUM]

**Fichero**: `README.md` (línea ~378)

**Descripción**: El ejemplo de output del CLI contenía "=== gTAA AI Validator - Fase 5 ===" en lugar de un texto genérico. Esto es ruido de una fase antigua.

**Estado**: ✅ **CORREGIDO** — Actualizado a texto genérico.

---

### DOC-20 — bad_project "~45 violaciones" vs "~35 violaciones" [MEDIUM]

**Fichero**: `README.md` (línea ~417 vs ~714)

**Descripción**: La sección de ejemplos describe bad_project con "~45 violaciones" (correcto tras BDD), pero la sección de estructura del proyecto decía "~35 violaciones".

**Estado**: ✅ **CORREGIDO** — Unificado a "~45 violaciones".

---

### DOC-21 — "five sub-phases" en PHASE10_FLOW_DIAGRAMS.md [MEDIUM]

**Fichero**: `docs/PHASE10_FLOW_DIAGRAMS.md` (línea 5)

**Descripción**: "La Fase 10 se divide en five sub-fases documentadas" cuando ya son nueve.

**Estado**: ✅ **CORREGIDO** — Actualizado a nueve sub-fases.

---

### DOC-22 — Lista de sub-fases incompleta en PHASE10_FLOW_DIAGRAMS.md [MEDIUM]

**Fichero**: `docs/PHASE10_FLOW_DIAGRAMS.md` (línea 7-11)

**Descripción**: Solo listaba 10.1, 10.2, 10.3, 10.4 y 10.8. Faltaban 10.5, 10.6, 10.7 y 10.9.

**Estado**: ✅ **CORREGIDO** — Lista completa con las 9 sub-fases.

---

### DOC-23 — Fecha de PHASE10_FLOW_DIAGRAMS.md desactualizada [MEDIUM]

**Fichero**: `docs/PHASE10_FLOW_DIAGRAMS.md` (línea 1539)

**Descripción**: "Última actualización: Fase 10.8"

**Estado**: ✅ **CORREGIDO** — Actualizado a "Fase 10.10".

---

### DOC-24 — TEST_AUDIT_REPORT.md sin resultados post-implementación [MEDIUM]

**Fichero**: `docs/TEST_AUDIT_REPORT.md`

**Descripción**: El informe de auditoría QA contenía el plan de corrección pero no los resultados finales tras la implementación (761 tests, 0 fallos, 2.76s).

**Estado**: ✅ **CORREGIDO** — Añadida sección "10. Resultados Post-Implementación".

---

### DOC-25 — "10.5 tests: 633" cuando fueron 667 [MEDIUM]

**Fichero**: `README.md` (tabla de fases, línea ~47)

**Descripción**: La fila de Fase 10.5 indicaba "633 tests" en su descripción, pero el conteo real post-10.5 fue 667.

**Estado**: ✅ **CORREGIDO** — Actualizado a 667.

---

### DOC-26 — ADR listing en docs/README.md solo hasta ADR 37 [MEDIUM]

**Fichero**: `docs/README.md` (línea ~165-212)

**Descripción**: El índice de ADRs en la sección de ARCHITECTURE_DECISIONS.md solo listaba hasta el ADR 37. Faltan los ADRs 38-60 añadidos en las fases 10.1-10.8.

**Estado**: ✅ **CORREGIDO** — Índice extendido hasta ADR 60.

---

### DOC-27 — Naming inconsistente de auditorías [MEDIUM]

**Ficheros**: `docs/PHASE10_SECURITY_AUDIT.md` vs `docs/TEST_AUDIT_REPORT.md`

**Descripción**: Los informes de auditoría usaban convenciones de nombre diferentes:
- Seguridad: `PHASE10_SECURITY_AUDIT.md` (prefijo de fase)
- Tests: `TEST_AUDIT_REPORT.md` (sin prefijo de fase)

**Estado**: ✅ **CORREGIDO** — Renombrado a `SECURITY_AUDIT_REPORT.md` para consistencia.

---

### DOC-28 — Referencia a "Fase 5" en ejemplo de output CLI [MEDIUM]

**Fichero**: `README.md`

**Descripción**: Duplicado conceptual de DOC-19 (el mismo ejemplo de output).

**Estado**: ✅ **CORREGIDO** — Ver DOC-19.

---

## 6. Hallazgos Segunda Pasada (5) — Revisión Post-10.10

> **Fecha**: 8 de febrero de 2026 (revisión posterior a la auditoría inicial)

### DOC-29 — "nueve sub-fases" en PHASE10_FLOW_DIAGRAMS.md cuando son diez [CRITICAL]

**Fichero**: `docs/PHASE10_FLOW_DIAGRAMS.md` (línea 5)

**Descripción**: El resumen general indicaba "nueve sub-fases documentadas" y la lista solo contenía 9 elementos (10.1 a 10.9). Faltaba la Fase 10.10 (auditoría de documentación), que es precisamente este documento.

**Impacto**: Un evaluador no encontraría la Fase 10.10 referenciada en el documento que describe la Fase 10.

**Estado**: ✅ **CORREGIDO** — Actualizado a "diez sub-fases" y añadida Fase 10.10 a la lista.

---

### DOC-30 — Test count "672 → 669" sin nota de actualización posterior [HIGH]

**Ficheros**: `docs/PHASE10_FLOW_DIAGRAMS.md` (líneas 1166 y 1539)

**Descripción**: El documento de Fase 10.8 mostraba "672 tests → 669 tests (3 legacy eliminados)" como dato final, sin indicar que la Fase 10.9 posterior llevó el total a 761 tests. Un lector que no consultase otros documentos quedaría con la impresión de que el proyecto tiene 669 tests.

**Nota**: El dato 672→669 es históricamente correcto para la Fase 10.8. No se modifica el dato, sino que se añade una nota aclaratoria.

**Estado**: ✅ **CORREGIDO** — Añadida nota: "Tras la Fase 10.9, el total pasó a 761 tests."

---

### DOC-31 — Test count "672 → 669" sin nota en ARCHITECTURE_DECISIONS.md [HIGH]

**Fichero**: `docs/ARCHITECTURE_DECISIONS.md` (línea 3366)

**Descripción**: El ADR 55 (eliminación de código muerto) indicaba "Tests: 672 → 669 (3 legacy eliminados). Los 669 tests restantes pasan." sin contexto de que el total actual es 761.

**Estado**: ✅ **CORREGIDO** — Añadida nota aclaratoria sobre el total actual de 761 tests.

---

### DOC-32 — "4 checkers" en descripción de PHASE3 en docs/README.md [MEDIUM]

**Fichero**: `docs/README.md` (línea 56)

**Descripción**: La descripción del contenido de PHASE3_FLOW_DIAGRAMS.md indicaba "Visión general de la arquitectura con 4 checkers". Aunque históricamente correcto para la Fase 3 (BDDChecker se añadió en Fase 8), el índice de documentación debería indicar el estado actual para evitar confusión.

**Estado**: ✅ **CORREGIDO** — Cambiado a "4 checkers (5 desde Fase 8)".

---

### DOC-33 — Sección "Documentación Futura (Planeada)" obsoleta [MEDIUM]

**Fichero**: `docs/README.md` (líneas 661-670)

**Descripción**: La sección listaba 3 documentos planeados (`gtaa_reference.md`, `api_documentation.md`, `contributing.md`) que no se van a crear dado que el desarrollo del TFM está completo y el proyecto se encuentra en fase UAT. Mantener documentación futura planeada en un proyecto finalizado genera confusión.

**Estado**: ✅ **CORREGIDO** — Sección eliminada.

---

## 7. Hallazgos Tercera Pasada (3) — Verificación de Diagramas E2E vs Código

> **Fecha**: 9 de febrero de 2026 (verificación cruzada diagramas vs código fuente real)

Se generó un diagrama de flujo E2E completo a partir del código fuente (`__main__.py`, `static_analyzer.py`, `semantic_analyzer.py`, `file_classifier.py`, `models.py`) y se comparó con los diagramas documentados en `docs/README.md` (sección "Flujo E2E de Análisis"). Se encontraron 3 errores factuales.

### DOC-34 — Orden de ejecución incorrecto en diagrama E2E [CRITICAL]

**Fichero**: `docs/README.md` (diagrama E2E, líneas 283-291)

**Descripción**: El diagrama mostraba el paso "2a. Descubrir archivos" (`_discover_python_files()`) **antes** del paso "2b. Verificaciones a nivel proyecto" (`check_project()`). Sin embargo, el código real en `static_analyzer.py:131-143` ejecuta `check_project()` **primero** y luego descubre los archivos:

```python
# Código real (static_analyzer.py:131-143):
for checker in self.checkers:
    project_violations = checker.check_project(self.project_path)  # ← PRIMERO

python_files = self._discover_python_files()  # ← DESPUÉS
```

**Impacto**: Un evaluador que lea el diagrama entenderá un flujo de ejecución diferente al real. Las verificaciones a nivel proyecto (ej. existencia de `/tests` y `/pages`) son independientes de los archivos descubiertos y se ejecutan antes.

**Estado**: ✅ **CORREGIDO** — Intercambiados a "2a. Verificaciones a nivel proyecto" → "2b. Descubrir archivos".

---

### DOC-35 — Valores de file_type incorrectos en diagrama E2E [CRITICAL]

**Fichero**: `docs/README.md` (diagrama E2E, líneas 335 y 357)

**Descripción**: El diagrama mostraba los posibles valores de `file_type` como:
```
file_type = "ui_test" | "api_test" | "page_object"
```

Los valores reales en `FileClassifier` (`file_classifier.py`) son:
```
file_type = "ui" | "api" | "page_object" | "unknown"
```

Los nombres `"ui_test"` y `"api_test"` no existen en el código. Además, faltaba el valor `"unknown"` que es el default cuando el clasificador no alcanza el umbral de scoring.

**Impacto**: Un evaluador que busque los strings `"ui_test"` o `"api_test"` en el código no los encontrará. El diagrama técnico no refleja la interfaz real del clasificador.

**Estado**: ✅ **CORREGIDO** — Actualizado a `"ui" | "api" | "page_object" | "unknown"` en ambas ubicaciones.

---

### DOC-36 — TextReporter inexistente en diagrama E2E [CRITICAL]

**Fichero**: `docs/README.md` (diagrama E2E, líneas 440-451)

**Descripción**: El diagrama de la sección 4 (Reporter) mostraba tres reporters:
- `TextReporter` (default) → stdout
- `JsonReporter` → file.json
- `HtmlReporter` → file.html

**`TextReporter` no existe** en el código. La salida a stdout se genera directamente en `__main__.py` mediante `click.echo()` en el método `_display_results()`. Solo existen 2 reporters reales:
- `JsonReporter` (`reporters/json_reporter.py`)
- `HtmlReporter` (`reporters/html_reporter.py`)

**Impacto**: Componente fabricado en el diagrama de arquitectura. Un evaluador que busque `TextReporter` en el código no lo encontrará. Este es un ejemplo de alucinación del modelo: el nombre es plausible pero no corresponde a ninguna clase real.

**Estado**: ✅ **CORREGIDO** — Reemplazado por "CLI (stdout)" con `click.echo()` / `_display_results`.

---

## 7b. Hallazgos Cuarta Pasada (1) — Diagrama de Arquitectura del README raíz

> **Fecha**: 9 de febrero de 2026 (verificación del diagrama de arquitectura de alto nivel en README.md)

### DOC-37 — Diagrama de arquitectura del sistema simplificado y engañoso [CRITICAL]

**Fichero**: `README.md` (sección "Arquitectura del sistema", líneas 206-224)

**Descripción**: El diagrama de arquitectura de alto nivel en el README raíz mostraba:

```
INPUT → ESTÁTICO ──┐
                   ├─→ SCORING + REPORTS
        SEMÁNTICO ─┘
```

Este diagrama tenía **5 problemas** que daban una impresión incorrecta de la arquitectura:

1. **Flujo paralelo**: Mostraba análisis estático y semántico como ramas paralelas, cuando en realidad son **secuenciales** — el semántico recibe y enriquece el Report producido por el estático
2. **Semántico no marcado como opcional**: No indicaba que el análisis semántico solo se ejecuta con `--ai`. Sin esta flag, solo corre el estático
3. **"✅ Fase 5" como texto**: Ruido de desarrollo que no aporta información arquitectónica
4. **Sin soporte multilenguaje**: No reflejaba los 4 parsers (AST para Python, tree-sitter para Java/JS/C#, regex para Gherkin) ni el ParseResult unificado — una pieza clave de la Fase 9
5. **Output simplificado**: "SCORING + REPORTS" no distinguía las 3 salidas reales: CLI stdout (`click.echo()`), JsonReporter y HtmlReporter. Tampoco mencionaba el exit code 1 para CI/CD

**Impacto**: Un evaluador del TFM que lea este diagrama entendería una arquitectura más simple de lo que realmente es. No vería el soporte multilenguaje, el FileClassifier, la opcionalidad del análisis semántico, ni el factory pattern para LLM clients. Dado que el diagrama de arquitectura es lo primero que un evaluador consulta para entender el sistema, su impacto es alto.

**Estado**: ✅ **CORREGIDO** — Diagrama reemplazado por uno detallado con 3 bloques secuenciales:
1. Análisis Estático (parsers multilenguaje → ParseResult → FileClassifier → 5 Checkers → Report)
2. Análisis Semántico (opcional con --ai, factory → APILLMClient/MockLLMClient, fallback 429)
3. Output (CLI stdout + JsonReporter + HtmlReporter + exit code 1)

---

## 8. Hallazgos Quinta Pasada (8) — Diagramas de Parser, Ejemplo Java y Fases Históricas

> **Fecha**: 9 de febrero de 2026 (verificación cruzada de diagramas de parser, ejemplo concreto Java y diagramas de fases históricas vs código fuente)

Se verificaron los diagramas "Selección de Parser por Lenguaje" y "Ejemplo Concreto: Proyecto Java" en `docs/README.md`, y los diagramas de clases en `docs/PHASE2_FLOW_DIAGRAMS.md` y `docs/PHASE9_FLOW_DIAGRAMS.md`, contra el código fuente real. Se encontraron 8 errores: 5 nombres fabricados y 3 datos incompletos.

### DOC-38 — Extensiones JS/TS incompletas en diagrama de parser [MEDIUM]

**Fichero**: `docs/README.md` (diagrama de parser, línea 475)

**Descripción**: El diagrama mostraba `.js / .ts / .tsx` como extensiones soportadas por JSParser. Faltaban `.jsx`, `.mjs` y `.cjs`, que están definidas en `LANGUAGE_EXTENSIONS` (`treesitter_base.py:87-92`) y se descubren en `static_analyzer.py:186-187`.

**Estado**: ✅ **CORREGIDO** — Actualizado a `.js/.ts/.tsx/.jsx/.mjs/.cjs`.

---

### DOC-39 — GherkinParser mostrado como parte del factory get_parser_for_file() [MEDIUM]

**Fichero**: `docs/README.md` (diagrama de parser, línea 479)

**Descripción**: El diagrama mostraba `.feature → GherkinParser` como una ruta dentro de la factory function `get_parser_for_file()`. En realidad, `get_parser_for_file()` retorna `None` para `.feature` — el GherkinParser es usado directamente por BDDChecker sin pasar por la factory.

**Estado**: ✅ **CORREGIDO** — Añadida nota aclaratoria: "usado directamente por BDDChecker, no pasa por get_parser_for_file".

---

### DOC-40 — ParseResult con campos incompletos en diagrama [MEDIUM]

**Fichero**: `docs/README.md` (diagrama de parser, líneas 486-491)

**Descripción**: El diagrama mostraba 5 campos en ParseResult (`imports`, `classes`, `functions`, `calls`, `strings`). Faltaban 2 campos adicionales definidos en `treesitter_base.py:68-76`: `language` (str) y `parse_errors` (List[str]).

**Estado**: ✅ **CORREGIDO** — Añadidos `language` y `parse_errors` al diagrama.

---

### DOC-41 — Nombre de método fabricado: _discover_files() [CRITICAL]

**Fichero**: `docs/README.md` (ejemplo Java, línea 544)

**Descripción**: El diagrama mostraba `StaticAnalyzer._discover_files()`. El método real es `_discover_python_files()` (`static_analyzer.py:169`). El nombre `_discover_files` no existe en el código.

**Impacto**: Un evaluador que busque `_discover_files` en el código no lo encontrará. El nombre correcto refleja el origen histórico del método (inicialmente solo Python, ahora multi-lenguaje).

**Estado**: ✅ **CORREGIDO** — Renombrado a `_discover_python_files()`.

---

### DOC-42 — Firma de checker.check() incorrecta [CRITICAL]

**Fichero**: `docs/README.md` (ejemplo Java, líneas 562, 567, 576)

**Descripción**: El diagrama mostraba `DefinitionChecker.check(parse_result, ".java")` con 2 parámetros. La firma real (`checkers/base.py:53-55`) es:
```python
def check(self, file_path: Path,
          tree: Optional[Union[ast.Module, ParseResult]] = None,
          file_type: str = "unknown") -> List[Violation]:
```
Faltaba el parámetro obligatorio `file_path` y el segundo parámetro es `file_type` (no la extensión directa).

**Impacto**: Un evaluador que intente entender la API de los checkers verá una interfaz diferente a la real. El parámetro `file_path` es obligatorio y la extensión no se pasa directamente — se pasa `file_type` (clasificación del FileClassifier).

**Estado**: ✅ **CORREGIDO** — Actualizado a `check(file_path, parse_result, file_type="unknown")` en los 3 checkers.

---

### DOC-43 — Nombre de variable fabricado: POOR_PATTERNS_JAVA [CRITICAL]

**Fichero**: `docs/README.md` (ejemplo Java, línea 572)

**Descripción**: El diagrama mostraba `_check_poor_naming() con POOR_PATTERNS_JAVA`. La variable real en `quality_checker.py:66-67` es `GENERIC_NAME_PATTERNS_JAVA`. El nombre `POOR_PATTERNS_JAVA` no existe en el código.

**Impacto**: Alucinación del modelo. Un evaluador que busque `POOR_PATTERNS_JAVA` en el código no lo encontrará. El patrón de naming real es `GENERIC_NAME_PATTERNS_<LANG>` (Python, Java, JS, CSharp).

**Estado**: ✅ **CORREGIDO** — Renombrado a `GENERIC_NAME_PATTERNS_JAVA`.

---

### DOC-44 — Nombre de método fabricado en diagrama Fase 2: _discover_files() [CRITICAL]

**Fichero**: `docs/PHASE2_FLOW_DIAGRAMS.md` (diagrama de clases, línea 696)

**Descripción**: El diagrama de clases de StaticAnalyzer mostraba `_discover_files()`. El método real es `_discover_python_files()` (incluso en la Fase 2, cuando el proyecto solo soportaba Python).

**Estado**: ✅ **CORREGIDO** — Renombrado a `_discover_python_files()`.

---

### DOC-45 — Nombre de método fabricado en diagrama Fase 9: _discover_files() [CRITICAL]

**Fichero**: `docs/PHASE9_FLOW_DIAGRAMS.md` (diagrama de discovery, línea 607)

**Descripción**: El diagrama de discovery de archivos mostraba `StaticAnalyzer._discover_files()`. El método real es `_discover_python_files()`. Irónicamente, el diagrama de la Fase 9 (multilenguaje) usaba un nombre incorrecto para el método que descubre archivos de todos los lenguajes.

**Estado**: ✅ **CORREGIDO** — Renombrado a `_discover_python_files()`.

---

## 8b. Hallazgos Sexta Pasada (6) — Auditoría cruzada de informes de Reports

> **Fecha**: 10 de febrero de 2026 (revisión de formato y contenido de los 4 informes de auditoría/UAT cruzando datos contra código fuente, ejecución real de tests y consistencia inter-documental)

Se revisaron los 4 ficheros `*_REPORT.md` en `docs/` verificando: (1) que los datos factuales coincidan con el código y tests reales, (2) que los conteos sean internamente consistentes, y (3) que la convención de datos sea uniforme entre informes. Se encontraron 6 errores.

### DOC-46 — Tabla de distribución de tests no suma 670 [HIGH]

**Fichero**: `docs/TEST_AUDIT_REPORT.md` (sección 1, tabla "Distribución actual por fichero")

**Descripción**: La tabla de distribución por fichero listaba conteos individuales que sumaban **729**, no **670** como indicaba el texto "Tests totales: 670 (pytest --co)". La discrepancia de 59 tests se debía a que algunos conteos por fichero fueron actualizados durante la implementación de la Fase 10.9 sin actualizar el total del resumen. Además, faltaba `test_llm_protocol.py` (fichero nuevo creado en Fase 10.9).

**Estado**: ✅ **CORREGIDO** — Tabla reemplazada con la distribución post-implementación real (761 tests, 29 ficheros) verificada con `pytest --co -q`. Resumen actualizado para reflejar que los 670 corresponden al estado pre-auditoría y la tabla muestra el estado final.

---

### DOC-47 — Sección "Tercera Pasada (4)" agrupa hallazgos de dos pasadas distintas [MEDIUM]

**Fichero**: `docs/DOC_AUDIT_REPORT.md` (sección 7)

**Descripción**: La sección 7 se titulaba "Hallazgos Tercera Pasada **(4)**" agrupando DOC-34 a DOC-37. Sin embargo, el desglose de totales (líneas 292 y 700) indicaba "3 tercera pasada + 1 cuarta pasada", contando DOC-37 (diagrama de arquitectura del README raíz) como una pasada separada. No existía sección dedicada para la cuarta pasada, por lo que un lector que buscase la "cuarta pasada" mencionada en el resumen no la encontraría.

**Estado**: ✅ **CORREGIDO** — Sección 7 renombrada a "Tercera Pasada (3)" con DOC-34 a DOC-36. Creada sección 7b "Cuarta Pasada (1)" con DOC-37 y su propia fecha y contexto.

---

### DOC-48 — "416 tests" sin nota aclaratoria del total actual [LOW]

**Fichero**: `docs/SECURITY_AUDIT_REPORT.md` (línea 565)

**Descripción**: El texto "416 tests pasando tras la remediación (0 fallos)" era históricamente correcto para el 6 de febrero de 2026 (Fase 10.3), pero otros documentos históricos (`ARCHITECTURE_DECISIONS.md` ADR 55, `PHASE10_FLOW_DIAGRAMS.md`) añadieron notas aclaratorias tipo "Nota: Tras la Fase 10.9, el total actual es 761 tests". Este informe carecía de tal nota, lo que podía dar la impresión de que la suite solo tenía 416 tests.

**Estado**: ✅ **CORREGIDO** — Añadida nota aclaratoria en cursiva tras el conteo de 416 tests.

---

### DOC-49 — "Versión auditada" usa convención de fase, no de paquete [LOW]

**Fichero**: `docs/DOC_AUDIT_REPORT.md` (línea 716)

**Descripción**: El campo "Versión auditada: 0.10.10" usaba el número de fase como versión, mientras que `SECURITY_AUDIT_REPORT.md` usaba "0.10.4" (la versión real del paquete, `__version__`). Un lector podría buscar la versión `0.10.10` en el código sin encontrarla, ya que la versión del paquete es `0.10.4`.

**Estado**: ✅ **CORREGIDO** — Actualizado a "0.10.4 (Fase 10.10)" para mantener la referencia a la fase sin confundir con la versión del paquete.

---

### DOC-50 — Conteo de tipos de violación de bad_project incompleto [LOW]

**Fichero**: `docs/UAT_TESTING_REPORT.md` (sección 7.1, líneas 235-247)

**Descripción**: El listado de tipos de violación para `bad_project` sumaba 54, no 58 (el total real verificado con el validador). Las diferencias:
- `HARDCODED_TEST_DATA`: documentado como 12, real es **15** (+3)
- `HARDCODED_CONFIGURATION`: documentado como 3, real es **4** (+1)

**Estado**: ✅ **CORREGIDO** — Conteos actualizados a los valores reales. El listado ahora suma 58, coincidiendo con la distribución por severidad (19+30+6+3=58).

---

### DOC-51 — "32 archivos de test" desactualizado [LOW]

**Fichero**: `docs/TEST_AUDIT_REPORT.md` (sección 1, resumen ejecutivo)

**Descripción**: El resumen indicaba "32 archivos de test" pero el conteo real es 29 ficheros de test (26 unit + 3 integration). La diferencia de 3 se debía probablemente a la inclusión de ficheros `conftest.py` y `__init__.py` en el conteo original.

**Estado**: ✅ **CORREGIDO** — Actualizado a "28" (pre-auditoría, sin `test_llm_protocol.py`) en el resumen, y la tabla post-implementación muestra 29 ficheros.

---

## 9. Impacto de la Corrección

| Métrica | Antes | Después |
|---------|-------|---------|
| Errores factuales | 16 | 0 |
| Datos desactualizados | 14 | 0 |
| Inconsistencias menores | 15 | 0 |
| Fórmula de scoring | Incorrecta (-15/-10/-5/-2) | Correcta (-10/-5/-2/-1) |
| Tipos BDD en diagrama | 3 inexistentes | 5 reales |
| Parser Gherkin | "gherkin-official" | "regex propio" |
| Test count | 669 | 761 (con notas aclaratorias en docs históricos) |
| ADR count | 55 | 60 |
| Sub-fases Fase 10 | 9 (faltaba 10.10) | 10 |
| Orden E2E diagram | discover_files antes de check_project | check_project primero (correcto) |
| file_type values | "ui_test" \| "api_test" (inexistentes) | "ui" \| "api" \| "page_object" \| "unknown" |
| TextReporter | Componente fabricado en diagrama | CLI (stdout) con click.echo() |
| Naming auditorías | Inconsistente | Consistente (*_AUDIT_REPORT.md) |
| Diagrama arquitectura | Simplificado (paralelo, sin multi-lang) | Detallado (secuencial, 4 parsers, 3 outputs) |
| Documentación futura obsoleta | 3 docs planeados | Sección eliminada |
| Extensiones JS en diagrama parser | `.js/.ts/.tsx` (incompleto) | `.js/.ts/.tsx/.jsx/.mjs/.cjs` |
| GherkinParser en factory | Mostrado como parte de factory | Nota: BDDChecker lo usa directamente |
| ParseResult campos | 5 campos (incompleto) | 7 campos (+`language`, `parse_errors`) |
| Método `_discover_files()` | Nombre fabricado | `_discover_python_files()` (nombre real) |
| Firma `checker.check()` | `check(parse_result, ".java")` | `check(file_path, parse_result, file_type)` |
| Variable `POOR_PATTERNS_JAVA` | Nombre fabricado | `GENERIC_NAME_PATTERNS_JAVA` (nombre real) |
| `_discover_files()` en Fase 2 | Nombre fabricado en diagrama de clases | `_discover_python_files()` |
| `_discover_files()` en Fase 9 | Nombre fabricado en diagrama de discovery | `_discover_python_files()` |
| Tabla test counts en TEST_AUDIT | Suma 729, no 670 | Actualizada a 761 (post-10.9) |
| "416 tests" en SECURITY_AUDIT | Sin nota aclaratoria | Nota: "Tras Fases 10.5-10.9, total 761" |
| "Versión auditada" en DOC_AUDIT | "0.10.10" (fase) | "0.10.4 (Fase 10.10)" |
| bad_project types en UAT | HARDCODED_TEST_DATA: 12, CONFIG: 3 | HARDCODED_TEST_DATA: 15, CONFIG: 4 |
| "32 archivos de test" | Conteo desactualizado | "28" pre-auditoría, 29 post-10.9 |
| Sección "Tercera Pasada (4)" | 4 hallazgos en una sección, breakdown dice 3+1 | Separada en Tercera (3) + Cuarta (1) |

---

## 10. Ficheros Modificados

| Fichero | Hallazgos corregidos |
|---------|---------------------|
| `README.md` | DOC-04, DOC-05, DOC-07, DOC-09, DOC-10, DOC-11, DOC-12, DOC-13, DOC-14, DOC-15, DOC-16, DOC-17, DOC-19, DOC-20, DOC-25, DOC-37 |
| `docs/README.md` | DOC-01, DOC-02, DOC-03, DOC-06, DOC-08, DOC-18, DOC-26, DOC-32, DOC-33, DOC-34, DOC-35, DOC-36, DOC-38, DOC-39, DOC-40, DOC-41, DOC-42, DOC-43 |
| `docs/PHASE2_FLOW_DIAGRAMS.md` | DOC-44 |
| `docs/PHASE9_FLOW_DIAGRAMS.md` | DOC-45 |
| `docs/PHASE10_FLOW_DIAGRAMS.md` | DOC-21, DOC-22, DOC-23, DOC-29, DOC-30 |
| `docs/TEST_AUDIT_REPORT.md` | DOC-24, DOC-46, DOC-51 |
| `docs/SECURITY_AUDIT_REPORT.md` | DOC-27 (renombrado), DOC-48 |
| `docs/UAT_TESTING_REPORT.md` | DOC-50 |
| `docs/ARCHITECTURE_DECISIONS.md` | DOC-31 |
| `docs/DOC_AUDIT_REPORT.md` | DOC-47, DOC-49 (este documento) |

---

## 11. Conclusiones

La documentación del proyecto presentaba un nivel de calidad **bueno** en cuanto a estructura y profundidad, pero contenía **16 errores factuales** que podrían haber afectado negativamente la evaluación del TFM. Los más graves eran:

1. **Fórmula de scoring contradictoria**: El diagrama E2E mostraba penalizaciones diferentes a las implementadas en código
2. **Tipos de violación BDD fabricados**: Tres tipos inexistentes listados en un diagrama técnico
3. **Parser mal identificado**: Código propio presentado como dependencia externa
4. **Sub-fases de Fase 10 incompletas**: El propio documento de Fase 10 omitía la Fase 10.10
5. **Orden de ejecución incorrecto en diagrama E2E**: El diagrama mostraba descubrir archivos antes de check_project, cuando el código lo ejecuta al revés
6. **Valores de file_type fabricados**: `"ui_test"` y `"api_test"` no existen en el código (los reales son `"ui"` y `"api"`)
7. **TextReporter inexistente**: Componente fabricado en el diagrama de reporters — la salida a stdout se genera con `click.echo()`, no existe una clase TextReporter
8. **Firma de checker.check() incorrecta**: El diagrama mostraba 2 parámetros cuando la firma real requiere 3 (`file_path`, `tree`, `file_type`)
9. **Método `_discover_files()` fabricado**: El nombre real es `_discover_python_files()`
10. **Variable `POOR_PATTERNS_JAVA` fabricada**: El nombre real es `GENERIC_NAME_PATTERNS_JAVA`

Los 14 hallazgos HIGH correspondían a datos que fueron correctos en fases anteriores pero no se actualizaron tras las fases 10.5-10.9. Esto es un efecto natural del desarrollo incremental, donde la documentación de fases anteriores queda desactualizada. En la segunda pasada se añadieron notas aclaratorias a los datos históricos (672→669 tests) para evitar confusión sin alterar el registro histórico.

La tercera pasada (verificación cruzada del diagrama E2E contra código fuente) reveló 3 errores CRITICAL adicionales, incluyendo una alucinación del modelo (TextReporter). La quinta pasada (verificación de diagramas de parser, ejemplo Java y fases históricas) reveló 5 errores CRITICAL más, incluyendo nombres fabricados replicados en 3 ficheros (`_discover_files` en docs/README.md, PHASE2 y PHASE9). Esto refuerza la necesidad de verificar **cada componente documentado** contra el código real, especialmente en diagramas técnicos donde los nombres plausibles son fáciles de aceptar sin cuestionar.

La sexta pasada (auditoría cruzada de los propios informes de auditoría y UAT) reveló 6 errores adicionales: 1 HIGH (tabla de tests con conteos inconsistentes), 1 MEDIUM (sección de pasada mal agrupada) y 4 LOW (notas aclaratorias faltantes, convención de versión, conteos parciales). Este hallazgo demuestra que los propios documentos de auditoría también requieren verificación, cerrando el ciclo de calidad documental.

Tras la corrección de los 51 hallazgos (28 primera pasada + 5 segunda pasada + 3 tercera pasada + 1 cuarta pasada + 8 quinta pasada + 6 sexta pasada), la documentación es **coherente, factualmente correcta y actualizada** al estado real del proyecto (Fase 10.10, 761 tests, 60 ADRs).

---

**Fecha de auditoría inicial**: 8 de febrero de 2026
**Fecha de segunda pasada**: 8 de febrero de 2026
**Fecha de tercera pasada**: 9 de febrero de 2026 (verificación E2E vs código)
**Fecha de cuarta pasada**: 9 de febrero de 2026 (diagrama de arquitectura)
**Fecha de quinta pasada**: 9 de febrero de 2026 (diagramas parser, ejemplo Java y fases históricas)
**Fecha de sexta pasada**: 10 de febrero de 2026 (auditoría cruzada de reports)
**Fecha de corrección**: 10 de febrero de 2026
**Versión auditada**: 0.10.4 (Fase 10.10)
**Auditor**: Revisión exhaustiva con enfoque evaluador TFM
**Metodología**: Cruce documentación vs código fuente, tests y ejecución real
