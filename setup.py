"""
Shim de compatibilidad para pip install -e .

La configuración principal está en pyproject.toml (PEP 621).
Este archivo se mantiene para compatibilidad con herramientas legacy.
"""

from setuptools import setup

setup()
