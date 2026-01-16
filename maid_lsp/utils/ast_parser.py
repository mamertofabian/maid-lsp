"""AST parsing utilities for finding artifact definitions in Python source files.

This module provides utilities for parsing Python source files using the AST
module to locate function, class, and attribute definitions for LSP navigation.
"""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactLocation:
    """Represents the location of an artifact in a source file.

    Attributes:
        file_path: Path to the file containing the artifact.
        line: 0-based line number where the artifact is defined.
        column: 0-based column number where the artifact name starts.
        end_line: 0-based line number where the artifact definition ends.
        end_column: 0-based column number where the artifact definition ends.
    """

    file_path: Path
    line: int
    column: int
    end_line: int
    end_column: int

    def __hash__(self) -> int:
        """Make ArtifactLocation hashable by converting Path to string."""
        return hash(
            (
                str(self.file_path),
                self.line,
                self.column,
                self.end_line,
                self.end_column,
            )
        )


def parse_file(file_path: Path) -> ast.Module | None:
    """Parse a Python file and return its AST.

    Args:
        file_path: Path to the Python file to parse.

    Returns:
        The AST Module node if parsing succeeds, None otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
        return ast.parse(source, filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def find_function_definition(
    tree: ast.Module,
    name: str,
    class_name: str | None = None,
    file_path: Path | None = None,
) -> ArtifactLocation | None:
    """Find a function or method definition in an AST.

    Args:
        tree: The AST module to search.
        name: Name of the function to find.
        class_name: Optional class name if searching for a method.
        file_path: Path to the source file (required for location).

    Returns:
        ArtifactLocation if found, None otherwise.
    """
    if file_path is None:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == name:
                if class_name is None:
                    # Module-level function
                    return _create_location_from_node(node, file_path)
                # Check if it's a method of the specified class
                parent = _get_parent_class(node, tree)
                if parent and parent.name == class_name:
                    return _create_location_from_node(node, file_path)
        elif isinstance(node, ast.AsyncFunctionDef) and node.name == name:  # noqa: SIM102
            if class_name is None:
                return _create_location_from_node(node, file_path)
            parent = _get_parent_class(node, tree)
            if parent and parent.name == class_name:
                return _create_location_from_node(node, file_path)

    return None


def find_class_definition(
    tree: ast.Module, name: str, file_path: Path | None = None
) -> ArtifactLocation | None:
    """Find a class definition in an AST.

    Args:
        tree: The AST module to search.
        name: Name of the class to find.
        file_path: Path to the source file (required for location).

    Returns:
        ArtifactLocation if found, None otherwise.
    """
    if file_path is None:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return _create_location_from_node(node, file_path)

    return None


def find_attribute_definition(
    tree: ast.Module, name: str, file_path: Path | None = None
) -> ArtifactLocation | None:
    """Find a module-level attribute definition in an AST.

    Args:
        tree: The AST module to search.
        name: Name of the attribute to find.
        file_path: Path to the source file (required for location).

    Returns:
        ArtifactLocation if found, None otherwise.
    """
    if file_path is None:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return _create_location_from_node(target, file_path)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            return _create_location_from_node(node.target, file_path)

    return None


def find_artifact_definition(
    file_path: Path,
    artifact_type: str,
    artifact_name: str,
    class_name: str | None = None,
) -> ArtifactLocation | None:
    """Find an artifact definition in a Python source file.

    Args:
        file_path: Path to the Python source file.
        artifact_type: Type of artifact ("function", "class", "attribute").
        artifact_name: Name of the artifact to find.
        class_name: Optional class name for class methods.

    Returns:
        ArtifactLocation if found, None otherwise.
    """
    tree = parse_file(file_path)
    if tree is None:
        return None

    resolved_path = file_path.resolve()
    location = None
    if artifact_type == "function":
        location = find_function_definition(tree, artifact_name, class_name, resolved_path)
    elif artifact_type == "class":
        location = find_class_definition(tree, artifact_name, resolved_path)
    elif artifact_type == "attribute":
        location = find_attribute_definition(tree, artifact_name, resolved_path)

    return location


def _create_location_from_node(node: ast.AST, file_path: Path) -> ArtifactLocation | None:
    """Create an ArtifactLocation from an AST node.

    Args:
        node: The AST node representing the artifact.
        file_path: Path to the source file.

    Returns:
        ArtifactLocation with position information.
    """
    if not hasattr(node, "lineno") or not hasattr(node, "col_offset"):
        return None

    line = node.lineno - 1  # Convert to 0-based
    column = node.col_offset

    # Calculate end position
    end_line = line
    end_column = column

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        # For definitions, use the name length
        name_length = len(node.name)
        end_column = column + name_length
    elif isinstance(node, ast.Name):
        end_column = column + len(node.id)

    return ArtifactLocation(
        file_path=file_path.resolve(),
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
    )


def _get_parent_class(node: ast.AST, tree: ast.Module) -> ast.ClassDef | None:
    """Get the parent class of a node if it's a method.

    Args:
        node: The AST node (should be a function/method).
        tree: The AST module to search.

    Returns:
        The parent ClassDef node if found, None otherwise.
    """
    for parent in ast.walk(tree):
        if isinstance(parent, ast.ClassDef):
            for child in ast.walk(parent):
                if child is node and isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    return parent
    return None
