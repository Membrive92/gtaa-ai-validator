"""
Cliente mock LLM para análisis semántico.

Usa heurísticas deterministas (AST + regex) para simular detección
de violaciones semánticas y generación de sugerencias AI.
"""

import ast
from typing import List


class MockLLMClient:
    """
    Cliente mock que simula análisis LLM con heurísticas deterministas.

    Usa reglas simples (AST + regex) para producir resultados predecibles,
    permitiendo tests deterministas y demostración sin API key.
    """

    def analyze_file(self, file_content: str, file_path: str,
                     file_type: str = "unknown",
                     has_auto_wait: bool = False) -> List[dict]:
        """Detecta violaciones semánticas usando heurísticas."""
        violations = []

        try:
            tree = ast.parse(file_content)
        except SyntaxError:
            return []

        is_test_file = _is_test_file(file_path)
        is_page_object = _is_page_object(file_path)

        if is_test_file:
            violations.extend(self._check_unclear_test_purpose(tree, file_content))
            violations.extend(self._check_implicit_test_dependency(tree, file_content))
            violations.extend(self._check_missing_aaa_structure(tree, file_content))

        if is_page_object:
            violations.extend(self._check_page_object_too_much(tree, file_content))
            # MISSING_WAIT_STRATEGY no aplica a archivos API ni frameworks con auto-wait
            if file_type != "api" and not has_auto_wait:
                violations.extend(self._check_missing_wait_strategy(tree, file_content))
            violations.extend(self._check_mixed_abstraction_level(tree, file_content))

        return violations

    def enrich_violation(self, violation: dict, file_content: str) -> str:
        """Genera sugerencia contextual basada en el tipo de violación."""
        vtype = violation.get("type", "")
        message = violation.get("message", "")
        snippet = violation.get("code_snippet", "") or ""

        enrichments = {
            "ADAPTATION_IN_DEFINITION": (
                f"En este contexto, la llamada directa '{snippet}' debería encapsularse "
                "en un método del Page Object correspondiente. Esto mejora la "
                "mantenibilidad cuando cambien los selectores de la UI."
            ),
            "HARDCODED_TEST_DATA": (
                f"El dato '{snippet}' está embebido en el código. Considera crear "
                "un fichero de datos (JSON/YAML) o usar fixtures de pytest para "
                "parametrizar los tests con múltiples conjuntos de datos."
            ),
            "ASSERTION_IN_POM": (
                "Los Page Objects deben limitarse a interactuar con la UI y devolver "
                "valores. Mueve esta aserción al test que consume este Page Object."
            ),
            "FORBIDDEN_IMPORT": (
                "Esta importación rompe la separación de capas gTAA. Los Page Objects "
                "no deben conocer el framework de testing. Elimina esta dependencia."
            ),
            "BUSINESS_LOGIC_IN_POM": (
                "La lógica condicional en Page Objects dificulta el mantenimiento. "
                "Extrae esta lógica a un helper o servicio que el test invoque."
            ),
            "DUPLICATE_LOCATOR": (
                "Este localizador duplicado puede causar mantenimiento doble. "
                "Crea una clase base o un objeto de componente reutilizable."
            ),
            "LONG_TEST_FUNCTION": (
                "Un test largo suele indicar que verifica múltiples comportamientos. "
                "Divide en tests más pequeños, cada uno con un único assert."
            ),
            "POOR_TEST_NAMING": (
                "El nombre no describe qué comportamiento se valida. Usa el formato: "
                "test_<accion>_<condicion>_<resultado_esperado>."
            ),
            "MISSING_LAYER_STRUCTURE": (
                "Sin la estructura de capas, no hay separación entre definición, "
                "adaptación y ejecución. Crea los directorios tests/ y pages/."
            ),
            "GHERKIN_IMPLEMENTATION_DETAIL": (
                "Los archivos .feature deben usar lenguaje de negocio, no detalles técnicos. "
                "Mueve los selectores y URLs a las step definitions o Page Objects."
            ),
            "STEP_DEF_DIRECT_BROWSER_CALL": (
                f"La step definition llama directamente al navegador con '{snippet}'. "
                "Crea un Page Object que encapsule esta interacción."
            ),
            "STEP_DEF_TOO_COMPLEX": (
                "Una step definition larga indica que hace demasiado. Extrae la lógica "
                "a métodos de Page Object y deja el step como simple delegador."
            ),
            "MISSING_THEN_STEP": (
                "Un Scenario sin step Then no verifica ningún resultado. Añade "
                "al menos un Then que valide el comportamiento esperado."
            ),
            "DUPLICATE_STEP_PATTERN": (
                "Este step pattern está duplicado en otro archivo. Consolida "
                "en un archivo compartido de steps para evitar mantenimiento doble."
            ),
        }

        if vtype in enrichments:
            return enrichments[vtype]

        return (
            f"Violación '{vtype}' detectada: {message}. "
            "Revisa la documentación gTAA para corregir este patrón."
        )

    # --- Heurísticas internas ---

    def _check_unclear_test_purpose(
        self, tree: ast.Module, source: str
    ) -> List[dict]:
        """Tests sin docstring y con nombre corto → UNCLEAR_TEST_PURPOSE."""
        violations = []
        lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue

            has_docstring = (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            )

            if not has_docstring and len(node.name) < 20:
                line_text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                violations.append({
                    "type": "UNCLEAR_TEST_PURPOSE",
                    "line": node.lineno,
                    "message": (
                        f"El test '{node.name}' no tiene docstring y su nombre "
                        "es demasiado corto para describir su propósito"
                    ),
                    "code_snippet": line_text,
                })

        return violations

    def _check_page_object_too_much(
        self, tree: ast.Module, source: str
    ) -> List[dict]:
        """Clases con >10 métodos públicos → PAGE_OBJECT_DOES_TOO_MUCH."""
        violations = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            public_methods = [
                n for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not n.name.startswith("_")
            ]

            if len(public_methods) > 10:
                violations.append({
                    "type": "PAGE_OBJECT_DOES_TOO_MUCH",
                    "line": node.lineno,
                    "message": (
                        f"La clase '{node.name}' tiene {len(public_methods)} métodos "
                        "públicos. Considerar dividir en componentes más pequeños"
                    ),
                    "code_snippet": f"class {node.name}: # {len(public_methods)} métodos públicos",
                })

        return violations

    def _check_implicit_test_dependency(
        self, tree: ast.Module, source: str
    ) -> List[dict]:
        """Variables globales mutables en módulos de test → IMPLICIT_TEST_DEPENDENCY."""
        violations = []
        lines = source.splitlines()

        for node in ast.iter_child_nodes(tree):
            # Buscar asignaciones a nivel de módulo (no dentro de funciones/clases)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Ignorar constantes (MAYÚSCULAS) y variables privadas típicas
                        if name.isupper() or name.startswith("_"):
                            continue
                        # Ignorar asignaciones simples de tipo (type hints)
                        line_text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                        violations.append({
                            "type": "IMPLICIT_TEST_DEPENDENCY",
                            "line": node.lineno,
                            "message": (
                                f"Variable mutable '{name}' a nivel de módulo puede "
                                "crear dependencias implícitas entre tests"
                            ),
                            "code_snippet": line_text,
                        })

        return violations

    def _check_missing_wait_strategy(
        self, tree: ast.Module, source: str
    ) -> List[dict]:
        """Llamadas click/fill sin wait previo → MISSING_WAIT_STRATEGY."""
        violations = []
        lines = source.splitlines()
        interaction_methods = {"click", "fill", "type", "send_keys", "submit", "clear"}

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in interaction_methods:
                continue

            # Verificar si hay una espera en las ~5 líneas anteriores
            line_no = node.lineno
            preceding = source.splitlines()[max(0, line_no - 6):line_no - 1]
            preceding_text = "\n".join(preceding).lower()

            has_wait = any(
                kw in preceding_text
                for kw in ["wait", "sleep", "expect", "until", "waitfor", "wait_for"]
            )

            if not has_wait:
                line_text = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                violations.append({
                    "type": "MISSING_WAIT_STRATEGY",
                    "line": line_no,
                    "message": (
                        f"Llamada a '{node.func.attr}()' sin espera explícita previa"
                    ),
                    "code_snippet": line_text,
                })

        return violations

    def _check_missing_aaa_structure(
        self, tree: ast.Module, source: str
    ) -> List[dict]:
        """Tests sin aserciones → MISSING_AAA_STRUCTURE."""
        violations = []
        lines = source.splitlines()
        assert_keywords = {"assert", "assertEqual", "assertTrue", "assertFalse",
                           "assertIn", "assertRaises", "assertIsNone", "assertIsNotNone",
                           "assert_called", "assert_called_once", "assert_called_with"}

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue

            # Check if test body contains any assert
            func_source = "\n".join(
                lines[node.lineno - 1:node.end_lineno] if hasattr(node, "end_lineno") and node.end_lineno
                else lines[node.lineno - 1:node.lineno + 10]
            )

            has_assert = any(kw in func_source for kw in assert_keywords)
            if not has_assert:
                line_text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                violations.append({
                    "type": "MISSING_AAA_STRUCTURE",
                    "line": node.lineno,
                    "message": (
                        f"El test '{node.name}' no contiene aserciones visibles. "
                        "Un test debe tener una fase Assert clara"
                    ),
                    "code_snippet": line_text,
                })

        return violations

    def _check_mixed_abstraction_level(
        self, tree: ast.Module, source: str
    ) -> List[dict]:
        """Métodos públicos en Page Objects con selectores directos → MIXED_ABSTRACTION_LEVEL."""
        import re as _re
        violations = []
        lines = source.splitlines()
        selector_patterns = [
            r'//[\w\[\]@=\'"]+',       # XPath
            r'css=',                     # CSS selector prefix
            r'By\.\w+',                  # Selenium By.*
            r'\[data-[\w-]+',            # data attributes
            r'#[\w-]+',                  # CSS id selector
        ]
        selector_regex = _re.compile('|'.join(selector_patterns))

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                # Only public methods (not starting with _)
                if item.name.startswith("_"):
                    continue
                func_lines = lines[item.lineno - 1:item.end_lineno] if hasattr(item, "end_lineno") and item.end_lineno else lines[item.lineno - 1:item.lineno + 10]
                func_source = "\n".join(func_lines)
                if selector_regex.search(func_source):
                    line_text = lines[item.lineno - 1].strip() if item.lineno <= len(lines) else ""
                    violations.append({
                        "type": "MIXED_ABSTRACTION_LEVEL",
                        "line": item.lineno,
                        "message": (
                            f"El método '{item.name}' mezcla lógica de negocio con "
                            "selectores de UI directos"
                        ),
                        "code_snippet": line_text,
                    })

        return violations

# --- Utilidades ---

def _is_test_file(file_path: str) -> bool:
    """Determina si un fichero es un archivo de test."""
    path_lower = file_path.lower().replace("\\", "/")
    name = path_lower.split("/")[-1] if "/" in path_lower else path_lower
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or "/tests/" in path_lower
        or "/test/" in path_lower
    )


def _is_page_object(file_path: str) -> bool:
    """Determina si un fichero es un Page Object."""
    path_lower = file_path.lower().replace("\\", "/")
    name = path_lower.split("/")[-1] if "/" in path_lower else path_lower
    return (
        name.endswith("_page.py")
        or name.endswith("_pom.py")
        or "/pages/" in path_lower
        or "/page_objects/" in path_lower
        or "/pom/" in path_lower
    )
