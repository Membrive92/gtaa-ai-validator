"""
Analyzers package for gTAA Validator.

This package contains analyzers that orchestrate the violation detection process.
Analyzers coordinate multiple checkers and aggregate results into reports.

Available analyzers:
- StaticAnalyzer: Orchestrates static analysis checkers (AST, regex, filesystem)
- AIAnalyzer: Uses LLM for semantic analysis (Phase 6, optional)
- MLAnalyzer: Uses trained ML model for classification (Phase 7, optional)

The analyzers implement the Facade Pattern, providing a simple interface
to a complex subsystem of checkers.
"""

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer

# Phase 6: AI analyzer (optional, requires API key)
# from gtaa_validator.analyzers.ai_analyzer import AIAnalyzer

# Phase 7: ML classifier (optional)
# from gtaa_validator.analyzers.ml_analyzer import MLAnalyzer

__all__ = [
    "StaticAnalyzer",
    # "AIAnalyzer",  # Uncomment in Phase 6
    # "MLAnalyzer",  # Uncomment in Phase 7
]
