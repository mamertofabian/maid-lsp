"""Code actions handler for maid-lsp.

This module provides the CodeActionsHandler class that handles code action
requests, and helper functions for creating specific types of code actions.
"""

import re

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    Command,
    CreateFile,
    Diagnostic,
    OptionalVersionedTextDocumentIdentifier,
    Position,
    Range,
    TextDocumentEdit,
    TextEdit,
    WorkspaceEdit,
)


def _ranges_overlap(range1: Range, range2: Range) -> bool:
    """Check if two ranges overlap.

    Args:
        range1: First range to check.
        range2: Second range to check.

    Returns:
        True if the ranges overlap, False otherwise.
    """
    # range1 ends before range2 starts
    if (range1.end.line < range2.start.line) or (
        range1.end.line == range2.start.line and range1.end.character < range2.start.character
    ):
        return False
    # range1 starts after range2 ends
    return not (
        (range1.start.line > range2.end.line)
        or (range1.start.line == range2.end.line and range1.start.character > range2.end.character)
    )


def _extract_field_name_from_message(message: str) -> str | None:
    """Extract field name from a diagnostic message.

    Args:
        message: The diagnostic message.

    Returns:
        The field name if found, None otherwise.
    """
    # Try to match patterns like "Missing required field 'goal'" or "Missing 'goal' field"
    match = re.search(r"['\"](\w+)['\"]", message)
    if match:
        return match.group(1)
    return None


def _extract_file_path_from_message(message: str) -> str | None:
    """Extract file path from a diagnostic message.

    Args:
        message: The diagnostic message.

    Returns:
        The file path if found, None otherwise.
    """
    # Try to match patterns like "File not found: src/module.py"
    match = re.search(r"File not found:\s*(.+)$", message)
    if match:
        return match.group(1).strip()
    # Try other patterns with file paths
    match = re.search(r":\s*(.+\.py)$", message)
    if match:
        return match.group(1).strip()
    return None


def create_add_field_action(diagnostic: Diagnostic, field_name: str) -> CodeAction:
    """Create a code action to add a missing field.

    Creates a CodeAction with kind 'quickfix' that adds the missing field
    to the manifest. The action includes a WorkspaceEdit with the text to insert.

    Args:
        diagnostic: The diagnostic indicating the missing field.
        field_name: The name of the field to add.

    Returns:
        A CodeAction that will add the missing field.
    """
    # Calculate insertion position (at the end of the diagnostic range)
    insert_position = Position(
        line=diagnostic.range.end.line,
        character=diagnostic.range.end.character,
    )

    # Create a placeholder value based on the field name
    if field_name == "goal":
        placeholder_value = '""'
    elif field_name == "taskType":
        placeholder_value = '"create"'
    else:
        placeholder_value = '""'

    # The text to insert
    insert_text = f'"{field_name}": {placeholder_value}'

    # Create the text edit
    text_edit = TextEdit(
        range=Range(start=insert_position, end=insert_position),
        new_text=insert_text,
    )

    # We need a document identifier, but we don't have the URI from the diagnostic
    # The diagnostic doesn't contain the URI, so we create a placeholder
    # The actual URI will need to be provided when applying the action
    # For now, we'll create an edit that the handler can fill in
    workspace_edit = WorkspaceEdit(
        changes=None,
        document_changes=[
            TextDocumentEdit(
                text_document=OptionalVersionedTextDocumentIdentifier(
                    uri="",  # Will be filled in by the handler
                    version=None,
                ),
                edits=[text_edit],
            )
        ],
    )

    return CodeAction(
        title=f"Add missing '{field_name}' field",
        kind=CodeActionKind.QuickFix,
        diagnostics=[diagnostic],
        edit=workspace_edit,
    )


def create_file_action(diagnostic: Diagnostic, file_path: str) -> CodeAction:
    """Create a code action to create a missing file.

    Creates a CodeAction with kind 'quickfix' that creates the missing file.
    The action includes a WorkspaceEdit with a CreateFile operation.

    Args:
        diagnostic: The diagnostic indicating the missing file.
        file_path: The path of the file to create.

    Returns:
        A CodeAction that will create the missing file.
    """
    # Create a file creation operation
    create_file = CreateFile(uri=f"file://{file_path}")

    workspace_edit = WorkspaceEdit(
        changes=None,
        document_changes=[create_file],
    )

    return CodeAction(
        title=f"Create file: {file_path}",
        kind=CodeActionKind.QuickFix,
        diagnostics=[diagnostic],
        edit=workspace_edit,
    )


def create_generate_snapshot_action(manifest_uri: str) -> CodeAction:
    """Create a code action that will run maid snapshot command for the manifest.

    Creates a CodeAction with a command to run the maid snapshot command
    for the specified manifest.

    Args:
        manifest_uri: The URI of the manifest file to snapshot.

    Returns:
        A CodeAction that will run the maid snapshot command.
    """
    return CodeAction(
        title="Generate snapshot for manifest",
        kind=CodeActionKind.Source,
        command=Command(
            title="Run maid snapshot",
            command="maid.snapshot",
            arguments=[manifest_uri],
        ),
    )


def create_update_version_action(document_uri: str, current_version: str | None) -> CodeAction:
    """Create a code action to update the manifest version field.

    Creates a CodeAction with kind 'quickfix' that updates the version field
    of the manifest.

    Args:
        document_uri: The URI of the manifest document.
        current_version: The current version string, or None if not set.

    Returns:
        A CodeAction that will update the version field.
    """
    if current_version is not None:
        title = f"Update version (currently {current_version})"
    else:
        title = "Add version field"

    return CodeAction(
        title=title,
        kind=CodeActionKind.QuickFix,
        command=Command(
            title="Update manifest version",
            command="maid.updateVersion",
            arguments=[document_uri],
        ),
    )


def create_generate_tests_action(manifest_uri: str, test_file_path: str) -> CodeAction:
    """Create a code action to generate test file stubs for the manifest.

    Creates a CodeAction with a command to generate test file stubs
    based on the manifest specification.

    Args:
        manifest_uri: The URI of the manifest file.
        test_file_path: The path where the test file should be generated.

    Returns:
        A CodeAction that will generate test stubs.
    """
    return CodeAction(
        title=f"Generate tests: {test_file_path}",
        kind=CodeActionKind.Source,
        command=Command(
            title="Generate test stubs",
            command="maid.generateTests",
            arguments=[manifest_uri, test_file_path],
        ),
    )


class CodeActionsHandler:
    """Handles code action requests for maid-lsp.

    This class coordinates the generation of code actions based on diagnostics,
    filtering by range and creating appropriate quick fixes for different
    diagnostic types.
    """

    def __init__(self) -> None:
        """Initialize the code actions handler."""
        pass

    def get_code_actions(
        self, params: CodeActionParams, diagnostics: list[Diagnostic]
    ) -> list[CodeAction]:
        """Get code actions for the given diagnostics.

        Filters diagnostics that overlap with the requested range and creates
        appropriate code actions for each relevant diagnostic.

        Args:
            params: The code action request parameters containing the range.
            diagnostics: The list of diagnostics to consider.

        Returns:
            A list of CodeAction objects for applicable diagnostics.
        """
        if not diagnostics:
            return []

        actions: list[CodeAction] = []
        requested_range = params.range
        document_uri = params.text_document.uri

        for diagnostic in diagnostics:
            # Check if the diagnostic overlaps with the requested range
            if not _ranges_overlap(diagnostic.range, requested_range):
                continue

            # Get the diagnostic code
            code = diagnostic.code if diagnostic.code else ""
            code_str = str(code)

            # Create actions based on the diagnostic code
            if code_str in ("MAID-001", "MAID-002"):
                # Missing field diagnostic
                field_name = _extract_field_name_from_message(diagnostic.message)
                if field_name:
                    action = create_add_field_action(diagnostic, field_name)
                    # Update the workspace edit with the actual document URI
                    if action.edit and action.edit.document_changes:
                        for change in action.edit.document_changes:
                            if isinstance(change, TextDocumentEdit):
                                change.text_document.uri = document_uri
                    actions.append(action)

            if code_str in ("MAID-002", "MAID-003"):
                # File reference diagnostic - check if the message mentions a file
                file_path = _extract_file_path_from_message(diagnostic.message)
                if file_path:
                    action = create_file_action(diagnostic, file_path)
                    actions.append(action)

        return actions
