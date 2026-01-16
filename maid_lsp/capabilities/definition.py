"""Definition handler for maid-lsp.

This module provides the DefinitionHandler class that handles go-to-definition
requests to navigate from artifact references to their definitions in source
files or manifests.
"""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from lsprotocol.types import (
    DefinitionParams,
    Location,
    Position,
    Range,
)
from pygls.workspace import TextDocument

from maid_lsp.utils.ast_parser import find_artifact_definition
from maid_lsp.validation.runner import MaidRunner


class DefinitionHandler:
    """Handles go-to-definition requests.

    This class processes definition requests and returns locations for
    artifact definitions, supporting bidirectional navigation between
    manifests and source files.
    """

    def __init__(self, runner: MaidRunner | None = None) -> None:
        """Initialize the DefinitionHandler.

        Args:
            runner: Optional MaidRunner instance for manifest discovery.
                If None, creates a new instance.
        """
        self.runner = runner if runner is not None else MaidRunner()

    def get_definition(
        self, params: DefinitionParams, document: TextDocument
    ) -> Location | list[Location] | None:
        """Get definition location for a position in the document.

        Args:
            params: The definition parameters containing position information.
            document: The text document to search for artifacts.

        Returns:
            A Location or list of Locations pointing to the definition,
            or None if no definition found.
        """
        if not document.source:
            return None

        uri = params.text_document.uri
        file_path = self._uri_to_path(uri)

        # Determine if we're in a manifest or source file
        if self._is_manifest_file(file_path):
            return self._get_definition_from_manifest(params, document, file_path)
        else:
            # For source files, we need async but LSP handlers can be sync
            # Return None for now - will be handled in async wrapper
            return None

    async def get_definition_async(
        self, params: DefinitionParams, document: TextDocument
    ) -> Location | list[Location] | None:
        """Get definition location for a position in the document (async version).

        Args:
            params: The definition parameters containing position information.
            document: The text document to search for artifacts.

        Returns:
            A Location or list of Locations pointing to the definition,
            or None if no definition found.
        """
        if not document.source:
            return None

        uri = params.text_document.uri
        file_path = self._uri_to_path(uri)

        # Determine if we're in a manifest or source file
        if self._is_manifest_file(file_path):
            return self._get_definition_from_manifest(params, document, file_path)
        else:
            return await self._get_definition_from_source_async(params, document, file_path)

    def _get_definition_from_manifest(
        self, params: DefinitionParams, document: TextDocument, manifest_path: Path
    ) -> Location | None:
        """Get definition location when clicking on artifact in manifest.

        Args:
            params: The definition parameters.
            document: The manifest document.
            manifest_path: Path to the manifest file.

        Returns:
            Location pointing to source file definition, or None.
        """
        # Get word at cursor position
        word = self._get_word_at_position(document, params.position)
        if not word:
            return None

        # Parse manifest and find artifact
        try:
            manifest = json.loads(document.source)
        except json.JSONDecodeError:
            return None

        artifact = self._find_artifact_by_name(manifest, word)
        if artifact is None:
            return None

        # Get source file path from manifest
        expected_artifacts = manifest.get("expectedArtifacts", {})
        source_file_str = expected_artifacts.get("file")
        if not source_file_str:
            return None

        # Resolve source file path relative to manifest
        source_file_path = self._resolve_source_path(manifest_path, source_file_str)
        if not source_file_path or not source_file_path.exists():
            return None

        # Find artifact in source file
        artifact_type = artifact.get("type", "")
        artifact_name = artifact.get("name", "")
        class_name = artifact.get("class")

        location = find_artifact_definition(
            source_file_path, artifact_type, artifact_name, class_name
        )

        if location is None:
            return None

        return Location(
            uri=self._path_to_uri(location.file_path),
            range=Range(
                start=Position(line=location.line, character=location.column),
                end=Position(line=location.end_line, character=location.end_column),
            ),
        )

    async def _get_definition_from_source_async(
        self, params: DefinitionParams, document: TextDocument, source_path: Path
    ) -> Location | None:
        """Get definition location when clicking on artifact in source file (async).

        Args:
            params: The definition parameters.
            document: The source file document.
            source_path: Path to the source file.

        Returns:
            Location pointing to manifest definition, or None.
        """
        # Get word at cursor position
        word = self._get_word_at_position(document, params.position)
        if not word:
            return None

        # Find manifests that reference this file
        try:
            manifests = await self.runner.find_manifests(source_path)
        except Exception:
            return None

        # Search manifests for artifact definition
        for manifest_path in manifests:
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest_content = f.read()
                manifest = json.loads(manifest_content)
            except (OSError, json.JSONDecodeError):
                continue

            # Check if this manifest defines the artifact
            artifact_location = self._find_artifact_location_in_manifest(
                manifest, manifest_path, word
            )
            if artifact_location:
                return artifact_location

        return None

    def _find_artifact_location_in_manifest(
        self, manifest: dict, manifest_path: Path, artifact_name: str
    ) -> Location | None:
        """Find the location of an artifact definition in a manifest.

        Args:
            manifest: The parsed manifest dictionary.
            manifest_path: Path to the manifest file.
            artifact_name: Name of the artifact to find.

        Returns:
            Location pointing to artifact in manifest, or None.
        """
        expected_artifacts = manifest.get("expectedArtifacts", {})
        contains = expected_artifacts.get("contains", [])
        if not isinstance(contains, list):
            return None

        # Read manifest file to find line numbers
        try:
            with open(manifest_path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return None

        # Search for artifact name in manifest content
        for line_num, line in enumerate(lines):
            # Look for the artifact name in quotes (JSON format)
            pattern = rf'["\']{re.escape(artifact_name)}["\']'
            match = re.search(pattern, line)
            if match:
                # Check if this is actually in the "name" field of an artifact
                # Simple heuristic: look for "name" field before this line
                before_text = "".join(lines[max(0, line_num - 5) : line_num])
                if '"name"' in before_text or "'name'" in before_text:
                    column = match.start()
                    end_column = match.end()
                    return Location(
                        uri=self._path_to_uri(manifest_path),
                        range=Range(
                            start=Position(line=line_num, character=column),
                            end=Position(line=line_num, character=end_column),
                        ),
                    )

        return None

    def _resolve_source_path(self, manifest_path: Path, source_file_str: str) -> Path | None:
        """Resolve source file path relative to manifest location.

        Args:
            manifest_path: Path to the manifest file.
            source_file_str: Source file path from manifest (may be relative).

        Returns:
            Resolved Path object, or None if resolution fails.
        """
        # Find project root (parent of manifests directory)
        project_root = self._find_project_root(manifest_path)

        # Resolve source file path
        source_path = Path(source_file_str)
        if source_path.is_absolute():
            return source_path if source_path.exists() else None

        # Try relative to project root
        resolved = (project_root / source_path).resolve()
        if resolved.exists():
            return resolved

        # Try relative to manifest directory
        resolved = (manifest_path.parent / source_path).resolve()
        if resolved.exists():
            return resolved

        return None

    def _find_project_root(self, manifest_path: Path) -> Path:
        """Find the project root directory for a manifest file.

        Args:
            manifest_path: Path to the manifest file.

        Returns:
            The project root directory.
        """
        # Walk up the path looking for 'manifests' directory
        for parent in manifest_path.parents:
            if parent.name == "manifests":
                return parent.parent
        # Fallback: use the manifest's parent directory
        return manifest_path.parent

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

    def _find_artifact_by_name(self, manifest: dict, name: str) -> dict | None:
        """Find an artifact by name in the manifest.

        Args:
            manifest: The parsed manifest dictionary.
            name: The artifact name to find.

        Returns:
            The artifact dictionary if found, or None.
        """
        expected_artifacts = manifest.get("expectedArtifacts")
        if not expected_artifacts:
            return None

        contains = expected_artifacts.get("contains", [])
        if not isinstance(contains, list):
            return None

        for artifact in contains:
            if isinstance(artifact, dict) and artifact.get("name") == name:
                return artifact

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
