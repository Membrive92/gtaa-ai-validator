"""
Templates de prompts para análisis semántico con LLM.

Optimizados para reducir tokens (~40% menos) manteniendo precisión.
"""

# System prompt comprimido (~40% menos tokens)
SYSTEM_PROMPT = """Experto en gTAA (generic Test Automation Architecture).
Capas: tests/ (definición), pages/ (adaptación/Page Objects), steps/ (BDD).
Reglas: tests independientes, Page Objects con responsabilidad única, step definitions delegan a PO."""

# Prompt para análisis de archivo - optimizado
ANALYZE_FILE_PROMPT = """Analiza código de test automation y detecta violaciones gTAA.

Archivo: `{file_path}` | Tipo: {file_type} | Auto-wait: {has_auto_wait}

```
{file_content}
```

Violaciones válidas:
- UNCLEAR_TEST_PURPOSE: nombre/docstring no describe comportamiento
- PAGE_OBJECT_DOES_TOO_MUCH: PO con muchas responsabilidades
- IMPLICIT_TEST_DEPENDENCY: tests dependen del orden
- MISSING_WAIT_STRATEGY: UI sin espera (ignorar si api o auto-wait=sí)
- MISSING_AAA_STRUCTURE: test sin Arrange-Act-Assert claro
- MIXED_ABSTRACTION_LEVEL: PO mezcla keywords con selectores
- STEP_DEF_DIRECT_BROWSER_CALL: step llama browser directo
- STEP_DEF_TOO_COMPLEX: step >15 líneas

Responde SOLO JSON: [{{"type":"X","line":N,"message":"...","code_snippet":"..."}}] o []"""

# Prompt para enriquecimiento - optimizado (solo contexto relevante)
# Usa {context_snippet} en lugar de {file_content} para reducir tokens
ENRICH_VIOLATION_PROMPT = """Violación gTAA detectada:
Tipo: {violation_type} | Archivo: {file_path}:{line_number}
Código: `{code_snippet}`
Mensaje: {violation_message}

Contexto:
```
{context_snippet}
```

Genera sugerencia breve (2 frases): por qué es problema + cómo corregirlo."""


def extract_context_snippet(file_content: str, line_number: int, context_lines: int = 5) -> str:
    """
    Extrae solo las líneas relevantes alrededor de la violación.

    Reduce tokens enviando solo el contexto necesario en lugar del archivo completo.

    Args:
        file_content: Contenido completo del archivo
        line_number: Línea de la violación
        context_lines: Líneas antes y después a incluir

    Returns:
        Fragmento de código con contexto
    """
    if not line_number:
        # Sin número de línea, enviar primeras 30 líneas
        lines = file_content.split('\n')[:30]
        return '\n'.join(lines)

    lines = file_content.split('\n')
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)

    snippet_lines = []
    for i, line in enumerate(lines[start:end], start=start + 1):
        prefix = ">>> " if i == line_number else "    "
        snippet_lines.append(f"{prefix}{i}: {line}")

    return '\n'.join(snippet_lines)


def extract_functions_from_code(file_content: str, max_chars: int = 3000) -> str:
    """
    Extrae solo las funciones/métodos del código si el archivo es muy grande.

    Para archivos grandes, envía solo las firmas de funciones y código sospechoso.

    Args:
        file_content: Contenido completo del archivo
        max_chars: Máximo de caracteres a enviar

    Returns:
        Código reducido o completo si es pequeño
    """
    if len(file_content) <= max_chars:
        return file_content

    # Archivo grande: extraer solo definiciones de funciones/clases
    import re

    # Patrones para extraer estructuras importantes
    patterns = [
        r'^(class\s+\w+.*?:)',  # Definiciones de clase
        r'^(\s*def\s+\w+.*?:)',  # Definiciones de función
        r'^(\s*async\s+def\s+\w+.*?:)',  # Funciones async
        r'^(\s*@\w+.*?)$',  # Decoradores
    ]

    lines = file_content.split('\n')
    important_lines = []

    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.match(pattern, line):
                # Incluir línea y siguientes 5 líneas (cuerpo de función)
                important_lines.extend(lines[i:min(i+6, len(lines))])
                break

    result = '\n'.join(important_lines)

    # Si sigue siendo muy grande, truncar
    if len(result) > max_chars:
        result = result[:max_chars] + "\n... [truncado]"

    return result if result else file_content[:max_chars] + "\n... [truncado]"
