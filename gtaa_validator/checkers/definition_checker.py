"""
Definition Layer Checker for gTAA Validator.

This checker detects violations in the Definition layer (test files).
The primary violation detected is ADAPTATION_IN_DEFINITION: when test code
directly calls Selenium or Playwright APIs instead of using Page Objects.

Key concepts:
- AST (Abstract Syntax Tree): Python's built-in way to parse and analyze code
- Visitor Pattern: Walk through the AST tree and react to specific node types
- Static Analysis: Analyze code without executing it

According to gTAA architecture:
- Definition layer (tests) should only call Page Objects
- Adaptation layer (Page Objects) encapsulates Selenium/Playwright
- Test files should NOT directly call driver.find_element(), page.locator(), etc.
"""

import ast
from pathlib import Path
from typing import List, Optional, Set

from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.models import Violation, ViolationType, Severity


class DefinitionChecker(BaseChecker):
    """
    Checks test files for direct calls to Selenium/Playwright APIs.

    This checker parses Python test files and detects when test functions
    directly call browser automation APIs instead of using Page Objects.

    Example violation:
        def test_login():
            driver.find_element(By.ID, "username").send_keys("user")  # VIOLATION!

    Should be:
        def test_login():
            login_page.enter_username("user")  # OK - uses Page Object
    """

    # Method names that indicate direct Selenium usage
    SELENIUM_METHODS = {
        "find_element",
        "find_elements",
        "find_element_by_id",
        "find_element_by_name",
        "find_element_by_xpath",
        "find_element_by_css_selector",
        "find_element_by_class_name",
        "find_element_by_tag_name",
        "find_element_by_link_text",
        "find_element_by_partial_link_text",
    }

    # Method names that indicate direct Playwright usage
    PLAYWRIGHT_METHODS = {
        "locator",
        "query_selector",
        "query_selector_all",
        "wait_for_selector",
        "click",
        "fill",
        "type",
        "select_option",
    }

    # Object names that indicate browser automation objects
    BROWSER_OBJECTS = {
        "driver",      # Selenium WebDriver
        "page",        # Playwright Page
        "browser",     # Playwright Browser
        "context",     # Playwright BrowserContext
    }

    def __init__(self):
        """Initialize the DefinitionChecker."""
        super().__init__()
        self.violations: List[Violation] = []
        self.current_file: Path = None

    def can_check(self, file_path: Path) -> bool:
        """
        Only check Python files that appear to be test files.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this is a Python test file, False otherwise
        """
        if file_path.suffix != ".py":
            return False

        filename = file_path.name
        # Check common test file naming patterns
        is_test_file = (
            filename.startswith("test_") or
            filename.endswith("_test.py") or
            any(part in ("test", "tests") for part in file_path.parts)
        )
        return is_test_file

    def check(self, file_path: Path, tree: Optional[ast.Module] = None) -> List[Violation]:
        """
        Check a test file for ADAPTATION_IN_DEFINITION violations.

        This method:
        1. Uses the pre-parsed AST if provided, otherwise reads and parses the file
        2. Uses a visitor to find violations
        3. Returns list of violations found

        Args:
            file_path: Path to the test file to check
            tree: Pre-parsed AST tree (optional)

        Returns:
            List of Violation objects (empty if no violations)
        """
        self.violations = []
        self.current_file = file_path

        try:
            if tree is None:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
                tree = ast.parse(source_code, filename=str(file_path))

            # Create visitor and walk the AST
            visitor = BrowserAPICallVisitor(self)
            visitor.visit(tree)

        except SyntaxError:
            pass
        except Exception:
            pass

        return self.violations

    def add_violation(
        self,
        line_number: int,
        method_name: str,
        object_name: str,
        code_snippet: str
    ):
        """
        Add a violation to the list.

        Args:
            line_number: Line number where violation occurs
            method_name: Name of the forbidden method called
            object_name: Name of the object the method was called on
            code_snippet: The actual code that violated the rule
        """
        violation = Violation(
            violation_type=ViolationType.ADAPTATION_IN_DEFINITION,
            severity=Severity.CRITICAL,
            file_path=self.current_file,
            line_number=line_number,
            message=(
                f"Test code directly calls {object_name}.{method_name}() "
                f"instead of using a Page Object method. "
                f"According to gTAA, the Definition layer (tests) should only call "
                f"the Adaptation layer (Page Objects), not browser automation APIs directly."
            ),
            code_snippet=code_snippet,
            recommendation=ViolationType.ADAPTATION_IN_DEFINITION.get_recommendation()
        )
        self.violations.append(violation)


class BrowserAPICallVisitor(ast.NodeVisitor):
    """
    AST Visitor that detects direct browser automation API calls in test functions.

    Detects calls to both Selenium and Playwright (and any future framework)
    when used directly inside test functions instead of through Page Objects.

    The Visitor Pattern allows us to traverse the AST and react to specific
    node types without modifying the AST itself.

    Key methods:
    - visit_FunctionDef: Called for every function definition
    - visit_Call: Called for every function call
    - generic_visit: Default behavior for nodes we don't handle specifically
    """

    def __init__(self, checker: DefinitionChecker):
        """
        Initialize the visitor.

        Args:
            checker: The DefinitionChecker instance that created this visitor
        """
        self.checker = checker
        self.inside_test_function = False
        self.current_function_name = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit a function definition node.

        This is called for every function in the file.
        We use it to track when we're inside a test function.

        Args:
            node: The FunctionDef AST node
        """
        # Check if this is a test function (starts with "test_")
        is_test = node.name.startswith("test_")

        if is_test:
            # Remember we're inside a test function
            previous_state = self.inside_test_function
            previous_name = self.current_function_name

            self.inside_test_function = True
            self.current_function_name = node.name

            # Visit all child nodes (the function body)
            self.generic_visit(node)

            # Restore previous state when leaving the function
            self.inside_test_function = previous_state
            self.current_function_name = previous_name
        else:
            # Not a test function, still visit children but don't track
            self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """
        Visit a function call node.

        This is called for every function call in the code.
        We check if it's a forbidden Selenium/Playwright call.

        Args:
            node: The Call AST node
        """
        # Only check calls inside test functions
        if self.inside_test_function:
            # Check if this is a method call (e.g., object.method())
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr  # The method being called

                # Try to get the object name (e.g., "driver", "page")
                object_name = self._get_object_name(node.func.value)

                # Check if this is a violation
                is_selenium_call = method_name in DefinitionChecker.SELENIUM_METHODS
                is_playwright_call = method_name in DefinitionChecker.PLAYWRIGHT_METHODS
                is_browser_object = object_name in DefinitionChecker.BROWSER_OBJECTS

                if (is_selenium_call or is_playwright_call) and is_browser_object:
                    # Found a violation!
                    code_snippet = self._get_code_snippet(node)
                    self.checker.add_violation(
                        line_number=node.lineno,
                        method_name=method_name,
                        object_name=object_name,
                        code_snippet=code_snippet
                    )

        # Continue visiting child nodes
        self.generic_visit(node)

    def _get_object_name(self, node: ast.AST) -> str:
        """
        Extract the object name from an AST node.

        Examples:
        - driver.find_element() -> "driver"
        - self.driver.find_element() -> "driver"
        - page.locator() -> "page"

        Args:
            node: AST node representing the object

        Returns:
            The object name as a string, or empty string if not found
        """
        if isinstance(node, ast.Name):
            # Simple name: driver
            return node.id
        elif isinstance(node, ast.Attribute):
            # Attribute access: self.driver
            # Recursively get the rightmost name
            return self._get_object_name(node.value)
        else:
            return ""

    def _get_code_snippet(self, node: ast.Call) -> str:
        """
        Generate a readable code snippet for the violation.

        This is a simplified version - in production you'd want to use
        ast.unparse() (Python 3.9+) or astor library for better results.

        Args:
            node: The Call node to convert to code

        Returns:
            String representation of the code
        """
        try:
            # Python 3.9+ has ast.unparse()
            return ast.unparse(node)
        except AttributeError:
            # Fallback for Python 3.8
            if isinstance(node.func, ast.Attribute):
                obj = self._get_object_name(node.func.value)
                method = node.func.attr
                return f"{obj}.{method}(...)"
            return "<code>"
