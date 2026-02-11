"""Example projects for gTAA AI Validator.

Provides access to bundled example projects for testing and demonstration.
"""

from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent


def get_examples_path() -> Path:
    """Return the absolute path to the examples directory."""
    return EXAMPLES_DIR


def get_bad_project_path() -> Path:
    """Return path to the bad_project example (expects ~58 violations)."""
    return EXAMPLES_DIR / "bad_project"


def get_good_project_path() -> Path:
    """Return path to the good_project example (expects 0 violations)."""
    return EXAMPLES_DIR / "good_project"
