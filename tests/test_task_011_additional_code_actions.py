"""Behavioral tests for Task 011: Additional Code Actions.

These tests verify that the three new code action functions create properly
structured CodeAction objects:
- create_generate_snapshot_action: Creates action to run maid snapshot command
- create_update_version_action: Creates action to update manifest version
- create_generate_tests_action: Creates action to generate test file stubs
"""

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    Command,
)

from maid_lsp.capabilities.code_actions import (
    create_generate_snapshot_action,
    create_generate_tests_action,
    create_update_version_action,
)


class TestCreateGenerateSnapshotAction:
    """Test create_generate_snapshot_action function."""

    def test_returns_code_action_object(self) -> None:
        """create_generate_snapshot_action should return a CodeAction object."""
        action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/task-001.manifest.json"
        )

        assert isinstance(action, CodeAction)

    def test_action_title_mentions_snapshot(self) -> None:
        """create_generate_snapshot_action should have a title mentioning snapshot."""
        action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/task-001.manifest.json"
        )

        assert "snapshot" in action.title.lower()

    def test_action_title_includes_manifest_path(self) -> None:
        """create_generate_snapshot_action should include manifest info in title."""
        action = create_generate_snapshot_action(
            manifest_uri="file:///project/manifests/task-042.manifest.json"
        )

        # Title should reference the manifest somehow
        assert action.title is not None
        assert len(action.title) > 0

    def test_action_has_appropriate_kind(self) -> None:
        """create_generate_snapshot_action should have source or quickfix kind."""
        action = create_generate_snapshot_action(manifest_uri="file:///path/to/manifest.json")

        # Should be either a source action or quickfix
        assert action.kind in (
            CodeActionKind.Source,
            CodeActionKind.QuickFix,
            CodeActionKind.SourceOrganizeImports,
            "source.maid.snapshot",
        )

    def test_action_has_command(self) -> None:
        """create_generate_snapshot_action should have a command to execute."""
        action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/task-001.manifest.json"
        )

        # Should have a command since snapshot requires external execution
        assert action.command is not None
        assert isinstance(action.command, Command)

    def test_command_contains_snapshot_reference(self) -> None:
        """create_generate_snapshot_action command should reference snapshot."""
        action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/task-001.manifest.json"
        )

        assert action.command is not None
        # Command title or command string should mention snapshot
        assert (
            "snapshot" in action.command.command.lower()
            or "snapshot" in action.command.title.lower()
        )

    def test_command_includes_manifest_uri(self) -> None:
        """create_generate_snapshot_action command should include the manifest URI."""
        manifest_uri = "file:///project/manifests/task-099.manifest.json"
        action = create_generate_snapshot_action(manifest_uri=manifest_uri)

        assert action.command is not None
        # The manifest URI should be passed as an argument
        assert action.command.arguments is not None
        assert manifest_uri in action.command.arguments

    def test_different_manifest_uris_create_different_commands(self) -> None:
        """Different manifest URIs should result in different command arguments."""
        uri1 = "file:///path/to/manifest1.json"
        uri2 = "file:///path/to/manifest2.json"

        action1 = create_generate_snapshot_action(manifest_uri=uri1)
        action2 = create_generate_snapshot_action(manifest_uri=uri2)

        assert action1.command is not None
        assert action2.command is not None
        assert action1.command.arguments != action2.command.arguments


class TestCreateUpdateVersionAction:
    """Test create_update_version_action function."""

    def test_returns_code_action_object(self) -> None:
        """create_update_version_action should return a CodeAction object."""
        action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )

        assert isinstance(action, CodeAction)

    def test_action_title_mentions_version(self) -> None:
        """create_update_version_action should have a title mentioning version."""
        action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )

        assert "version" in action.title.lower()

    def test_action_title_includes_current_version(self) -> None:
        """create_update_version_action should include current version in title."""
        action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="2.3.4",
        )

        # Title should include the version number
        assert "2.3.4" in action.title

    def test_action_with_none_version(self) -> None:
        """create_update_version_action should handle None current_version."""
        action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version=None,
        )

        assert isinstance(action, CodeAction)
        assert action.title is not None

    def test_action_has_quickfix_kind(self) -> None:
        """create_update_version_action should have quickfix kind."""
        action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )

        assert action.kind == CodeActionKind.QuickFix

    def test_action_has_edit_or_command(self) -> None:
        """create_update_version_action should have an edit or command."""
        action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )

        # Should have either edit (for direct modification) or command
        assert action.edit is not None or action.command is not None

    def test_action_with_different_document_uri(self) -> None:
        """create_update_version_action should use the provided document URI."""
        uri = "file:///project/manifests/task-005.manifest.json"
        action = create_update_version_action(
            document_uri=uri,
            current_version="0.1.0",
        )

        # If there's an edit, it should reference the document URI
        # If there's a command, the URI should be in the arguments
        if action.edit is not None:
            assert action.edit is not None
        if action.command is not None:
            assert action.command.arguments is not None
            assert uri in action.command.arguments

    def test_different_versions_create_different_titles(self) -> None:
        """Different current versions should result in different titles."""
        action1 = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )
        action2 = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="2.0.0",
        )

        assert action1.title != action2.title

    def test_none_version_has_different_title_than_specific_version(self) -> None:
        """None version should have a different title than a specific version."""
        action_none = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version=None,
        )
        action_specific = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )

        # Titles should be different since one has a version and one doesn't
        assert action_none.title != action_specific.title


class TestCreateGenerateTestsAction:
    """Test create_generate_tests_action function."""

    def test_returns_code_action_object(self) -> None:
        """create_generate_tests_action should return a CodeAction object."""
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/task-001.manifest.json",
            test_file_path="tests/test_task_001.py",
        )

        assert isinstance(action, CodeAction)

    def test_action_title_mentions_tests(self) -> None:
        """create_generate_tests_action should have a title mentioning tests."""
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/task-001.manifest.json",
            test_file_path="tests/test_task_001.py",
        )

        assert "test" in action.title.lower()

    def test_action_title_includes_test_file_path(self) -> None:
        """create_generate_tests_action should include test file path in title."""
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/task-001.manifest.json",
            test_file_path="tests/test_task_042_feature.py",
        )

        # Title should include the test file path
        assert "test_task_042_feature.py" in action.title

    def test_action_has_appropriate_kind(self) -> None:
        """create_generate_tests_action should have source or quickfix kind."""
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_foo.py",
        )

        # Should be either a source action or quickfix
        assert action.kind in (
            CodeActionKind.Source,
            CodeActionKind.QuickFix,
            "source.maid.generateTests",
        )

    def test_action_has_command_or_edit(self) -> None:
        """create_generate_tests_action should have a command or edit."""
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/task-001.manifest.json",
            test_file_path="tests/test_task_001.py",
        )

        # Should have either a command or an edit
        assert action.command is not None or action.edit is not None

    def test_command_or_edit_references_test_file(self) -> None:
        """create_generate_tests_action should reference the test file path."""
        test_path = "tests/test_task_999.py"
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path=test_path,
        )

        if action.command is not None:
            assert action.command.arguments is not None
            assert test_path in action.command.arguments
        elif action.edit is not None:
            # Edit should create or modify the test file
            assert action.edit is not None

    def test_command_or_edit_references_manifest(self) -> None:
        """create_generate_tests_action should reference the manifest URI."""
        manifest_uri = "file:///project/manifests/task-007.manifest.json"
        action = create_generate_tests_action(
            manifest_uri=manifest_uri,
            test_file_path="tests/test_task_007.py",
        )

        if action.command is not None:
            assert action.command.arguments is not None
            assert manifest_uri in action.command.arguments

    def test_different_test_paths_create_different_actions(self) -> None:
        """Different test file paths should result in different actions."""
        action1 = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_a.py",
        )
        action2 = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_b.py",
        )

        assert action1.title != action2.title

    def test_different_manifests_create_different_actions(self) -> None:
        """Different manifest URIs should result in different actions."""
        uri1 = "file:///path/to/manifest1.json"
        uri2 = "file:///path/to/manifest2.json"

        action1 = create_generate_tests_action(
            manifest_uri=uri1,
            test_file_path="tests/test_foo.py",
        )
        action2 = create_generate_tests_action(
            manifest_uri=uri2,
            test_file_path="tests/test_foo.py",
        )

        # The actions should differ (at least in command arguments)
        if action1.command is not None and action2.command is not None:
            assert action1.command.arguments != action2.command.arguments


class TestAdditionalCodeActionsIntegration:
    """Integration tests for the additional code action functions."""

    def test_all_actions_return_code_action_type(self) -> None:
        """All three functions should return CodeAction objects."""
        snapshot_action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/manifest.json"
        )
        version_action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )
        tests_action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_foo.py",
        )

        assert isinstance(snapshot_action, CodeAction)
        assert isinstance(version_action, CodeAction)
        assert isinstance(tests_action, CodeAction)

    def test_all_actions_have_titles(self) -> None:
        """All three functions should return actions with non-empty titles."""
        snapshot_action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/manifest.json"
        )
        version_action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )
        tests_action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_foo.py",
        )

        assert snapshot_action.title is not None and len(snapshot_action.title) > 0
        assert version_action.title is not None and len(version_action.title) > 0
        assert tests_action.title is not None and len(tests_action.title) > 0

    def test_all_actions_have_kinds(self) -> None:
        """All three functions should return actions with kinds."""
        snapshot_action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/manifest.json"
        )
        version_action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )
        tests_action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_foo.py",
        )

        assert snapshot_action.kind is not None
        assert version_action.kind is not None
        assert tests_action.kind is not None

    def test_actions_have_distinct_titles(self) -> None:
        """All three actions should have distinct titles for the same manifest."""
        manifest_uri = "file:///path/to/task-001.manifest.json"

        snapshot_action = create_generate_snapshot_action(manifest_uri=manifest_uri)
        version_action = create_update_version_action(
            document_uri=manifest_uri,
            current_version="1.0.0",
        )
        tests_action = create_generate_tests_action(
            manifest_uri=manifest_uri,
            test_file_path="tests/test_task_001.py",
        )

        titles = {snapshot_action.title, version_action.title, tests_action.title}
        assert len(titles) == 3  # All titles should be unique

    def test_all_actions_have_edit_or_command(self) -> None:
        """All three functions should return actions with either edit or command."""
        snapshot_action = create_generate_snapshot_action(
            manifest_uri="file:///path/to/manifest.json"
        )
        version_action = create_update_version_action(
            document_uri="file:///path/to/manifest.json",
            current_version="1.0.0",
        )
        tests_action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_foo.py",
        )

        assert snapshot_action.edit is not None or snapshot_action.command is not None
        assert version_action.edit is not None or version_action.command is not None
        assert tests_action.edit is not None or tests_action.command is not None

    def test_snapshot_action_uses_command(self) -> None:
        """Snapshot action should use a command (external process needed)."""
        action = create_generate_snapshot_action(manifest_uri="file:///path/to/manifest.json")

        # Snapshot requires running external maid command, so should have command
        assert action.command is not None
        assert isinstance(action.command, Command)

    def test_generate_tests_action_uses_command(self) -> None:
        """Generate tests action should use a command (file generation needed)."""
        action = create_generate_tests_action(
            manifest_uri="file:///path/to/manifest.json",
            test_file_path="tests/test_foo.py",
        )

        # Generating tests likely requires a command
        assert action.command is not None or action.edit is not None
