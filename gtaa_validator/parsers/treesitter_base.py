"""
Parser base usando tree-sitter para análisis multi-lenguaje.

Proporciona estructuras de datos comunes y métodos base para extraer
información de código fuente en Java, JavaScript/TypeScript y C#.

Fase 9: Soporte multilenguaje.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from gtaa_validator.file_utils import read_file_safe

# tree-sitter imports
from tree_sitter import Parser, Language, Node


@dataclass
class ParsedImport:
    """Representa un import/using extraído del código."""
    module: str  # ej: "org.openqa.selenium", "@playwright/test"
    line: int
    alias: Optional[str] = None  # ej: "import X as Y"


@dataclass
class ParsedFunction:
    """Representa una función o método extraído del código."""
    name: str
    line_start: int
    line_end: int
    decorators: List[str] = field(default_factory=list)  # @Test, @given, etc.
    parameters: List[str] = field(default_factory=list)
    is_async: bool = False


@dataclass
class ParsedClass:
    """Representa una clase extraída del código."""
    name: str
    line_start: int
    line_end: int
    methods: List[ParsedFunction] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)  # Clases padre
    is_page_object: bool = False  # Heurística: *Page, *PageObject


@dataclass
class ParsedCall:
    """Representa una llamada a método/función extraída del código."""
    object_name: str  # driver, page, cy, browser, this
    method_name: str  # findElement, locator, get
    line: int
    full_text: str = ""  # Texto completo de la llamada


@dataclass
class ParsedString:
    """Representa un string literal extraído del código."""
    value: str
    line: int


@dataclass
class ParseResult:
    """Resultado completo del parsing de un archivo."""
    imports: List[ParsedImport] = field(default_factory=list)
    classes: List[ParsedClass] = field(default_factory=list)
    functions: List[ParsedFunction] = field(default_factory=list)  # Top-level functions
    calls: List[ParsedCall] = field(default_factory=list)
    strings: List[ParsedString] = field(default_factory=list)
    language: str = "unknown"
    parse_errors: List[str] = field(default_factory=list)


class TreeSitterBaseParser(ABC):
    """
    Parser base abstracto usando tree-sitter.

    Subclases deben implementar métodos específicos para cada lenguaje.
    """

    # Extensiones soportadas por cada lenguaje
    LANGUAGE_EXTENSIONS: Dict[str, List[str]] = {
        "java": [".java"],
        "javascript": [".js", ".mjs", ".cjs", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "c_sharp": [".cs"],
    }

    def __init__(self, language: str):
        """
        Inicializa el parser para un lenguaje específico.

        Args:
            language: Nombre del lenguaje (java, javascript, typescript, c_sharp)
        """
        self.language = language
        self._parser = self._create_parser(language)

    def _create_parser(self, language: str) -> Parser:
        """Crea el parser tree-sitter para el lenguaje especificado."""
        if language == "c_sharp":
            # C# usa paquete separado
            import tree_sitter_c_sharp as tscs
            return Parser(Language(tscs.language()))
        else:
            # Java, JavaScript, TypeScript usan tree-sitter-language-pack
            from tree_sitter_language_pack import get_parser
            return get_parser(language)

    def parse(self, source: str) -> ParseResult:
        """
        Parsea código fuente y extrae información estructurada.

        Args:
            source: Código fuente como string

        Returns:
            ParseResult con imports, clases, funciones, llamadas y strings
        """
        result = ParseResult(language=self.language)

        try:
            tree = self._parser.parse(bytes(source, "utf-8"))
            root = tree.root_node

            # Verificar errores de parsing
            if root.has_error:
                result.parse_errors.append("El archivo contiene errores de sintaxis")

            # Extraer información
            result.imports = self.extract_imports(root, source)
            result.classes = self.extract_classes(root, source)
            result.functions = self.extract_top_level_functions(root, source)
            result.calls = self.extract_calls(root, source)
            result.strings = self.extract_strings(root, source)

        except Exception as e:
            result.parse_errors.append(f"Error de parsing: {str(e)}")

        return result

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parsea un archivo y extrae información estructurada.

        Args:
            file_path: Ruta al archivo

        Returns:
            ParseResult con información extraída
        """
        try:
            source = read_file_safe(file_path)
            if not source:
                result = ParseResult(language=self.language)
                result.parse_errors.append("Archivo vacio o excede limite de tamano")
                return result
            return self.parse(source)
        except Exception as e:
            result = ParseResult(language=self.language)
            result.parse_errors.append(f"Error leyendo archivo: {str(e)}")
            return result

    # --- Métodos abstractos que deben implementar las subclases ---

    @abstractmethod
    def extract_imports(self, root: Node, source: str) -> List[ParsedImport]:
        """Extrae imports/using del AST."""
        pass

    @abstractmethod
    def extract_classes(self, root: Node, source: str) -> List[ParsedClass]:
        """Extrae clases del AST."""
        pass

    @abstractmethod
    def extract_top_level_functions(self, root: Node, source: str) -> List[ParsedFunction]:
        """Extrae funciones de nivel superior (no métodos de clase)."""
        pass

    @abstractmethod
    def extract_calls(self, root: Node, source: str) -> List[ParsedCall]:
        """Extrae llamadas a métodos del AST."""
        pass

    @abstractmethod
    def extract_strings(self, root: Node, source: str) -> List[ParsedString]:
        """Extrae strings literales del AST."""
        pass

    # --- Utilidades comunes ---

    def get_node_text(self, node: Node, source: str) -> str:
        """Obtiene el texto de un nodo del AST."""
        return source[node.start_byte:node.end_byte]

    def get_node_line(self, node: Node) -> int:
        """Obtiene el número de línea de un nodo (1-indexed)."""
        return node.start_point[0] + 1

    def find_nodes_by_type(self, root: Node, node_type: str) -> List[Node]:
        """Encuentra todos los nodos de un tipo específico."""
        results = []
        self._find_nodes_recursive(root, node_type, results)
        return results

    def _find_nodes_recursive(self, node: Node, node_type: str, results: List[Node]):
        """Búsqueda recursiva de nodos por tipo."""
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            self._find_nodes_recursive(child, node_type, results)

    def find_child_by_type(self, node: Node, child_type: str) -> Optional[Node]:
        """Encuentra el primer hijo de un tipo específico."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def find_children_by_type(self, node: Node, child_type: str) -> List[Node]:
        """Encuentra todos los hijos de un tipo específico."""
        return [child for child in node.children if child.type == child_type]

    @classmethod
    def get_language_for_extension(cls, extension: str) -> Optional[str]:
        """Determina el lenguaje basado en la extensión del archivo."""
        for lang, extensions in cls.LANGUAGE_EXTENSIONS.items():
            if extension.lower() in extensions:
                return lang
        return None

    @classmethod
    def supports_extension(cls, extension: str) -> bool:
        """Verifica si una extensión está soportada."""
        return cls.get_language_for_extension(extension) is not None


def get_parser_for_file(file_path: Path):
    """
    Factory function para obtener el parser correcto basado en la extensión.

    Args:
        file_path: Ruta al archivo

    Returns:
        Parser apropiado (PythonParser, JavaParser, JSParser, CSharpParser) o None
    """
    extension = file_path.suffix.lower()

    # Python usa parser nativo (no tree-sitter)
    if extension == ".py":
        from gtaa_validator.parsers.python_parser import PythonParser
        return PythonParser()

    language = TreeSitterBaseParser.get_language_for_extension(extension)

    if language is None:
        return None

    # Importar el parser específico (tree-sitter)
    if language == "java":
        from gtaa_validator.parsers.java_parser import JavaParser
        return JavaParser()
    elif language in ("javascript", "typescript"):
        from gtaa_validator.parsers.js_parser import JSParser
        return JSParser(language)
    elif language == "c_sharp":
        from gtaa_validator.parsers.csharp_parser import CSharpParser
        return CSharpParser()

    return None
