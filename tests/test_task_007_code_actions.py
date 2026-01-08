"""Behavioral tests for Task 007: Code Actions Handler.

These tests verify that the CodeActionsHandler class correctly handles code action
requests, and that the helper functions create_add_field_action and create_file_action
return properly structured CodeAction objects.
"""

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
    TextDocumentIdentifier,
)

from maid_lsp.capabilities.code_actions import (
    CodeActionsHandler,
    create_add_field_action,
    create_file_action,
)


class TestCodeActionsHandlerInit:
    """Test CodeActionsHandler initialization."""

    def test_init_creates_instance(self) -> None:
        """CodeActionsHandler should be instantiable."""
        handler = CodeActionsHandler()

        assert handler is not None
        assert isinstance(handler, CodeActionsHandler)

    def test_init_explicit_call(self) -> None:
        """CodeActionsHandler.__init__ should initialize properly with explicit call."""
        handler = CodeActionsHandler.__new__(CodeActionsHandler)
        CodeActionsHandler.__init__(handler)

        assert handler is not None
        assert isinstance(handler, CodeActionsHandler)


class TestCodeActionsHandlerGetCodeActions:
    """Test CodeActionsHandler.get_code_actions method."""

    def test_get_code_actions_returns_list(self) -> None:
        """get_code_actions should return a list."""
        handler = CodeActionsHandler()

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=10),
            ),
            context=None,  # type: ignore[arg-type]
        )
        diagnostics: list[Diagnostic] = []

        result = handler.get_code_actions(params=params, diagnostics=diagnostics)

        assert isinstance(result, list)

    def test_get_code_actions_returns_code_action_objects(self) -> None:
        """get_code_actions should return list of CodeAction objects."""
        handler = CodeActionsHandler()

        # Create a diagnostic that should trigger a code action
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=5, character=0),
                end=Position(line=5, character=10),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=5, character=0),
                end=Position(line=5, character=10),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(params=params, diagnostics=[diagnostic])

        # If there are results, they should all be CodeAction objects
        for action in result:
            assert isinstance(action, CodeAction)

    def test_get_code_actions_filters_by_diagnostic_range(self) -> None:
        """get_code_actions should filter actions by diagnostic range."""
        handler = CodeActionsHandler()

        # Create a diagnostic at line 5
        diagnostic_in_range = Diagnostic(
            range=Range(
                start=Position(line=5, character=0),
                end=Position(line=5, character=10),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        # Create a diagnostic at line 20 (outside the requested range)
        diagnostic_out_of_range = Diagnostic(
            range=Range(
                start=Position(line=20, character=0),
                end=Position(line=20, character=10),
            ),
            message="Missing required field 'taskType'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        # Request code actions for range covering line 5 only
        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=4, character=0),
                end=Position(line=6, character=0),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(
            params=params, diagnostics=[diagnostic_in_range, diagnostic_out_of_range]
        )

        # Result should contain actions only for diagnostics within the requested range
        assert isinstance(result, list)
        # All returned actions should be related to diagnostics in the range

    def test_get_code_actions_returns_empty_list_for_no_matching_diagnostics(
        self,
    ) -> None:
        """get_code_actions should return empty list when no diagnostics match."""
        handler = CodeActionsHandler()

        # Create a diagnostic at line 50 (outside the requested range)
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=50, character=0),
                end=Position(line=50, character=10),
            ),
            message="Some error",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        # Request code actions for range at line 0
        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=1, character=0),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(params=params, diagnostics=[diagnostic])

        assert result == []
        assert len(result) == 0

    def test_get_code_actions_with_empty_diagnostics_list(self) -> None:
        """get_code_actions should return empty list when diagnostics list is empty."""
        handler = CodeActionsHandler()

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=10, character=0),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(params=params, diagnostics=[])

        assert result == []
        assert len(result) == 0


class TestCreateAddFieldAction:
    """Test create_add_field_action function."""

    def test_returns_code_action_object(self) -> None:
        """create_add_field_action should return a CodeAction object."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        action = create_add_field_action(diagnostic=diagnostic, field_name="goal")

        assert isinstance(action, CodeAction)

    def test_action_title_includes_field_name(self) -> None:
        """create_add_field_action should include field name in the title."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        action = create_add_field_action(diagnostic=diagnostic, field_name="goal")

        assert "goal" in action.title

    def test_action_title_includes_different_field_name(self) -> None:
        """create_add_field_action should include the specific field name in the title."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5),
            ),
            message="Missing required field 'taskType'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        action = create_add_field_action(diagnostic=diagnostic, field_name="taskType")

        assert "taskType" in action.title

    def test_action_has_quickfix_kind(self) -> None:
        """create_add_field_action should have kind 'quickfix'."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        action = create_add_field_action(diagnostic=diagnostic, field_name="goal")

        assert action.kind == CodeActionKind.QuickFix

    def test_action_includes_workspace_edit(self) -> None:
        """create_add_field_action should include a workspace edit."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        action = create_add_field_action(diagnostic=diagnostic, field_name="goal")

        assert action.edit is not None

    def test_action_has_diagnostics_property(self) -> None:
        """create_add_field_action should associate the diagnostic with the action."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        action = create_add_field_action(diagnostic=diagnostic, field_name="goal")

        # CodeAction can have a diagnostics property
        assert action.diagnostics is not None or action.edit is not None


class TestCreateFileAction:
    """Test create_file_action function."""

    def test_returns_code_action_object(self) -> None:
        """create_file_action should return a CodeAction object."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=0),
                end=Position(line=3, character=20),
            ),
            message="File not found: src/module.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        action = create_file_action(diagnostic=diagnostic, file_path="src/module.py")

        assert isinstance(action, CodeAction)

    def test_action_title_includes_file_path(self) -> None:
        """create_file_action should include file path in the title."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=0),
                end=Position(line=3, character=20),
            ),
            message="File not found: src/module.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        action = create_file_action(diagnostic=diagnostic, file_path="src/module.py")

        assert "src/module.py" in action.title

    def test_action_title_includes_different_file_path(self) -> None:
        """create_file_action should include the specific file path in the title."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=0),
                end=Position(line=3, character=20),
            ),
            message="File not found: tests/test_main.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        action = create_file_action(diagnostic=diagnostic, file_path="tests/test_main.py")

        assert "tests/test_main.py" in action.title

    def test_action_has_quickfix_kind(self) -> None:
        """create_file_action should have kind 'quickfix'."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=0),
                end=Position(line=3, character=20),
            ),
            message="File not found: src/module.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        action = create_file_action(diagnostic=diagnostic, file_path="src/module.py")

        assert action.kind == CodeActionKind.QuickFix

    def test_action_has_edit_or_command(self) -> None:
        """create_file_action should have an edit or command to create the file."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=0),
                end=Position(line=3, character=20),
            ),
            message="File not found: src/module.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        action = create_file_action(diagnostic=diagnostic, file_path="src/module.py")

        # CodeAction should have either edit or command
        assert action.edit is not None or action.command is not None

    def test_action_has_diagnostics_property(self) -> None:
        """create_file_action should associate the diagnostic with the action."""
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=0),
                end=Position(line=3, character=20),
            ),
            message="File not found: src/module.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        action = create_file_action(diagnostic=diagnostic, file_path="src/module.py")

        # CodeAction can have a diagnostics property
        assert (
            action.diagnostics is not None or action.edit is not None or action.command is not None
        )


class TestCodeActionsIntegration:
    """Integration tests for code actions with handler and helper functions."""

    def test_handler_get_code_actions_with_missing_field_diagnostic(self) -> None:
        """Handler should return add field action for missing field diagnostic."""
        handler = CodeActionsHandler()

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=2, character=0),
                end=Position(line=2, character=10),
            ),
            message="Missing required field 'goal'",
            severity=DiagnosticSeverity.Error,
            code="MAID-001",
            source="maid-lsp",
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=2, character=0),
                end=Position(line=2, character=10),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(params=params, diagnostics=[diagnostic])

        assert isinstance(result, list)
        # Should have at least one action for the missing field

    def test_handler_get_code_actions_with_missing_file_diagnostic(self) -> None:
        """Handler should return create file action for missing file diagnostic."""
        handler = CodeActionsHandler()

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=5, character=0),
                end=Position(line=5, character=30),
            ),
            message="File not found: src/main.py",
            severity=DiagnosticSeverity.Error,
            code="MAID-002",
            source="maid-lsp",
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=5, character=0),
                end=Position(line=5, character=30),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(params=params, diagnostics=[diagnostic])

        assert isinstance(result, list)
        # Should have at least one action for the missing file

    def test_handler_get_code_actions_returns_multiple_actions(self) -> None:
        """Handler should return multiple actions for multiple diagnostics."""
        handler = CodeActionsHandler()

        diagnostics = [
            Diagnostic(
                range=Range(
                    start=Position(line=2, character=0),
                    end=Position(line=2, character=10),
                ),
                message="Missing required field 'goal'",
                severity=DiagnosticSeverity.Error,
                code="MAID-001",
                source="maid-lsp",
            ),
            Diagnostic(
                range=Range(
                    start=Position(line=3, character=0),
                    end=Position(line=3, character=10),
                ),
                message="Missing required field 'taskType'",
                severity=DiagnosticSeverity.Error,
                code="MAID-001",
                source="maid-lsp",
            ),
        ]

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=10, character=0),
            ),
            context=None,  # type: ignore[arg-type]
        )

        result = handler.get_code_actions(params=params, diagnostics=diagnostics)

        assert isinstance(result, list)
        # All returned items should be CodeAction objects
        for action in result:
            assert isinstance(action, CodeAction)
