"""
Checkers package for gTAA Validator.

This package contains all violation detection checkers.
Each checker is responsible for detecting specific types of gTAA violations.

Checkers use the Strategy Pattern:
- base.py: Abstract base class defining the checker interface
- definition_checker.py: Detects violations in the Definition layer (test files)
- structure_checker.py: Validates project structure (Phase 3)
- adaptation_checker.py: Validates Page Objects (Phase 3)
- quality_checker.py: Code quality checks (Phase 3)

All checkers inherit from BaseChecker and implement the check() method.
"""

from gtaa_validator.checkers.base import BaseChecker

# Phase 2: Only DefinitionChecker is implemented
from gtaa_validator.checkers.definition_checker import DefinitionChecker

# Phase 3: Additional checkers will be imported
# from gtaa_validator.checkers.structure_checker import StructureChecker
# from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
# from gtaa_validator.checkers.quality_checker import QualityChecker

__all__ = [
    "BaseChecker",
    "DefinitionChecker",
]
