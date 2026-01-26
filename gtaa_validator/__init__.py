"""
gTAA AI Validator - Automated Test Automation Architecture Compliance Checker

This package validates compliance with the Generic Test Automation Architecture (gTAA)
defined in the ISTQB CT-TAE syllabus.

The validator combines static analysis and AI-powered semantic analysis to detect
architectural violations in test automation projects (Selenium, Playwright, etc.).

Main components:
- analyzers: Static and AI-powered code analyzers
- checkers: Violation detection for different gTAA layers
- reporters: HTML and JSON report generators
- models: Data structures for violations and reports
"""

__version__ = "0.1.0"
__author__ = "Jose Antonio Membrive Guillen"
__license__ = "MIT"
__all__ = ["__version__", "__author__", "__license__"]
