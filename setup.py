"""
Configuración de instalación para gTAA AI Validator.

Este archivo permite instalar el proyecto con pip.
"""

import re
from setuptools import setup, find_packages
from pathlib import Path

# Single source of truth: leer versión desde __init__.py
_version_match = re.search(
    r'__version__\s*=\s*["\']([^"\']+)',
    (Path(__file__).parent / "gtaa_validator" / "__init__.py").read_text()
)
__version__ = _version_match.group(1)

# Leer README para la descripción larga
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Validador de cumplimiento arquitectónico gTAA para proyectos de test automation"

setup(
    name="gtaa-ai-validator",
    version=__version__,
    author="Jose Antonio Membrive Guillen",
    author_email="membri_2@hotmail.com",
    description="Validador de cumplimiento arquitectónico gTAA para proyectos de test automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Membrive92/gtaa-ai-validator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0.0",
        "google-genai>=1.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0",
        "tree-sitter-language-pack>=0.4.0",  # Multi-lang parsing (Fase 9)
        "tree-sitter-c-sharp>=0.23.0",  # C# parsing (Fase 9)
    ],
    entry_points={
        "console_scripts": [
            "gtaa-validator=gtaa_validator.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
