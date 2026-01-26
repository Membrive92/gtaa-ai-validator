"""
Setup configuration for gTAA AI Validator.

This file makes the project installable with pip.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "AI-powered validator for gTAA test automation architecture compliance"

setup(
    name="gtaa-ai-validator",
    version="0.1.0",
    author="Jose Antonio Membrive Guillen",
    author_email="membri_2@hotmail.com",
    description="AI-powered validator for gTAA test automation architecture compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gtaa-ai-validator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "gtaa-validator=gtaa_validator.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
