"""
Analyzers package for gTAA Validator.

This package contains analyzers that orchestrate the violation detection process.
Analyzers coordinate multiple checkers and aggregate results into reports.

Available analyzers:
- StaticAnalyzer: Orchestrates static analysis checkers (AST, regex, filesystem)
- SemanticAnalyzer: Uses LLM for semantic analysis (Phase 5, optional — requires API key)

The analyzers implement the Facade Pattern, providing a simple interface
to a complex subsystem of checkers.
"""

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer

__all__ = [
    "StaticAnalyzer",
]
