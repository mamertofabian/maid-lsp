"""Tests for AST parser utilities.

These tests verify that the AST parser correctly locates artifact definitions
in Python source files.
"""

import ast
from pathlib import Path
from tempfile import NamedTemporaryFile

from maid_lsp.utils.ast_parser import (
    ArtifactLocation,
    find_artifact_definition,
    find_attribute_definition,
    find_class_definition,
    find_function_definition,
    parse_file,
)


class TestParseFile:
    """Test parse_file function."""

    def test_parses_valid_python_file(self) -> None:
        """parse_file should parse a valid Python file and return AST."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def my_function():\n    pass\n")
            file_path = Path(f.name)

        try:
            tree = parse_file(file_path)
            assert tree is not None
            assert isinstance(tree, ast.Module)
        finally:
            file_path.unlink()

    def test_returns_none_for_invalid_syntax(self) -> None:
        """parse_file should return None for files with invalid syntax."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def invalid syntax here\n")
            file_path = Path(f.name)

        try:
            tree = parse_file(file_path)
            assert tree is None
        finally:
            file_path.unlink()

    def test_returns_none_for_nonexistent_file(self) -> None:
        """parse_file should return None for nonexistent files."""
        file_path = Path("/nonexistent/path/file.py")
        tree = parse_file(file_path)
        assert tree is None


class TestFindFunctionDefinition:
    """Test find_function_definition function."""

    def test_finds_module_level_function(self) -> None:
        """find_function_definition should find a module-level function."""
        source = "def my_function():\n    pass\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_function_definition(tree, "my_function", None, file_path)

        assert location is not None
        assert isinstance(location, ArtifactLocation)
        assert location.file_path == file_path.resolve()
        assert location.line == 0
        assert location.column == 0

    def test_finds_class_method(self) -> None:
        """find_function_definition should find a class method."""
        source = "class MyClass:\n    def my_method(self):\n        pass\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_function_definition(tree, "my_method", "MyClass", file_path)

        assert location is not None
        assert isinstance(location, ArtifactLocation)
        assert location.file_path == file_path.resolve()

    def test_returns_none_for_nonexistent_function(self) -> None:
        """find_function_definition should return None for nonexistent function."""
        source = "def other_function():\n    pass\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_function_definition(tree, "my_function", None, file_path)

        assert location is None

    def test_finds_async_function(self) -> None:
        """find_function_definition should find async functions."""
        source = "async def my_async_function():\n    pass\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_function_definition(tree, "my_async_function", None, file_path)

        assert location is not None
        assert isinstance(location, ArtifactLocation)


class TestFindClassDefinition:
    """Test find_class_definition function."""

    def test_finds_class_definition(self) -> None:
        """find_class_definition should find a class definition."""
        source = "class MyClass:\n    pass\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_class_definition(tree, "MyClass", file_path)

        assert location is not None
        assert isinstance(location, ArtifactLocation)
        assert location.file_path == file_path.resolve()
        assert location.line == 0
        assert location.column == 0

    def test_returns_none_for_nonexistent_class(self) -> None:
        """find_class_definition should return None for nonexistent class."""
        source = "class OtherClass:\n    pass\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_class_definition(tree, "MyClass", file_path)

        assert location is None


class TestFindAttributeDefinition:
    """Test find_attribute_definition function."""

    def test_finds_assignment_attribute(self) -> None:
        """find_attribute_definition should find an assignment attribute."""
        source = "__version__ = '1.0.0'\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_attribute_definition(tree, "__version__", file_path)

        assert location is not None
        assert isinstance(location, ArtifactLocation)
        assert location.file_path == file_path.resolve()

    def test_finds_annotated_attribute(self) -> None:
        """find_attribute_definition should find an annotated attribute."""
        source = "my_var: int = 42\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_attribute_definition(tree, "my_var", file_path)

        assert location is not None
        assert isinstance(location, ArtifactLocation)

    def test_returns_none_for_nonexistent_attribute(self) -> None:
        """find_attribute_definition should return None for nonexistent attribute."""
        source = "other_var = 42\n"
        tree = ast.parse(source)
        file_path = Path("/test/file.py")

        location = find_attribute_definition(tree, "my_var", file_path)

        assert location is None


class TestFindArtifactDefinition:
    """Test find_artifact_definition function."""

    def test_finds_function_artifact(self) -> None:
        """find_artifact_definition should find a function artifact."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def my_function():\n    pass\n")
            file_path = Path(f.name)

        try:
            location = find_artifact_definition(file_path, "function", "my_function", None)

            assert location is not None
            assert isinstance(location, ArtifactLocation)
        finally:
            file_path.unlink()

    def test_finds_class_artifact(self) -> None:
        """find_artifact_definition should find a class artifact."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("class MyClass:\n    pass\n")
            file_path = Path(f.name)

        try:
            location = find_artifact_definition(file_path, "class", "MyClass", None)

            assert location is not None
            assert isinstance(location, ArtifactLocation)
        finally:
            file_path.unlink()

    def test_finds_attribute_artifact(self) -> None:
        """find_artifact_definition should find an attribute artifact."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("__version__ = '1.0.0'\n")
            file_path = Path(f.name)

        try:
            location = find_artifact_definition(file_path, "attribute", "__version__", None)

            assert location is not None
            assert isinstance(location, ArtifactLocation)
        finally:
            file_path.unlink()

    def test_finds_class_method(self) -> None:
        """find_artifact_definition should find a class method."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("class MyClass:\n    def my_method(self):\n        pass\n")
            file_path = Path(f.name)

        try:
            location = find_artifact_definition(file_path, "function", "my_method", "MyClass")

            assert location is not None
            assert isinstance(location, ArtifactLocation)
        finally:
            file_path.unlink()

    def test_returns_none_for_invalid_file(self) -> None:
        """find_artifact_definition should return None for invalid file."""
        file_path = Path("/nonexistent/file.py")
        location = find_artifact_definition(file_path, "function", "my_function", None)
        assert location is None

    def test_returns_none_for_unknown_type(self) -> None:
        """find_artifact_definition should return None for unknown artifact type."""
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def my_function():\n    pass\n")
            file_path = Path(f.name)

        try:
            location = find_artifact_definition(file_path, "unknown", "my_function", None)

            assert location is None
        finally:
            file_path.unlink()


class TestArtifactLocation:
    """Test ArtifactLocation dataclass."""

    def test_creates_location_with_all_fields(self) -> None:
        """ArtifactLocation should store all required fields."""
        file_path = Path("/test/file.py")
        location = ArtifactLocation(
            file_path=file_path,
            line=10,
            column=5,
            end_line=10,
            end_column=15,
        )

        assert location.file_path == file_path
        assert location.line == 10
        assert location.column == 5
        assert location.end_line == 10
        assert location.end_column == 15
