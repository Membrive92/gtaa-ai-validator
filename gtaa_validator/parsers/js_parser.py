"""
Parser de JavaScript/TypeScript usando tree-sitter.

Extrae imports, funciones, clases y llamadas de archivos JS/TS
para análisis de violaciones gTAA.

Fase 9: Soporte multilenguaje.
"""

from typing import List, Optional
from tree_sitter import Node

from gtaa_validator.parsers.treesitter_base import (
    TreeSitterBaseParser,
    ParsedImport,
    ParsedClass,
    ParsedFunction,
    ParsedCall,
    ParsedString,
)


class JSParser(TreeSitterBaseParser):
    """
    Parser para archivos JavaScript y TypeScript.

    Detecta:
    - Imports (ES6 import, require)
    - Clases y sus métodos
    - Funciones (declaraciones, arrow functions)
    - Llamadas de test (describe, it, test)
    - Llamadas a browser APIs (cy.get, page.locator, etc.)
    - Strings literales
    """

    # Funciones de test en frameworks JS
    TEST_FUNCTIONS = {"it", "test", "specify"}
    SUITE_FUNCTIONS = {"describe", "context", "suite"}
    HOOK_FUNCTIONS = {"before", "beforeEach", "beforeAll", "after", "afterEach", "afterAll"}

    def __init__(self, language: str = "javascript"):
        """
        Inicializa el parser JS/TS.

        Args:
            language: "javascript" o "typescript"
        """
        super().__init__(language)

    def extract_imports(self, root: Node, source: str) -> List[ParsedImport]:
        """Extrae imports de JavaScript/TypeScript."""
        imports = []

        # ES6 imports: import X from 'module'
        for node in self.find_nodes_by_type(root, "import_statement"):
            module = self._extract_import_source(node, source)
            if module:
                imports.append(ParsedImport(
                    module=module,
                    line=self.get_node_line(node),
                ))

        # CommonJS require: const X = require('module')
        for node in self.find_nodes_by_type(root, "call_expression"):
            func = self.find_child_by_type(node, "identifier")
            if func and self.get_node_text(func, source) == "require":
                args = self.find_child_by_type(node, "arguments")
                if args:
                    string_node = self.find_child_by_type(args, "string")
                    if string_node:
                        module = self.get_node_text(string_node, source).strip("'\"")
                        imports.append(ParsedImport(
                            module=module,
                            line=self.get_node_line(node),
                        ))

        return imports

    def _extract_import_source(self, import_node: Node, source: str) -> Optional[str]:
        """Extrae el módulo de un import statement."""
        # Buscar el string del módulo
        string_node = self.find_child_by_type(import_node, "string")
        if string_node:
            return self.get_node_text(string_node, source).strip("'\"")
        return None

    def extract_classes(self, root: Node, source: str) -> List[ParsedClass]:
        """Extrae clases de JavaScript/TypeScript."""
        classes = []

        for class_node in self.find_nodes_by_type(root, "class_declaration"):
            parsed_class = self._parse_class(class_node, source)
            if parsed_class:
                classes.append(parsed_class)

        # También class expressions: const X = class {}
        for class_node in self.find_nodes_by_type(root, "class"):
            parsed_class = self._parse_class(class_node, source)
            if parsed_class:
                classes.append(parsed_class)

        return classes

    def _parse_class(self, class_node: Node, source: str) -> Optional[ParsedClass]:
        """Parsea una declaración de clase JS/TS."""
        # Obtener nombre
        name_node = self.find_child_by_type(class_node, "identifier")
        class_name = self.get_node_text(name_node, source) if name_node else "AnonymousClass"

        # Obtener clase base (extends)
        base_classes = []
        heritage = self.find_child_by_type(class_node, "class_heritage")
        if heritage:
            extends_clause = self.find_child_by_type(heritage, "extends_clause")
            if extends_clause:
                base_id = self.find_child_by_type(extends_clause, "identifier")
                if base_id:
                    base_classes.append(self.get_node_text(base_id, source))

        # Detectar si es Page Object
        is_page_object = (
            "Page" in class_name or
            "PageObject" in class_name or
            any("Page" in bc for bc in base_classes)
        )

        # Extraer métodos
        methods = []
        body = self.find_child_by_type(class_node, "class_body")
        if body:
            for method_node in self.find_children_by_type(body, "method_definition"):
                method = self._parse_method(method_node, source)
                if method:
                    methods.append(method)

        return ParsedClass(
            name=class_name,
            line_start=self.get_node_line(class_node),
            line_end=class_node.end_point[0] + 1,
            methods=methods,
            base_classes=base_classes,
            is_page_object=is_page_object,
        )

    def _parse_method(self, method_node: Node, source: str) -> Optional[ParsedFunction]:
        """Parsea un método de clase JS/TS."""
        name_node = self.find_child_by_type(method_node, "property_identifier")
        if not name_node:
            name_node = self.find_child_by_type(method_node, "identifier")
        if not name_node:
            return None

        method_name = self.get_node_text(name_node, source)

        # Detectar si es async
        is_async = any(
            child.type == "async" or self.get_node_text(child, source) == "async"
            for child in method_node.children
        )

        # Obtener parámetros
        parameters = self._extract_parameters(method_node, source)

        return ParsedFunction(
            name=method_name,
            line_start=self.get_node_line(method_node),
            line_end=method_node.end_point[0] + 1,
            decorators=[],  # JS no tiene decoradores nativos (pero TS sí)
            parameters=parameters,
            is_async=is_async,
            body_node=self.find_child_by_type(method_node, "statement_block"),
        )

    def extract_top_level_functions(self, root: Node, source: str) -> List[ParsedFunction]:
        """Extrae funciones de nivel superior de JS/TS."""
        functions = []

        # Function declarations: function foo() {}
        for func_node in self.find_nodes_by_type(root, "function_declaration"):
            func = self._parse_function(func_node, source)
            if func:
                functions.append(func)

        # Arrow functions asignadas: const foo = () => {}
        for var_decl in self.find_nodes_by_type(root, "variable_declarator"):
            init = self.find_child_by_type(var_decl, "arrow_function")
            if init:
                name_node = self.find_child_by_type(var_decl, "identifier")
                if name_node:
                    func = self._parse_arrow_function(init, source, self.get_node_text(name_node, source))
                    if func:
                        functions.append(func)

        return functions

    def _parse_function(self, func_node: Node, source: str) -> Optional[ParsedFunction]:
        """Parsea una declaración de función JS/TS."""
        name_node = self.find_child_by_type(func_node, "identifier")
        if not name_node:
            return None

        func_name = self.get_node_text(name_node, source)
        is_async = any(child.type == "async" for child in func_node.children)
        parameters = self._extract_parameters(func_node, source)

        return ParsedFunction(
            name=func_name,
            line_start=self.get_node_line(func_node),
            line_end=func_node.end_point[0] + 1,
            decorators=[],
            parameters=parameters,
            is_async=is_async,
            body_node=self.find_child_by_type(func_node, "statement_block"),
        )

    def _parse_arrow_function(self, arrow_node: Node, source: str, name: str) -> Optional[ParsedFunction]:
        """Parsea una arrow function."""
        is_async = any(child.type == "async" for child in arrow_node.children)
        parameters = self._extract_parameters(arrow_node, source)

        return ParsedFunction(
            name=name,
            line_start=self.get_node_line(arrow_node),
            line_end=arrow_node.end_point[0] + 1,
            decorators=[],
            parameters=parameters,
            is_async=is_async,
            body_node=self.find_child_by_type(arrow_node, "statement_block"),
        )

    def _extract_parameters(self, node: Node, source: str) -> List[str]:
        """Extrae los nombres de parámetros de una función."""
        parameters = []
        params_node = self.find_child_by_type(node, "formal_parameters")
        if params_node:
            for param in params_node.children:
                if param.type == "identifier":
                    parameters.append(self.get_node_text(param, source))
                elif param.type == "required_parameter" or param.type == "optional_parameter":
                    id_node = self.find_child_by_type(param, "identifier")
                    if id_node:
                        parameters.append(self.get_node_text(id_node, source))
        return parameters

    def extract_calls(self, root: Node, source: str) -> List[ParsedCall]:
        """Extrae llamadas a funciones/métodos de JS/TS."""
        calls = []

        for call_node in self.find_nodes_by_type(root, "call_expression"):
            call = self._parse_call(call_node, source)
            if call:
                calls.append(call)

        return calls

    def _parse_call(self, call_node: Node, source: str) -> Optional[ParsedCall]:
        """Parsea una llamada a función/método."""
        full_text = self.get_node_text(call_node, source)
        object_name = ""
        method_name = ""

        # Buscar el callee (función/método que se llama)
        callee = call_node.children[0] if call_node.children else None

        if callee:
            if callee.type == "member_expression":
                # objeto.método
                obj = self.find_child_by_type(callee, "identifier")
                prop = self.find_child_by_type(callee, "property_identifier")
                if obj:
                    object_name = self.get_node_text(obj, source)
                if prop:
                    method_name = self.get_node_text(prop, source)
                # Manejar cadenas: cy.get().click()
                if not obj:
                    inner_call = self.find_child_by_type(callee, "call_expression")
                    if inner_call:
                        inner_member = self.find_child_by_type(inner_call, "member_expression")
                        if inner_member:
                            inner_obj = self.find_child_by_type(inner_member, "identifier")
                            if inner_obj:
                                object_name = self.get_node_text(inner_obj, source)

            elif callee.type == "identifier":
                # función directa
                method_name = self.get_node_text(callee, source)

        if method_name or object_name:
            return ParsedCall(
                object_name=object_name,
                method_name=method_name,
                line=self.get_node_line(call_node),
                full_text=full_text[:100],  # Limitar longitud
            )

        return None

    def extract_strings(self, root: Node, source: str) -> List[ParsedString]:
        """Extrae strings literales de JS/TS."""
        strings = []

        # String literals
        for string_node in self.find_nodes_by_type(root, "string"):
            value = self.get_node_text(string_node, source)
            # Quitar comillas
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            strings.append(ParsedString(
                value=value,
                line=self.get_node_line(string_node),
            ))

        # Template literals
        for template_node in self.find_nodes_by_type(root, "template_string"):
            value = self.get_node_text(template_node, source)
            if value.startswith("`") and value.endswith("`"):
                value = value[1:-1]
            strings.append(ParsedString(
                value=value,
                line=self.get_node_line(template_node),
            ))

        return strings

    # --- Utilidades específicas de JS/TS ---

    def is_test_call(self, call: ParsedCall) -> bool:
        """Verifica si una llamada es un test (it, test)."""
        return call.method_name in self.TEST_FUNCTIONS or \
               (not call.object_name and call.method_name in self.TEST_FUNCTIONS)

    def is_suite_call(self, call: ParsedCall) -> bool:
        """Verifica si una llamada es una suite (describe)."""
        return call.method_name in self.SUITE_FUNCTIONS

    def is_hook_call(self, call: ParsedCall) -> bool:
        """Verifica si una llamada es un hook (before, after)."""
        return call.method_name in self.HOOK_FUNCTIONS

    def has_cypress_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de Cypress."""
        return any("cypress" in imp.module.lower() for imp in imports)

    def has_playwright_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de Playwright."""
        return any("playwright" in imp.module.lower() for imp in imports)

    def has_webdriverio_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de WebdriverIO."""
        return any("webdriverio" in imp.module.lower() or "wdio" in imp.module.lower() for imp in imports)

    def is_cypress_call(self, call: ParsedCall) -> bool:
        """Verifica si es una llamada de Cypress (cy.*)."""
        return call.object_name == "cy"

    def is_playwright_call(self, call: ParsedCall) -> bool:
        """Verifica si es una llamada de Playwright (page.*)."""
        return call.object_name in ("page", "browser", "context")

    def is_browser_api_call(self, call: ParsedCall) -> bool:
        """Verifica si es una llamada directa a API de browser."""
        browser_objects = {"cy", "page", "browser", "driver", "$", "$$"}
        browser_methods = {
            "get", "locator", "getByRole", "getByText", "getByTestId",
            "click", "fill", "type", "check", "select", "wait",
            "findElement", "findElements", "querySelector", "querySelectorAll",
        }
        return call.object_name in browser_objects or call.method_name in browser_methods
