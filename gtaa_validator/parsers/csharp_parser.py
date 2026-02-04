"""
Parser de C# usando tree-sitter.

Extrae usings, clases, métodos y llamadas de archivos C#
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


class CSharpParser(TreeSitterBaseParser):
    """
    Parser para archivos C#.

    Detecta:
    - Using directives (imports)
    - Clases y sus métodos
    - Atributos ([Test], [SetUp], etc.)
    - Llamadas a métodos (driver.FindElement, etc.)
    - Strings literales
    """

    # Atributos de test en C# (NUnit, xUnit, MSTest)
    TEST_ATTRIBUTES = {
        "Test", "TestCase", "TestCaseSource",  # NUnit
        "Fact", "Theory",  # xUnit
        "TestMethod", "DataTestMethod",  # MSTest
    }

    # Atributos de setup/teardown
    SETUP_ATTRIBUTES = {
        "SetUp", "OneTimeSetUp",  # NUnit
        "TestInitialize", "ClassInitialize",  # MSTest
    }
    TEARDOWN_ATTRIBUTES = {
        "TearDown", "OneTimeTearDown",  # NUnit
        "TestCleanup", "ClassCleanup",  # MSTest
    }

    def __init__(self):
        super().__init__("c_sharp")

    def extract_imports(self, root: Node, source: str) -> List[ParsedImport]:
        """Extrae using directives de C#."""
        imports = []

        for node in self.find_nodes_by_type(root, "using_directive"):
            # Extraer el namespace
            namespace = self._extract_namespace(node, source)
            if namespace:
                imports.append(ParsedImport(
                    module=namespace,
                    line=self.get_node_line(node),
                ))

        return imports

    def _extract_namespace(self, using_node: Node, source: str) -> Optional[str]:
        """Extrae el namespace de un using directive."""
        # Buscar qualified_name o identifier
        qualified = self.find_child_by_type(using_node, "qualified_name")
        if qualified:
            return self.get_node_text(qualified, source)

        identifier = self.find_child_by_type(using_node, "identifier")
        if identifier:
            return self.get_node_text(identifier, source)

        # Fallback: extraer texto entre "using" y ";"
        text = self.get_node_text(using_node, source)
        if text.startswith("using ") and text.endswith(";"):
            return text[6:-1].strip()

        return None

    def extract_classes(self, root: Node, source: str) -> List[ParsedClass]:
        """Extrae clases de C#."""
        classes = []

        for class_node in self.find_nodes_by_type(root, "class_declaration"):
            parsed_class = self._parse_class(class_node, source)
            if parsed_class:
                classes.append(parsed_class)

        return classes

    def _parse_class(self, class_node: Node, source: str) -> Optional[ParsedClass]:
        """Parsea una declaración de clase C#."""
        # Obtener nombre
        name_node = self.find_child_by_type(class_node, "identifier")
        if not name_node:
            return None

        class_name = self.get_node_text(name_node, source)

        # Obtener clases base
        base_classes = []
        base_list = self.find_child_by_type(class_node, "base_list")
        if base_list:
            for base_type in self.find_children_by_type(base_list, "identifier"):
                base_classes.append(self.get_node_text(base_type, source))

        # Detectar si es Page Object
        is_page_object = (
            "Page" in class_name or
            "PageObject" in class_name or
            any("Page" in bc for bc in base_classes)
        )

        # Extraer métodos
        methods = []
        body = self.find_child_by_type(class_node, "declaration_list")
        if body:
            for method_node in self.find_children_by_type(body, "method_declaration"):
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
        """Parsea una declaración de método C#."""
        # Obtener nombre
        name_node = self.find_child_by_type(method_node, "identifier")
        if not name_node:
            return None

        method_name = self.get_node_text(name_node, source)

        # Obtener atributos/decoradores
        decorators = self._extract_attributes(method_node, source)

        # Detectar si es async
        is_async = any(
            child.type == "modifier" and self.get_node_text(child, source) == "async"
            for child in method_node.children
        )

        # Obtener parámetros
        parameters = self._extract_parameters(method_node, source)

        # Obtener body
        body_node = self.find_child_by_type(method_node, "block")

        return ParsedFunction(
            name=method_name,
            line_start=self.get_node_line(method_node),
            line_end=method_node.end_point[0] + 1,
            decorators=decorators,
            parameters=parameters,
            is_async=is_async,
            body_node=body_node,
        )

    def _extract_attributes(self, node: Node, source: str) -> List[str]:
        """Extrae atributos ([Test], [SetUp], etc.) de un nodo."""
        attributes = []

        # Buscar attribute_list en el nodo o sus hermanos anteriores
        for child in node.children:
            if child.type == "attribute_list":
                for attr in self.find_children_by_type(child, "attribute"):
                    name_node = self.find_child_by_type(attr, "identifier")
                    if name_node:
                        attributes.append(self.get_node_text(name_node, source))

        # También buscar en el padre (los atributos pueden estar antes del método)
        if node.parent:
            idx = node.parent.children.index(node) if node in node.parent.children else -1
            if idx > 0:
                for i in range(idx - 1, -1, -1):
                    sibling = node.parent.children[i]
                    if sibling.type == "attribute_list":
                        for attr in self.find_children_by_type(sibling, "attribute"):
                            name_node = self.find_child_by_type(attr, "identifier")
                            if name_node:
                                attr_name = self.get_node_text(name_node, source)
                                if attr_name not in attributes:
                                    attributes.append(attr_name)
                    else:
                        break

        return attributes

    def _extract_parameters(self, method_node: Node, source: str) -> List[str]:
        """Extrae nombres de parámetros de un método."""
        parameters = []
        params_list = self.find_child_by_type(method_node, "parameter_list")
        if params_list:
            for param in self.find_children_by_type(params_list, "parameter"):
                name_node = self.find_child_by_type(param, "identifier")
                if name_node:
                    parameters.append(self.get_node_text(name_node, source))
        return parameters

    def extract_top_level_functions(self, root: Node, source: str) -> List[ParsedFunction]:
        """C# tradicionalmente no tiene funciones top-level (antes de C# 9)."""
        # C# 9+ soporta top-level statements, pero son raros en test automation
        return []

    def extract_calls(self, root: Node, source: str) -> List[ParsedCall]:
        """Extrae llamadas a métodos de C#."""
        calls = []

        for call_node in self.find_nodes_by_type(root, "invocation_expression"):
            call = self._parse_call(call_node, source)
            if call:
                calls.append(call)

        return calls

    def _parse_call(self, call_node: Node, source: str) -> Optional[ParsedCall]:
        """Parsea una llamada a método C#."""
        full_text = self.get_node_text(call_node, source)
        object_name = ""
        method_name = ""

        # Buscar member_access_expression para objeto.método
        member_access = self.find_child_by_type(call_node, "member_access_expression")
        if member_access:
            # Extraer objeto y método
            children = list(member_access.children)
            if len(children) >= 2:
                obj_node = children[0]
                method_node = children[-1]

                if obj_node.type == "identifier":
                    object_name = self.get_node_text(obj_node, source)
                elif obj_node.type == "member_access_expression":
                    # Cadena de llamadas
                    inner_id = self.find_child_by_type(obj_node, "identifier")
                    if inner_id:
                        object_name = self.get_node_text(inner_id, source)

                if method_node.type == "identifier":
                    method_name = self.get_node_text(method_node, source)

        # Si no hay member_access, puede ser una llamada directa
        if not method_name:
            id_node = self.find_child_by_type(call_node, "identifier")
            if id_node:
                method_name = self.get_node_text(id_node, source)

        if method_name or object_name:
            return ParsedCall(
                object_name=object_name,
                method_name=method_name,
                line=self.get_node_line(call_node),
                full_text=full_text[:100],
            )

        return None

    def extract_strings(self, root: Node, source: str) -> List[ParsedString]:
        """Extrae strings literales de C#."""
        strings = []

        # String literals regulares
        for string_node in self.find_nodes_by_type(root, "string_literal"):
            value = self.get_node_text(string_node, source)
            # Quitar comillas
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith('@"') and value.endswith('"'):
                value = value[2:-1]
            strings.append(ParsedString(
                value=value,
                line=self.get_node_line(string_node),
            ))

        # Interpolated strings
        for interp_node in self.find_nodes_by_type(root, "interpolated_string_expression"):
            value = self.get_node_text(interp_node, source)
            if value.startswith('$"') and value.endswith('"'):
                value = value[2:-1]
            strings.append(ParsedString(
                value=value,
                line=self.get_node_line(interp_node),
            ))

        return strings

    # --- Utilidades específicas de C# ---

    def is_test_method(self, func: ParsedFunction) -> bool:
        """Verifica si un método es un test ([Test], [Fact], etc.)."""
        return any(d in self.TEST_ATTRIBUTES for d in func.decorators)

    def is_setup_method(self, func: ParsedFunction) -> bool:
        """Verifica si un método es setup ([SetUp], etc.)."""
        return any(d in self.SETUP_ATTRIBUTES for d in func.decorators)

    def is_teardown_method(self, func: ParsedFunction) -> bool:
        """Verifica si un método es teardown ([TearDown], etc.)."""
        return any(d in self.TEARDOWN_ATTRIBUTES for d in func.decorators)

    def has_selenium_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay usings de Selenium."""
        return any("OpenQA.Selenium" in imp.module for imp in imports)

    def has_playwright_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay usings de Playwright."""
        return any("Microsoft.Playwright" in imp.module for imp in imports)

    def has_test_framework_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay usings de frameworks de test."""
        test_namespaces = {"NUnit.Framework", "Xunit", "Microsoft.VisualStudio.TestTools"}
        return any(
            any(ns in imp.module for ns in test_namespaces)
            for imp in imports
        )

    def is_browser_api_call(self, call: ParsedCall) -> bool:
        """Verifica si es una llamada directa a API de browser."""
        browser_objects = {"driver", "_driver", "Driver", "WebDriver", "page", "Page"}
        browser_methods = {
            "FindElement", "FindElements", "Navigate", "SwitchTo",
            "Click", "SendKeys", "Clear", "Submit",
            "Locator", "GetByRole", "GetByText",
        }
        return call.object_name in browser_objects or call.method_name in browser_methods
