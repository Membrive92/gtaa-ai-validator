"""
Parser de Java usando tree-sitter.

Extrae imports, clases, métodos y llamadas de archivos Java
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


class JavaParser(TreeSitterBaseParser):
    """
    Parser para archivos Java.

    Detecta:
    - Imports (import statements)
    - Clases y sus métodos
    - Anotaciones (@Test, @Before, etc.)
    - Llamadas a métodos (driver.findElement, etc.)
    - Strings literales
    """

    # Anotaciones de test en Java
    TEST_ANNOTATIONS = {"Test", "ParameterizedTest", "RepeatedTest", "TestFactory"}

    # Anotaciones de setup/teardown
    SETUP_ANNOTATIONS = {"Before", "BeforeEach", "BeforeAll", "BeforeClass"}
    TEARDOWN_ANNOTATIONS = {"After", "AfterEach", "AfterAll", "AfterClass"}

    def __init__(self):
        super().__init__("java")

    def extract_imports(self, root: Node, source: str) -> List[ParsedImport]:
        """Extrae import statements de Java."""
        imports = []

        for node in self.find_nodes_by_type(root, "import_declaration"):
            # Extraer el nombre del paquete/clase importado
            scoped_id = self.find_child_by_type(node, "scoped_identifier")
            if scoped_id:
                module = self.get_node_text(scoped_id, source)
                imports.append(ParsedImport(
                    module=module,
                    line=self.get_node_line(node),
                ))

        return imports

    def extract_classes(self, root: Node, source: str) -> List[ParsedClass]:
        """Extrae clases y sus métodos de Java."""
        classes = []

        for class_node in self.find_nodes_by_type(root, "class_declaration"):
            parsed_class = self._parse_class(class_node, source)
            if parsed_class:
                classes.append(parsed_class)

        return classes

    def _parse_class(self, class_node: Node, source: str) -> Optional[ParsedClass]:
        """Parsea una declaración de clase Java."""
        # Obtener nombre de la clase
        name_node = self.find_child_by_type(class_node, "identifier")
        if not name_node:
            return None

        class_name = self.get_node_text(name_node, source)

        # Obtener clases base (extends)
        base_classes = []
        superclass = self.find_child_by_type(class_node, "superclass")
        if superclass:
            type_id = self.find_child_by_type(superclass, "type_identifier")
            if type_id:
                base_classes.append(self.get_node_text(type_id, source))

        # Detectar si es un Page Object por nombre o herencia
        is_page_object = (
            "Page" in class_name or
            "PageObject" in class_name or
            any("Page" in bc for bc in base_classes)
        )

        # Extraer métodos de la clase
        methods = []
        body = self.find_child_by_type(class_node, "class_body")
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
        """Parsea una declaración de método Java."""
        # Obtener nombre del método
        name_node = self.find_child_by_type(method_node, "identifier")
        if not name_node:
            return None

        method_name = self.get_node_text(name_node, source)

        # Obtener anotaciones/decoradores
        decorators = []
        # Las anotaciones están antes del método en el padre
        parent = method_node.parent
        if parent:
            for sibling in parent.children:
                if sibling.type == "annotation" or sibling.type == "marker_annotation":
                    # Extraer nombre de la anotación
                    ann_name = self.find_child_by_type(sibling, "identifier")
                    if ann_name:
                        decorators.append(self.get_node_text(ann_name, source))
                if sibling == method_node:
                    break

        # También buscar anotaciones directamente asociadas
        for i, child in enumerate(method_node.parent.children if method_node.parent else []):
            if child == method_node and i > 0:
                prev = method_node.parent.children[i - 1]
                if prev.type in ("annotation", "marker_annotation"):
                    ann_name = self.find_child_by_type(prev, "identifier")
                    if ann_name and self.get_node_text(ann_name, source) not in decorators:
                        decorators.append(self.get_node_text(ann_name, source))

        # Buscar modifiers que contienen anotaciones
        modifiers = self.find_child_by_type(method_node, "modifiers")
        if modifiers:
            for ann in self.find_children_by_type(modifiers, "marker_annotation"):
                ann_name = self.find_child_by_type(ann, "identifier")
                if ann_name:
                    name = self.get_node_text(ann_name, source)
                    if name not in decorators:
                        decorators.append(name)
            for ann in self.find_children_by_type(modifiers, "annotation"):
                ann_name = self.find_child_by_type(ann, "identifier")
                if ann_name:
                    name = self.get_node_text(ann_name, source)
                    if name not in decorators:
                        decorators.append(name)

        # Obtener parámetros
        parameters = []
        params_node = self.find_child_by_type(method_node, "formal_parameters")
        if params_node:
            for param in self.find_children_by_type(params_node, "formal_parameter"):
                param_name = self.find_child_by_type(param, "identifier")
                if param_name:
                    parameters.append(self.get_node_text(param_name, source))

        return ParsedFunction(
            name=method_name,
            line_start=self.get_node_line(method_node),
            line_end=method_node.end_point[0] + 1,
            decorators=decorators,
            parameters=parameters,
        )

    def extract_top_level_functions(self, root: Node, source: str) -> List[ParsedFunction]:
        """Java no tiene funciones de nivel superior, retorna lista vacía."""
        return []

    def extract_calls(self, root: Node, source: str) -> List[ParsedCall]:
        """Extrae llamadas a métodos de Java."""
        calls = []

        for call_node in self.find_nodes_by_type(root, "method_invocation"):
            call = self._parse_method_call(call_node, source)
            if call:
                calls.append(call)

        return calls

    def _parse_method_call(self, call_node: Node, source: str) -> Optional[ParsedCall]:
        """Parsea una llamada a método Java."""
        full_text = self.get_node_text(call_node, source)

        # Buscar el objeto sobre el que se llama
        object_name = ""
        method_name = ""

        # Estructura: object.method(args)
        # En tree-sitter Java: field_access o identifier seguido de identifier
        for child in call_node.children:
            if child.type == "field_access":
                # objeto.campo o objeto.método
                obj = self.find_child_by_type(child, "identifier")
                if obj:
                    object_name = self.get_node_text(obj, source)
            elif child.type == "identifier":
                if not method_name:
                    # Primer identifier es el objeto o método
                    text = self.get_node_text(child, source)
                    if object_name:
                        method_name = text
                    else:
                        # Puede ser objeto o método solo
                        method_name = text
            elif child.type == "method_invocation":
                # Llamada encadenada
                pass

        # Intentar extraer de manera más robusta
        # Buscar patrón object.method
        if "." in full_text:
            parts = full_text.split("(")[0].split(".")
            if len(parts) >= 2:
                object_name = parts[-2].strip()
                method_name = parts[-1].strip()

        if method_name:
            return ParsedCall(
                object_name=object_name,
                method_name=method_name,
                line=self.get_node_line(call_node),
                full_text=full_text,
            )

        return None

    def extract_strings(self, root: Node, source: str) -> List[ParsedString]:
        """Extrae strings literales de Java."""
        strings = []

        for string_node in self.find_nodes_by_type(root, "string_literal"):
            value = self.get_node_text(string_node, source)
            # Quitar comillas
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            strings.append(ParsedString(
                value=value,
                line=self.get_node_line(string_node),
            ))

        return strings

    # --- Utilidades específicas de Java ---

    def is_test_method(self, func: ParsedFunction) -> bool:
        """Verifica si un método es un test (@Test, etc.)."""
        return any(d in self.TEST_ANNOTATIONS for d in func.decorators)

    def is_setup_method(self, func: ParsedFunction) -> bool:
        """Verifica si un método es setup (@Before, etc.)."""
        return any(d in self.SETUP_ANNOTATIONS for d in func.decorators)

    def is_teardown_method(self, func: ParsedFunction) -> bool:
        """Verifica si un método es teardown (@After, etc.)."""
        return any(d in self.TEARDOWN_ANNOTATIONS for d in func.decorators)

    def has_selenium_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de Selenium."""
        return any("selenium" in imp.module.lower() for imp in imports)

    def has_playwright_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de Playwright."""
        return any("playwright" in imp.module.lower() for imp in imports)

    def has_test_framework_imports(self, imports: List[ParsedImport]) -> bool:
        """Verifica si hay imports de frameworks de test (JUnit, TestNG)."""
        test_packages = {"org.junit", "org.testng", "org.junit.jupiter"}
        return any(
            any(pkg in imp.module for pkg in test_packages)
            for imp in imports
        )
