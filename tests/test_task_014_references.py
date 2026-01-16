"""Behavioral tests for Task 013: References Handler.

These tests verify that the ReferencesHandler class correctly handles
find-references requests to locate all places where artifacts are referenced.
"""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import MagicMock

import pytest
from lsprotocol.types import Position, ReferenceParams, TextDocumentIdentifier
from pygls.workspace import TextDocument

from maid_lsp.capabilities.references import ReferencesHandler
from maid_lsp.validation.runner import MaidRunner


class TestReferencesHandlerInit:
    """Test ReferencesHandler initialization."""

    def test_init_creates_instance(self) -> None:
        """ReferencesHandler should be instantiable."""
        handler = ReferencesHandler()
        assert handler is not None
        assert isinstance(handler, ReferencesHandler)

    def test_init_with_runner(self) -> None:
        """ReferencesHandler should accept a MaidRunner instance."""
        runner = MaidRunner()
        handler = ReferencesHandler(runner)
        assert handler is not None
        assert handler.runner is runner

    def test_init_explicit_call(self) -> None:
        """ReferencesHandler.__init__ should initialize properly with explicit call."""
        runner = MaidRunner()
        handler = ReferencesHandler.__new__(ReferencesHandler)
        ReferencesHandler.__init__(handler, runner=runner)

        assert handler is not None
        assert isinstance(handler, ReferencesHandler)


class TestReferencesHandlerGetReferences:
    """Test ReferencesHandler.get_references method."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_references(self) -> None:
        """get_references should return empty list when no references found."""
        handler = ReferencesHandler()

        document = MagicMock(spec=TextDocument)
        document.source = "def my_function():\n    pass\n"
        document.lines = document.source.split("\n")

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/file.py"),
            position=Position(line=0, character=0),
            context=None,  # type: ignore[arg-type]
        )

        result = await handler.get_references(params, document)

        assert result == []

    @pytest.mark.asyncio
    async def test_finds_references_in_manifests(self) -> None:
        """get_references should find references in manifest files."""
        handler = ReferencesHandler()

        with TemporaryDirectory() as tmpdir:
            manifest_dir = Path(tmpdir) / "manifests"
            manifest_dir.mkdir()

            manifest_content = {
                "goal": "Test",
                "expectedArtifacts": {
                    "file": "src/module.py",
                    "contains": [{"type": "function", "name": "my_function"}],
                },
            }

            manifest_path = manifest_dir / "task-001.manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest_content, f)

            document = MagicMock(spec=TextDocument)
            document.source = json.dumps(manifest_content)
            document.lines = document.source.split("\n")

            params = ReferenceParams(
                text_document=TextDocumentIdentifier(uri=f"file://{manifest_path}"),
                position=Position(line=5, character=25),  # Position on "my_function"
                context=None,  # type: ignore[arg-type]
            )

            # Mock workspace root
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = await handler.get_references(params, document)
                assert isinstance(result, list)
            finally:
                os.chdir(original_cwd)


class TestReferencesHandlerFindInManifests:
    """Test ReferencesHandler._find_in_manifests method."""

    @pytest.mark.asyncio
    async def test_finds_artifact_references_in_manifest(self) -> None:
        """_find_in_manifests should find references in manifest files."""
        handler = ReferencesHandler()

        with TemporaryDirectory() as tmpdir:
            manifest_dir = Path(tmpdir) / "manifests"
            manifest_dir.mkdir()

            manifest_content = {
                "goal": "Test",
                "expectedArtifacts": {
                    "file": "src/module.py",
                    "contains": [{"type": "function", "name": "my_function"}],
                },
            }

            manifest_path = manifest_dir / "task-001.manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest_content, f)

            artifact_info = {"type": "function", "name": "my_function"}

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = await handler._find_in_manifests("my_function", artifact_info)
                assert isinstance(result, list)
            finally:
                os.chdir(original_cwd)


class TestReferencesHandlerFindInSource:
    """Test ReferencesHandler._find_in_source method."""

    def test_finds_function_call_references(self) -> None:
        """_find_artifact_references_in_source should find function call references."""
        handler = ReferencesHandler()

        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as source_file:
            source_file.write("def my_function():\n    pass\n\nresult = my_function()\n")
            source_path = Path(source_file.name)

        try:
            artifact_info = {"type": "function", "name": "my_function"}
            workspace_root = source_path.parent

            result = handler._find_artifact_references_in_source(
                source_path, "my_function", artifact_info, workspace_root
            )

            assert isinstance(result, list)
            # Should find at least the call reference
            assert len(result) > 0
        finally:
            source_path.unlink()

    def test_finds_import_references(self) -> None:
        """_find_artifact_references_in_source should find import references."""
        handler = ReferencesHandler()

        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as source_file:
            source_file.write("from module import my_function\n")
            source_path = Path(source_file.name)

        try:
            artifact_info = {"type": "function", "name": "my_function"}
            workspace_root = source_path.parent

            result = handler._find_artifact_references_in_source(
                source_path, "my_function", artifact_info, workspace_root
            )

            assert isinstance(result, list)
        finally:
            source_path.unlink()


class TestReferencesHandlerUtilityMethods:
    """Test ReferencesHandler utility methods."""

    def test_get_word_at_position(self) -> None:
        """_get_word_at_position should extract word correctly."""
        handler = ReferencesHandler()

        document = MagicMock(spec=TextDocument)
        document.source = "def my_function():\n    pass\n"
        document.lines = document.source.split("\n")

        position = Position(line=0, character=4)
        word = handler._get_word_at_position(document, position)

        assert word == "my_function"

    def test_get_artifact_info_from_manifest(self) -> None:
        """_get_artifact_info_from_manifest should extract artifact info."""
        handler = ReferencesHandler()

        document = MagicMock(spec=TextDocument)
        document.source = json.dumps(
            {
                "expectedArtifacts": {
                    "file": "src/module.py",
                    "contains": [{"type": "function", "name": "my_function"}],
                },
            }
        )

        artifact_info = handler._get_artifact_info_from_manifest(document, "my_function")

        assert artifact_info is not None
        assert artifact_info["name"] == "my_function"

    def test_get_artifact_info_from_source(self) -> None:
        """_get_artifact_info_from_source should extract artifact info."""
        handler = ReferencesHandler()

        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as source_file:
            source_file.write("def my_function():\n    pass\n")
            source_path = Path(source_file.name)

        try:
            document = MagicMock(spec=TextDocument)
            document.source = "def my_function():\n    pass\n"

            artifact_info = handler._get_artifact_info_from_source(
                document, source_path, "my_function"
            )

            assert artifact_info is not None
            assert artifact_info["type"] == "function"
        finally:
            source_path.unlink()

    def test_is_manifest_file(self) -> None:
        """_is_manifest_file should identify manifest files correctly."""
        handler = ReferencesHandler()

        assert handler._is_manifest_file(Path("task-001.manifest.json")) is True
        assert handler._is_manifest_file(Path("manifests/task.json")) is True
        assert handler._is_manifest_file(Path("src/module.py")) is False

    def test_uri_to_path(self) -> None:
        """_uri_to_path should convert URI to Path correctly."""
        handler = ReferencesHandler()

        path = handler._uri_to_path("file:///path/to/file.py")
        assert isinstance(path, Path)

    def test_path_to_uri(self) -> None:
        """_path_to_uri should convert Path to URI correctly."""
        handler = ReferencesHandler()

        uri = handler._path_to_uri(Path("/path/to/file.py"))
        assert uri.startswith("file://")


class TestReferencesHandlerExtractTestFiles:
    """Test ReferencesHandler._extract_test_files_from_command method."""

    def test_extracts_test_file_from_pytest_command(self) -> None:
        """_extract_test_files_from_command should extract test file from pytest command."""
        handler = ReferencesHandler()

        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "tests" / "test_example.py"
            test_file.parent.mkdir()
            test_file.write_text("# test file\n")

            validation_command = ["pytest", "tests/test_example.py", "-v"]
            workspace_root = Path(tmpdir)

            result = handler._extract_test_files_from_command(validation_command, workspace_root)

            assert len(result) == 1
            assert result[0] == test_file.resolve()

    def test_extracts_test_file_with_glob_pattern(self) -> None:
        """_extract_test_files_from_command should handle glob patterns."""
        handler = ReferencesHandler()

        with TemporaryDirectory() as tmpdir:
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()
            test_file1 = tests_dir / "test_one.py"
            test_file2 = tests_dir / "test_two.py"
            test_file1.write_text("# test file 1\n")
            test_file2.write_text("# test file 2\n")

            validation_command = ["pytest", "tests/test_*.py", "-v"]
            workspace_root = Path(tmpdir)

            result = handler._extract_test_files_from_command(validation_command, workspace_root)

            assert len(result) >= 1
            assert all(f.exists() for f in result)

    def test_skips_non_test_arguments(self) -> None:
        """_extract_test_files_from_command should skip command names and flags."""
        handler = ReferencesHandler()

        validation_command = ["pytest", "-v", "--verbose", "pytest", "uv", "run"]
        workspace_root = Path.cwd()

        result = handler._extract_test_files_from_command(validation_command, workspace_root)

        # Should not include command names or flags
        assert len(result) == 0

    def test_handles_empty_command(self) -> None:
        """_extract_test_files_from_command should handle empty command."""
        handler = ReferencesHandler()

        result = handler._extract_test_files_from_command([], Path.cwd())

        assert result == []

    def test_handles_invalid_command(self) -> None:
        """_extract_test_files_from_command should handle invalid command."""
        handler = ReferencesHandler()

        result = handler._extract_test_files_from_command("not a list", Path.cwd())

        assert result == []


class TestReferencesHandlerFindInTests:
    """Test ReferencesHandler._find_in_tests method with validationCommand."""

    @pytest.mark.asyncio
    async def test_uses_validation_command_from_manifest(self) -> None:
        """_find_in_tests should use validationCommand from current manifest."""
        handler = ReferencesHandler()

        with TemporaryDirectory() as tmpdir:
            manifest_dir = Path(tmpdir) / "manifests"
            manifest_dir.mkdir()
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()

            # Create test file
            test_file = tests_dir / "test_task_001.py"
            test_file.write_text(
                "def test_my_function():\n    from src.module import my_function\n    assert my_function() is not None\n"
            )

            # Create manifest with validationCommand
            manifest_content = {
                "goal": "Test",
                "expectedArtifacts": {
                    "file": "src/module.py",
                    "contains": [{"type": "function", "name": "my_function"}],
                },
                "validationCommand": ["pytest", "tests/test_task_001.py", "-v"],
            }

            manifest_path = manifest_dir / "task-001.manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest_content, f)

            document = MagicMock(spec=TextDocument)
            document.source = json.dumps(manifest_content)
            document.lines = document.source.split("\n")

            artifact_info = {"type": "function", "name": "my_function"}

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = await handler._find_in_tests(
                    "my_function", artifact_info, document, manifest_path
                )
                assert isinstance(result, list)
                # Should find references in the test file from validationCommand
                assert len(result) > 0
            finally:
                os.chdir(original_cwd)
