"""
Templates de prompts para análisis semántico con LLM.

Estos prompts se envían al modelo (Gemini Flash) para:
1. Detectar violaciones semánticas en código de test automation
2. Enriquecer violaciones existentes con sugerencias contextuales
"""

SYSTEM_PROMPT = """Eres un experto en arquitectura de test automation y el patrón gTAA \
(generic Test Automation Architecture). Tu tarea es analizar código Python de proyectos \
de test automation y detectar violaciones arquitectónicas.

El patrón gTAA define estas capas:
- **Capa de Definición (tests/)**: Contiene los tests. Solo debe orquestar acciones y verificar resultados.
- **Capa de Adaptación (pages/)**: Contiene Page Objects que encapsulan la interacción con la UI.
- **Capa de Ejecución**: El framework de testing (pytest, Selenium, Playwright).

Los tests deben ser independientes, claros y mantenibles. Los Page Objects deben tener \
responsabilidad única y no contener lógica de test."""

ANALYZE_FILE_PROMPT = """Analiza el siguiente archivo Python de un proyecto de test automation \
y detecta violaciones semánticas.

**Archivo**: `{file_path}`
**Clasificación del archivo**: {file_type} (api = test de API, ui = test de UI, unknown = no clasificado)
**Contenido**:
```python
{file_content}
```

**Auto-wait del framework**: {has_auto_wait}

**IMPORTANTE**:
- Si el archivo es de tipo "api", NO reportes MISSING_WAIT_STRATEGY (las esperas de UI no aplican a tests de API).
- Si el framework tiene auto-wait (has_auto_wait = sí), NO reportes MISSING_WAIT_STRATEGY (el framework gestiona las esperas automáticamente, ej. Playwright).

Busca SOLO estos tipos de violaciones:
- `UNCLEAR_TEST_PURPOSE`: Test cuyo nombre y/o docstring no describen claramente qué comportamiento valida.
- `PAGE_OBJECT_DOES_TOO_MUCH`: Page Object con demasiadas responsabilidades (muchos métodos, múltiples páginas).
- `IMPLICIT_TEST_DEPENDENCY`: Tests que dependen del orden de ejecución o comparten estado mutable.
- `MISSING_WAIT_STRATEGY`: Interacciones con UI (click, fill, etc.) sin espera explícita previa.
- `MISSING_AAA_STRUCTURE`: Test que no sigue la estructura Arrange-Act-Assert. El código mezcla preparación, acción y verificación sin separación clara.
- `MIXED_ABSTRACTION_LEVEL`: Método de Page Object que mezcla keywords de negocio (login, add_to_cart) con selectores de UI directos (XPath, CSS selectors, By.ID).

Responde SOLO con un JSON array. Si no hay violaciones, responde con `[]`.
Cada violación debe tener este formato:
```json
[
  {{
    "type": "TIPO_DE_VIOLACION",
    "line": 42,
    "message": "Descripción breve del problema en español",
    "code_snippet": "la línea de código problemática"
  }}
]
```

Responde ÚNICAMENTE con el JSON, sin explicaciones adicionales."""

ENRICH_VIOLATION_PROMPT = """Se ha detectado la siguiente violación arquitectónica en un proyecto \
de test automation:

**Tipo**: `{violation_type}`
**Mensaje**: {violation_message}
**Archivo**: `{file_path}`
**Línea**: {line_number}
**Código**: `{code_snippet}`

**Contexto del archivo**:
```python
{file_content}
```

Genera una sugerencia breve (2-3 frases) en español que explique:
1. Por qué esto es un problema en la arquitectura gTAA
2. Cómo corregirlo concretamente en este contexto

Responde SOLO con la sugerencia, sin formato markdown ni prefijos."""
