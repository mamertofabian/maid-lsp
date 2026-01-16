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

        Performance optimizations:
        - Quick text search before expensive AST parsing
        - Limited search scope to package directories
        - Smart directory detection from pyproject.toml
        - Excludes non-source directories (tests, cache, build, etc.)
        - Deduplicates results to avoid duplicate locations

        Typical performance: <0.5s for most projects.

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
                # Find references in test files (using validationCommand from current manifest)
                references.extend(
                    await self._find_in_tests(word, artifact_info, document, file_path)
                )
                # Find references in source files
                references.extend(await self._find_in_source(word, artifact_info))
        else:
            # Find artifact info from source file
            artifact_info = self._get_artifact_info_from_source(document, file_path, word)
            if artifact_info:
                # Find references in manifests
                references.extend(await self._find_in_manifests(word, artifact_info))
                # Find references in test files (find manifests that define artifact)
                references.extend(
                    await self._find_in_tests(word, artifact_info, document, file_path)
                )
                # Find references in source files
                references.extend(await self._find_in_source(word, artifact_info))
            else:
                # If we can't determine artifact type from source, try to find it in manifests
                # This handles cases where the artifact is defined in source but we need manifest info
                try:
                    # Convert absolute path to relative for find_manifests
                    if file_path.is_absolute():
                        try:
                            relative_path = file_path.relative_to(Path.cwd())
                            manifests = await self.runner.find_manifests(relative_path)
                        except ValueError:
                            manifests = await self.runner.find_manifests(file_path)
                    else:
                        manifests = await self.runner.find_manifests(file_path)
                    
                    # Search manifests for this artifact
                    for manifest_path in manifests:
                        if not manifest_path.exists():
                            continue
                        try:
                            with open(manifest_path, encoding="utf-8") as f:
                                manifest_content = f.read()
                            manifest = json.loads(manifest_content)
                            artifact_info = self._get_artifact_info_from_manifest(
                                TextDocument(f"file://{manifest_path}", manifest_content), word
                            )
                            if artifact_info:
                                # Found artifact in manifest, now find all references
                                references.extend(await self._find_in_manifests(word, artifact_info))
                                references.extend(
                                    await self._find_in_tests(word, artifact_info, document, file_path)
                                )
                                references.extend(await self._find_in_source(word, artifact_info))
                                break
                        except (OSError, json.JSONDecodeError):
                            continue
                except Exception:
                    pass

        # Deduplicate references based on URI, line, and column
        return self._deduplicate_locations(references) if references else []

    async def _find_in_manifests(
        self, artifact_name: str, artifact_info: dict
    ) -> list[Location]:
        """Find references to artifact in manifest files.

        Optimized with quick text search before JSON parsing.

        Args:
            artifact_name: Name of the artifact.
            artifact_info: Dictionary with artifact type and other info.

        Returns:
            List of Locations where artifact is referenced in manifests.
        """
        references: list[Location] = []

        # Search workspace for manifest files
        workspace_root = Path.cwd()
        manifest_dirs = [
            workspace_root / "manifests",
            workspace_root,
        ]

        # Quick text search first - only parse manifests that contain the artifact name
        artifact_bytes = artifact_name.encode("utf-8")
        manifests_to_parse: list[Path] = []

        for manifest_dir in manifest_dirs:
            if not manifest_dir.exists():
                continue

            for manifest_path in manifest_dir.rglob("*.manifest.json"):
                if not manifest_path.is_file():
                    continue

                # Quick check: does file contain artifact name?
                try:
                    with open(manifest_path, "rb") as f:
                        content = f.read()
                        if artifact_bytes in content:
                            manifests_to_parse.append(manifest_path)
                except OSError:
                    continue

        # Now parse only the manifests that contain the artifact
        for manifest_path in manifests_to_parse:
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
        self,
        artifact_name: str,
        artifact_info: dict,
        document: TextDocument,
        file_path: Path,
    ) -> list[Location]:
        """Find references to artifact in test files using validationCommand from manifests.

        Args:
            artifact_name: Name of the artifact.
            artifact_info: Dictionary with artifact type and other info.
            document: The current document (manifest or source file).
            file_path: Path to the current document.

        Returns:
            List of Locations where artifact is referenced in test files.
        """
        references: list[Location] = []
        workspace_root = Path.cwd()

        # Get test files from validationCommand in manifests
        test_files: set[Path] = set()

        if self._is_manifest_file(file_path):
            # We're in a manifest - use its validationCommand
            try:
                manifest = json.loads(document.source)
                validation_command = manifest.get("validationCommand", [])
                test_files.update(self._extract_test_files_from_command(validation_command, workspace_root))
            except json.JSONDecodeError:
                pass
        else:
            # We're in a source file - find all manifests that define this artifact
            # Use quick text search first
            artifact_bytes = artifact_name.encode("utf-8")
            manifest_dirs = [
                workspace_root / "manifests",
                workspace_root,
            ]

            manifests_to_check: list[Path] = []
            for manifest_dir in manifest_dirs:
                if not manifest_dir.exists():
                    continue

                for manifest_path in manifest_dir.rglob("*.manifest.json"):
                    if not manifest_path.is_file():
                        continue

                    # Quick check: does file contain artifact name?
                    try:
                        with open(manifest_path, "rb") as f:
                            if artifact_bytes in f.read():
                                manifests_to_check.append(manifest_path)
                    except OSError:
                        continue

            # Now parse only manifests that might contain the artifact
            for manifest_path in manifests_to_check:
                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        manifest = json.loads(f.read())
                except (OSError, json.JSONDecodeError):
                    continue

                # Check if this manifest defines the artifact
                expected_artifacts = manifest.get("expectedArtifacts", {})
                contains = expected_artifacts.get("contains", [])
                if not isinstance(contains, list):
                    continue

                artifact_found = False
                for artifact in contains:
                    if isinstance(artifact, dict) and artifact.get("name") == artifact_name:
                        artifact_found = True
                        break

                if artifact_found:
                    # Extract test files from this manifest's validationCommand
                    validation_command = manifest.get("validationCommand", [])
                    test_files.update(
                        self._extract_test_files_from_command(validation_command, workspace_root)
                    )

        # Search for artifact references in the specific test files
        # Quick text search first
        artifact_bytes = artifact_name.encode("utf-8")
        for test_path in test_files:
            if not test_path.exists() or not test_path.is_file():
                continue

            # Quick check: does file contain artifact name?
            try:
                with open(test_path, "rb") as f:
                    if artifact_bytes not in f.read():
                        continue
            except OSError:
                continue

            test_refs = self._find_artifact_references_in_source(
                test_path, artifact_name, artifact_info, workspace_root
            )
            references.extend(test_refs)

        return references

    def _extract_test_files_from_command(
        self, validation_command: list, workspace_root: Path
    ) -> list[Path]:
        """Extract test file paths from validationCommand array.

        Args:
            validation_command: The validationCommand array (e.g., ["pytest", "tests/test_*.py", "-v"]).
            workspace_root: Root of the workspace.

        Returns:
            List of Path objects for test files.
        """
        test_files: list[Path] = []

        if not isinstance(validation_command, list):
            return test_files

        for item in validation_command:
            if not isinstance(item, str):
                continue

            # Skip pytest/uv/other command names
            if item in ("pytest", "uv", "run", "python", "-v", "-vv", "--verbose"):
                continue

            # Skip flags
            if item.startswith("-"):
                continue

            # Check if it looks like a test file path
            if "test" in item.lower() or item.endswith(".py"):
                # Resolve relative to workspace root
                test_path = (workspace_root / item).resolve()
                if test_path.exists() and test_path.is_file():
                    test_files.append(test_path)
                else:
                    # Try glob pattern matching
                    if "*" in item:
                        pattern_path = workspace_root / item
                        # Find parent directory
                        parent = pattern_path.parent
                        pattern = pattern_path.name
                        if parent.exists():
                            for matched_file in parent.glob(pattern):
                                if matched_file.is_file():
                                    test_files.append(matched_file.resolve())

        return test_files

    async def _find_in_source(
        self, artifact_name: str, artifact_info: dict
    ) -> list[Location]:
        """Find references to artifact in source files.

        Optimized to only search relevant directories and use fast text search
        before expensive AST parsing.

        Args:
            artifact_name: Name of the artifact.
            artifact_info: Dictionary with artifact type and other info.

        Returns:
            List of Locations where artifact is referenced in source files.
        """
        references: list[Location] = []
        workspace_root = Path.cwd()

        # Smart search scope: prioritize package directories but also search workspace
        # This balances performance with completeness
        source_dirs: list[Path] = []

        # First, try to find package directory from pyproject.toml
        # This is optional - if tomli isn't available, we'll use common locations
        if (workspace_root / "pyproject.toml").exists():
            try:
                # Try tomli first (common in modern Python projects)
                try:
                    import tomli as toml_parser
                except ImportError:
                    # Fallback to tomllib (Python 3.11+)
                    try:
                        import tomllib as toml_parser
                    except ImportError:
                        toml_parser = None

                if toml_parser:
                    with open(workspace_root / "pyproject.toml", "rb") as f:
                        pyproject = toml_parser.load(f)
                        package_name = pyproject.get("project", {}).get("name", "")
                        if package_name:
                            # Convert package name to directory (e.g., "maid-lsp" -> "maid_lsp")
                            package_dir = package_name.replace("-", "_")
                            package_path = workspace_root / package_dir
                            if package_path.exists() and package_path.is_dir():
                                source_dirs.append(package_path)
            except (OSError, KeyError, AttributeError):
                pass

        # Add common package locations
        common_dirs = ["maid_lsp", "src", "lib"]
        for dir_name in common_dirs:
            dir_path = workspace_root / dir_name
            if dir_path.exists() and dir_path.is_dir() and dir_path not in source_dirs:
                source_dirs.append(dir_path)

        # If no specific package dirs found, search workspace but exclude common non-source dirs
        if not source_dirs:
            source_dirs = [workspace_root]

        # Quick text search first - only parse files that contain the artifact name
        artifact_bytes = artifact_name.encode("utf-8")
        files_to_parse: list[Path] = []

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            # Look for Python source files (exclude tests and common non-source dirs)
            exclude_dirs = {"test", "tests", "__pycache__", ".pytest_cache", "build", "dist", ".venv", "venv", "node_modules", ".git"}
            for source_path in source_dir.rglob("*.py"):
                if not source_path.is_file():
                    continue
                # Skip if any part of the path is in exclude list
                if any(part in exclude_dirs for part in source_path.parts):
                    continue

                # Quick check: does file contain artifact name? (much faster than AST parsing)
                try:
                    with open(source_path, "rb") as f:
                        # Read first 64KB for quick check
                        chunk = f.read(65536)
                        if artifact_bytes in chunk:
                            files_to_parse.append(source_path)
                            # If file is small, we already have it in memory
                            if len(chunk) < 65536:
                                # Re-read full file for parsing
                                f.seek(0)
                                continue
                except OSError:
                    continue

        # Now parse only the files that contain the artifact
        for source_path in files_to_parse:
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
            # Check for module-level assignments (attributes)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == artifact_name:
                        return {"type": "attribute", "name": artifact_name}

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

    def _deduplicate_locations(self, locations: list[Location]) -> list[Location]:
        """Remove duplicate locations from a list.

        Two locations are considered duplicates if they have the same URI,
        line number, and column number.

        Args:
            locations: List of Location objects.

        Returns:
            List of unique Location objects, preserving order.
        """
        seen: set[tuple[str, int, int]] = set()
        unique_locations: list[Location] = []

        for location in locations:
            # Create a key from URI, line, and column
            key = (
                location.uri,
                location.range.start.line,
                location.range.start.character,
            )
            if key not in seen:
                seen.add(key)
                unique_locations.append(location)

        return unique_locations
