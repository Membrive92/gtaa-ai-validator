"""
Command-line interface for gTAA Validator.

This is the entry point when running: python -m gtaa_validator

FASE 1 (MVP): Basic file discovery
- Accept project path as argument
- Find all test files recursively
- Display count and list of files found
- Support --verbose flag for detailed output
"""

import click
import sys
from pathlib import Path


@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(project_path: str, verbose: bool):
    """
    Validate gTAA architecture compliance for a test automation project.

    PROJECT_PATH: Path to the root directory of the test project to analyze.

    Example:
        python -m gtaa_validator ./my-selenium-project
        python -m gtaa_validator ./my-selenium-project --verbose
    """
    # Display header
    click.echo("=== gTAA AI Validator - Fase 1 MVP ===")
    click.echo(f"Analyzing project: {project_path}\n")

    # Convert to Path object and resolve to absolute path
    project_path = Path(project_path).resolve()

    # Validate that path is a directory
    if not project_path.is_dir():
        click.echo(f"ERROR: {project_path} is not a directory", err=True)
        sys.exit(1)

    # Display project information if verbose
    if verbose:
        click.echo(f"Project directory: {project_path}")
        click.echo(f"Searching for test files...\n")

    # Find Python test files using common naming patterns
    # Pattern 1: test_*.py (pytest convention)
    test_files_pattern1 = list(project_path.rglob("test_*.py"))

    # Pattern 2: *_test.py (alternative convention)
    test_files_pattern2 = list(project_path.rglob("*_test.py"))

    # Combine and remove duplicates
    test_files = list(set(test_files_pattern1 + test_files_pattern2))

    # Sort files for consistent output
    test_files.sort()

    # Display results
    click.echo(f"[OK] Found {len(test_files)} test file(s)")

    if test_files and verbose:
        click.echo("\nTest files discovered:")
        for i, test_file in enumerate(test_files, 1):
            # Show relative path from project root for readability
            try:
                relative_path = test_file.relative_to(project_path)
            except ValueError:
                relative_path = test_file
            click.echo(f"  {i}. {relative_path}")

    # Find Python files (all .py files)
    all_python_files = list(project_path.rglob("*.py"))

    if verbose:
        click.echo(f"\nTotal Python files in project: {len(all_python_files)}")

    # Final message
    click.echo(f"\n{'='*60}")
    click.echo("Analysis complete!")
    click.echo("Phase 1 MVP: Basic file discovery working!")
    click.echo(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
