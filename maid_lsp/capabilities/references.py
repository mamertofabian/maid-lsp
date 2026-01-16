"""References handler for maid-lsp.

This module provides the ReferencesHandler class that handles find-references
requests to locate all places where artifacts are referenced across manifests,
test files, and source files.
"""

import ast
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from lsprotocol.types import (
    Location,
    Position,
    Range,
    ReferenceParams,
)
from pygls.workspace import TextDocument

from maid_lsp.utils.ast_parser import parse_file
from maid_lsp.validation.runner import MaidRunner


class ReferencesHandler:
    """Handles find-references requests.

    This class processes reference requests and returns all locations where
    an artifact is referenced across manifests, test files, and source files.
    """

    def __init__(self, runner: MaidRunner | None = None) -> None:
        """Initialize the ReferencesHandler.

        Args:
            runner: Optional MaidRunner instance for manifest discovery.
                If None, creates a new instance.
        """
        self.runner = runner if runner is not None else MaidRunner()

    async def get_references(
        self, params: ReferenceParams, document: TextDocument
    ) -> list[Location] | None:
        """Get all reference locations for a position in the document.

        Args:
            params: The reference parameters containing position information.
            document: The text document to search for artifacts.

        Returns:
            A list of Locations where the artifact is referenced, or None if error.
        """
        if not document.source:
            return []

        uri = params.text_document.uri
        file_path = self._uri_to_path(uri)

        # Get word at cursor position
        word = self._get_word_at_position(document, params.position)
        if not word:
            return []

        references: list[Location] = []

        # Determine if we're in a manifest or source file
        if self._is_manifest_file(file_path):
            # Find artifact info from manifest
            artifact_info = self._get_artifact_info_from_manifest(document, word)
            if artifact_info:
                # Find references in manifests
                references.extend(await self._find_in_manifests(word, artifact_info))
                # Find references in test files
                references.extend(await self._find_in_tests(word, artifact_info))
                # Find references in source files
                references.extend(await self._find_in_source(word, artifact_info))
        else:
            # Find artifact info from source file
            artifact_info = self._get_artifact_info_from_source(document, file_path, word)
            if artifact_info:
                # Find references in manifests
                references.extend(await self._find_in_manifests(word, artifact_info))
                # Find references in test files
                references.extend(await self._find_in_tests(word, artifact_info))
                # Find references in source files
                references.extend(await self._find_in_source(word, artifact_info))

        return references if references else []

    async def _find_in_manifests(
        self, artifact_name: str, artifact_info: dict
    ) -> list[Location]:
        """Find references to artifact in manifest files.

        Args:
            artifact_name: Name of the artifact.
            artifact_info: Dictionary with artifact type and other info.

        Returns:
            List of Locations where artifact is referenced in manifests.
        """
        references: list[Location] = []

        # Search workspace for manifest files
        # For now, search common locations
        workspace_root = Path.cwd()
        manifest_dirs = [
            workspace_root / "manifests",
            workspace_root,
        ]

        for manifest_dir in manifest_dirs:
            if not manifest_dir.exists():
                continue

            for manifest_path in manifest_dir.rglob("*.manifest.json"):
                if not manifest_path.is_file():
                    continue

                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        manifest_content = f.read()
                    manifest = json.loads(manifest_content)
                except (OSError, json.JSONDecodeError):
                    continue

                # Find artifact references in this manifest
                manifest_refs = self._find_artifact_references_in_manifest(
                    manifest, manifest_path, artifact_name
                )
                references.extend(manifest_refs)

        return references

    async def _find_in_tests(
        self, artifact_name: str, artifact_info: dict
    ) -> list[Location]:
        """Find references to artifact in test files.

        Args:
            artifact_name: Name of the artifact.
            artifact_info: Dictionary with artifact type and other info.

        Returns:
            List of Locations where artifact is referenced in test files.
        """
        references: list[Location] = []

        # Search workspace for test files
        workspace_root = Path.cwd()
        test_dirs = [
            workspace_root / "tests",
            workspace_root,
        ]

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue

            # Look for test files
            for test_path in test_dir.rglob("test_*.py"):
                if not test_path.is_file():
                    continue

                test_refs = self._find_artifact_references_in_source(
                    test_path, artifact_name, artifact_info, workspace_root
                )
                references.extend(test_refs)

        return references

    async def _find_in_source(
        self, artifact_name: str, artifact_info: dict
    ) -> list[Location]:
        """Find references to artifact in source files.

        Args:
            artifact_name: Name of the artifact.
            artifact_info: Dictionary with artifact type and other info.

        Returns:
            List of Locations where artifact is referenced in source files.
        """
        references: list[Location] = []

        # Search workspace for source files
        workspace_root = Path.cwd()
        source_dirs = [
            workspace_root,
        ]

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            # Look for Python source files (exclude tests)
            for source_path in source_dir.rglob("*.py"):
                if not source_path.is_file():
                    continue
                if "test" in source_path.parts:
                    continue

                source_refs = self._find_artifact_references_in_source(
                    source_path, artifact_name, artifact_info, workspace_root
                )
                references.extend(source_refs)

        return references

    def _find_artifact_references_in_manifest(
        self, manifest: dict, manifest_path: Path, artifact_name: str
    ) -> list[Location]:
        """Find all references to an artifact in a manifest file.

        Args:
            manifest: The parsed manifest dictionary.
            manifest_path: Path to the manifest file.
            artifact_name: Name of the artifact to find.

        Returns:
            List of Locations where artifact is referenced.
        """
        references: list[Location] = []

        # Read manifest file to find line numbers
        try:
            with open(manifest_path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return references

        # Search for artifact name in manifest content
        pattern = rf'["\']{re.escape(artifact_name)}["\']'
        for line_num, line in enumerate(lines):
            for match in re.finditer(pattern, line):
                # Check if this is in a "name" field (definition) or elsewhere (reference)
                before_text = "".join(lines[max(0, line_num - 5) : line_num])
                column = match.start()
                end_column = match.end()

                references.append(
                    Location(
                        uri=self._path_to_uri(manifest_path),
                        range=Range(
                            start=Position(line=line_num, character=column),
                            end=Position(line=line_num, character=end_column),
                        ),
                    )
                )

        return references

    def _find_artifact_references_in_source(
        self, source_path: Path, artifact_name: str, artifact_info: dict, workspace_root: Path
    ) -> list[Location]:
        """Find all references to an artifact in a Python source file.

        Args:
            source_path: Path to the source file.
            artifact_name: Name of the artifact to find.
            artifact_info: Dictionary with artifact type and other info.
            workspace_root: Root of the workspace.

        Returns:
            List of Locations where artifact is referenced.
        """
        references: list[Location] = []

        tree = parse_file(source_path)
        if tree is None:
            return references

        # Read file to get exact positions
        try:
            with open(source_path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return references

        # Find all references using AST
        for node in ast.walk(tree):
            # Function/method calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == artifact_name:
                    ref = self._create_location_from_node(node.func, lines, source_path)
                    if ref:
                        references.append(ref)
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == artifact_name:
                        ref = self._create_location_from_node(node.func, lines, source_path)
                        if ref:
                            references.append(ref)

            # Attribute access
            if isinstance(node, ast.Attribute):
                if node.attr == artifact_name:
                    ref = self._create_location_from_node(node, lines, source_path)
                    if ref:
                        references.append(ref)

            # Name references (imports, assignments, etc.)
            if isinstance(node, ast.Name):
                if node.id == artifact_name:
                    # Skip if it's a definition (handled separately)
                    if not isinstance(node.ctx, ast.Store):
                        ref = self._create_location_from_node(node, lines, source_path)
                        if ref:
                            references.append(ref)

            # Import statements
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname == artifact_name or (
                        alias.name == artifact_name and alias.asname is None
                    ):
                        ref = self._create_location_from_node(alias, lines, source_path)
                        if ref:
                            references.append(ref)

            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == artifact_name:
                        ref = self._create_location_from_node(alias, lines, source_path)
                        if ref:
                            references.append(ref)

        return references

    def _create_location_from_node(
        self, node: ast.AST, lines: list[str], file_path: Path
    ) -> Location | None:
        """Create a Location from an AST node.

        Args:
            node: The AST node.
            lines: List of file lines for position calculation.
            file_path: Path to the source file.

        Returns:
            Location object, or None if creation fails.
        """
        if not hasattr(node, "lineno") or not hasattr(node, "col_offset"):
            return None

        line_num = node.lineno - 1  # Convert to 0-based
        column = node.col_offset

        if line_num >= len(lines):
            return None

        # Calculate end position
        if isinstance(node, ast.Name):
            end_column = column + len(node.id)
        elif isinstance(node, ast.Attribute):
            end_column = column + len(node.attr)
        elif isinstance(node, ast.alias):
            name = node.asname if node.asname else node.name
            end_column = column + len(name)
        else:
            end_column = column

        return Location(
            uri=self._path_to_uri(file_path),
            range=Range(
                start=Position(line=line_num, character=column),
                end=Position(line=line_num, character=end_column),
            ),
        )

    def _get_artifact_info_from_manifest(
        self, document: TextDocument, artifact_name: str
    ) -> dict | None:
        """Get artifact information from a manifest document.

        Args:
            document: The manifest document.
            artifact_name: Name of the artifact.

        Returns:
            Dictionary with artifact info, or None.
        """
        try:
            manifest = json.loads(document.source)
        except json.JSONDecodeError:
            return None

        expected_artifacts = manifest.get("expectedArtifacts", {})
        contains = expected_artifacts.get("contains", [])
        if not isinstance(contains, list):
            return None

        for artifact in contains:
            if isinstance(artifact, dict) and artifact.get("name") == artifact_name:
                return artifact

        return None

    def _get_artifact_info_from_source(
        self, document: TextDocument, source_path: Path, artifact_name: str
    ) -> dict | None:
        """Get artifact information from a source file.

        Args:
            document: The source file document.
            source_path: Path to the source file.
            artifact_name: Name of the artifact.

        Returns:
            Dictionary with artifact info, or None.
        """
        tree = parse_file(source_path)
        if tree is None:
            return None

        # Try to determine artifact type by finding it in AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == artifact_name:
                return {"type": "function", "name": artifact_name}
            if isinstance(node, ast.ClassDef) and node.name == artifact_name:
                return {"type": "class", "name": artifact_name}

        return None

    def _get_word_at_position(
        self, document: TextDocument, position: Position
    ) -> str | None:
        """Extract the word at the given position.

        Args:
            document: The text document.
            position: The position to extract from.

        Returns:
            The word at the position, or None if not on a word.
        """
        lines = document.lines if document.lines else document.source.split("\n")
        line_num = position.line

        if line_num >= len(lines):
            return None

        current_line = lines[line_num]
        char_pos = position.character

        if char_pos > len(current_line):
            return None

        # Find word boundaries - include underscore as part of word
        word_pattern = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

        for match in word_pattern.finditer(current_line):
            start, end = match.span()
            if start <= char_pos <= end:
                return match.group()

        return None

    def _is_manifest_file(self, file_path: Path) -> bool:
        """Check if a file is a manifest file.

        Args:
            file_path: Path to check.

        Returns:
            True if the file is a manifest file, False otherwise.
        """
        return file_path.name.endswith(".manifest.json") or (
            "manifests" in file_path.parts and file_path.suffix == ".json"
        )

    def _uri_to_path(self, uri: str) -> Path:
        """Convert a file URI to a Path object.

        Args:
            uri: The file URI.

        Returns:
            A Path object.
        """
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            return Path(parsed.path)
        return Path(uri)

    def _path_to_uri(self, file_path: Path) -> str:
        """Convert a Path object to a file URI.

        Args:
            file_path: The file path.

        Returns:
            A file URI string.
        """
        return f"file://{file_path.resolve()}"
