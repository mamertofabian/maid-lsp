"""Hover handler for maid-lsp.

This module provides the HoverHandler class that handles hover requests
to show artifact information, and the format_artifact_hover function
that formats artifact data as markdown for hover display.
"""

import json
import re

from lsprotocol.types import (
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
)
from pygls.workspace import TextDocument


class HoverHandler:
    """Handles hover requests.

    This class processes hover requests and returns formatted information
    about artifacts defined in manifest files when the cursor is positioned
    over an artifact name.
    """

    def __init__(self) -> None:
        """Initialize the HoverHandler."""
        pass

    def get_hover(self, params: HoverParams, document: TextDocument) -> Hover | None:
        """Get hover information for a position in the document.

        Args:
            params: The hover parameters containing position information.
            document: The text document to search for artifacts.

        Returns:
            A Hover object with artifact information if hovering over an
            artifact name, or None if not on an artifact.
        """
        # Handle empty document
        if not document.source:
            return None

        lines = document.lines if document.lines else document.source.split("\n")
        line_num = params.position.line
        char_pos = params.position.character

        # Handle position outside document bounds
        if line_num >= len(lines):
            return None

        current_line = lines[line_num]

        # Handle position outside line bounds
        if char_pos > len(current_line):
            return None

        # Get the word at cursor position
        word = self._get_word_at_position(current_line, char_pos)
        if not word:
            return None

        # Try to parse the document as JSON and find artifacts
        try:
            manifest = json.loads(document.source)
        except json.JSONDecodeError:
            return None

        # Look for artifact in expectedArtifacts
        artifact = self._find_artifact_by_name(manifest, word)
        if artifact is None:
            return None

        # Format the artifact information
        formatted = format_artifact_hover(artifact)
        markup = MarkupContent(kind=MarkupKind.Markdown, value=formatted)

        return Hover(contents=markup)

    def _get_word_at_position(self, line: str, char_pos: int) -> str | None:
        """Extract the word at the given character position.

        Args:
            line: The line of text to extract from.
            char_pos: The character position within the line.

        Returns:
            The word at the position, or None if not on a word.
        """
        if not line or char_pos < 0 or char_pos > len(line):
            return None

        # Find word boundaries - include underscore as part of word
        word_pattern = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

        for match in word_pattern.finditer(line):
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


def format_artifact_hover(artifact: dict) -> str:
    """Formats artifact info as markdown for hover display.

    Args:
        artifact: A dictionary containing artifact information with fields
            like type, name, args, returns, bases, and description.

    Returns:
        A markdown-formatted string suitable for hover display.
    """
    parts: list[str] = []

    artifact_type = artifact.get("type", "unknown")
    artifact_name = artifact.get("name", "unknown")

    # Format the signature based on type
    if artifact_type == "function":
        # Build function signature
        args = artifact.get("args", [])
        args_str = _format_args(args)
        returns = artifact.get("returns", {})
        return_type = returns.get("type", "") if isinstance(returns, dict) else ""

        signature = f"def {artifact_name}({args_str})"
        if return_type:
            signature += f" -> {return_type}"

        parts.append(f"```python\n{signature}\n```")

    elif artifact_type == "class":
        # Build class signature
        bases = artifact.get("bases", [])
        if bases:
            bases_str = ", ".join(bases)
            signature = f"class {artifact_name}({bases_str})"
        else:
            signature = f"class {artifact_name}"

        parts.append(f"```python\n{signature}\n```")

    else:
        # Generic format for other types
        parts.append(f"**{artifact_type}** `{artifact_name}`")

    # Add description if present
    description = artifact.get("description")
    if description:
        parts.append(f"\n{description}")

    return "\n".join(parts)


def _format_args(args: list) -> str:
    """Format function arguments for signature display.

    Args:
        args: List of argument dictionaries with name and type fields.

    Returns:
        A comma-separated string of formatted arguments.
    """
    if not args:
        return ""

    formatted_args = []
    for arg in args:
        if isinstance(arg, dict):
            arg_name = arg.get("name", "")
            arg_type = arg.get("type", "")
            if arg_type:
                formatted_args.append(f"{arg_name}: {arg_type}")
            else:
                formatted_args.append(arg_name)

    return ", ".join(formatted_args)
