"""
Parsers especializados para análisis de código fuente.

Fase 8: GherkinParser para archivos .feature
Fase 9: Parsers multi-lenguaje usando tree-sitter
Fase 9+: PythonParser para checkers agnósticos
"""

from gtaa_validator.parsers.gherkin_parser import (
    GherkinParser,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
)

from gtaa_validator.parsers.treesitter_base import (
    TreeSitterBaseParser,
    ParseResult,
    ParsedImport,
    ParsedClass,
    ParsedFunction,
    ParsedCall,
    ParsedString,
    get_parser_for_file,
)

from gtaa_validator.parsers.python_parser import PythonParser, get_python_parser
from gtaa_validator.parsers.java_parser import JavaParser
from gtaa_validator.parsers.js_parser import JSParser
from gtaa_validator.parsers.csharp_parser import CSharpParser

__all__ = [
    # Gherkin (Fase 8)
    "GherkinParser",
    "GherkinFeature",
    "GherkinScenario",
    "GherkinStep",
    # Tree-sitter base (Fase 9)
    "TreeSitterBaseParser",
    "ParseResult",
    "ParsedImport",
    "ParsedClass",
    "ParsedFunction",
    "ParsedCall",
    "ParsedString",
    "get_parser_for_file",
    # Language-specific parsers (Fase 9)
    "PythonParser",
    "get_python_parser",
    "JavaParser",
    "JSParser",
    "CSharpParser",
]
