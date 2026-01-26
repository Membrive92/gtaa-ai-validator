"""
Command-line interface for gTAA Validator.

This is the entry point when running: python -m gtaa_validator

FASE 2: Static analysis with AST
- Detect gTAA architectural violations
- Calculate compliance score (0-100)
- Display violations by severity
- Support --verbose flag for detailed violation info
"""

import click
import sys
from pathlib import Path

from gtaa_validator.analyzers.static_analyzer import StaticAnalyzer


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
    click.echo("=== gTAA AI Validator - Phase 2 ===")
    click.echo(f"Analyzing project: {project_path}\n")

    # Convert to Path object and resolve to absolute path
    project_path = Path(project_path).resolve()

    # Validate that path is a directory
    if not project_path.is_dir():
        click.echo(f"ERROR: {project_path} is not a directory", err=True)
        sys.exit(1)

    # Create analyzer and run analysis
    # Pass verbose flag so analyzer can print detailed progress
    analyzer = StaticAnalyzer(project_path, verbose=verbose)

    if not verbose:
        # Show progress message if not in verbose mode
        click.echo("Running static analysis...")

    report = analyzer.analyze()

    # Display results
    if not verbose:
        # In non-verbose mode, show summary
        click.echo()  # Blank line

    click.echo("="*60)
    click.echo("ANALYSIS RESULTS")
    click.echo("="*60)

    # Show file statistics
    click.echo(f"\nFiles analyzed: {report.files_analyzed}")
    click.echo(f"Total violations: {len(report.violations)}")

    # Show violations by severity
    severity_counts = report.get_violation_count_by_severity()
    click.echo("\nViolations by severity:")
    click.echo(f"  CRITICAL: {severity_counts['CRITICAL']}")
    click.echo(f"  HIGH:     {severity_counts['HIGH']}")
    click.echo(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    click.echo(f"  LOW:      {severity_counts['LOW']}")

    # Show compliance score
    click.echo(f"\nCompliance Score: {report.score:.1f}/100")

    # Score interpretation
    if report.score >= 90:
        score_label = "EXCELLENT"
    elif report.score >= 75:
        score_label = "GOOD"
    elif report.score >= 50:
        score_label = "NEEDS IMPROVEMENT"
    else:
        score_label = "CRITICAL ISSUES"

    click.echo(f"Status: {score_label}")

    # In verbose mode, show detailed violation information
    if verbose and report.violations:
        click.echo("\n" + "="*60)
        click.echo("DETAILED VIOLATIONS")
        click.echo("="*60)

        for i, violation in enumerate(report.violations, 1):
            click.echo(f"\n[{i}] {violation.severity.value} - {violation.violation_type.name}")

            # Show file and line number
            try:
                relative_path = violation.file_path.relative_to(project_path)
            except ValueError:
                relative_path = violation.file_path

            location = f"{relative_path}"
            if violation.line_number:
                location += f":{violation.line_number}"
            click.echo(f"    Location: {location}")

            # Show message
            click.echo(f"    Message: {violation.message}")

            # Show code snippet if available
            if violation.code_snippet:
                click.echo(f"    Code: {violation.code_snippet}")

    # Final summary
    click.echo("\n" + "="*60)
    click.echo(f"Analysis completed in {report.execution_time_seconds:.2f}s")
    click.echo("="*60)

    # Exit with appropriate code
    # Exit code 1 if critical violations found
    if severity_counts['CRITICAL'] > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
