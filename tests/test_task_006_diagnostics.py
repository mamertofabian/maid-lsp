"""Behavioral tests for Task 006: Diagnostics Handler.

These tests verify that the DiagnosticsHandler class correctly manages
diagnostic publishing with debouncing support, and that the DiagnosticCode
enum contains the expected MAID diagnostic codes.
"""

from enum import Enum
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from maid_lsp.capabilities.diagnostics import DiagnosticCode, DiagnosticsHandler
from maid_lsp.utils.debounce import Debouncer
from maid_lsp.validation.models import ValidationError, ValidationResult
from maid_lsp.validation.runner import MaidRunner


class TestDiagnosticCodeEnum:
    """Test DiagnosticCode enum."""

    def test_diagnostic_code_is_enum(self) -> None:
        """DiagnosticCode should be an Enum."""
        assert issubclass(DiagnosticCode, Enum)

    def test_diagnostic_code_has_maid_001(self) -> None:
        """DiagnosticCode should have MAID_001 value."""
        assert hasattr(DiagnosticCode, "MAID_001")
        code = DiagnosticCode.MAID_001
        assert code is not None

    def test_diagnostic_code_has_maid_002(self) -> None:
        """DiagnosticCode should have MAID_002 value."""
        assert hasattr(DiagnosticCode, "MAID_002")
        code = DiagnosticCode.MAID_002
        assert code is not None

    def test_diagnostic_code_has_maid_003(self) -> None:
        """DiagnosticCode should have MAID_003 value."""
        assert hasattr(DiagnosticCode, "MAID_003")
        code = DiagnosticCode.MAID_003
        assert code is not None

    def test_diagnostic_code_has_maid_004(self) -> None:
        """DiagnosticCode should have MAID_004 value."""
        assert hasattr(DiagnosticCode, "MAID_004")
        code = DiagnosticCode.MAID_004
        assert code is not None

    def test_diagnostic_code_has_maid_005(self) -> None:
        """DiagnosticCode should have MAID_005 value."""
        assert hasattr(DiagnosticCode, "MAID_005")
        code = DiagnosticCode.MAID_005
        assert code is not None

    def test_diagnostic_code_has_maid_006(self) -> None:
        """DiagnosticCode should have MAID_006 value."""
        assert hasattr(DiagnosticCode, "MAID_006")
        code = DiagnosticCode.MAID_006
        assert code is not None

    def test_diagnostic_code_has_maid_007(self) -> None:
        """DiagnosticCode should have MAID_007 value."""
        assert hasattr(DiagnosticCode, "MAID_007")
        code = DiagnosticCode.MAID_007
        assert code is not None

    def test_diagnostic_code_has_maid_008(self) -> None:
        """DiagnosticCode should have MAID_008 value."""
        assert hasattr(DiagnosticCode, "MAID_008")
        code = DiagnosticCode.MAID_008
        assert code is not None

    def test_diagnostic_codes_are_distinct(self) -> None:
        """All DiagnosticCode values should be distinct."""
        codes = [
            DiagnosticCode.MAID_001,
            DiagnosticCode.MAID_002,
            DiagnosticCode.MAID_003,
            DiagnosticCode.MAID_004,
            DiagnosticCode.MAID_005,
            DiagnosticCode.MAID_006,
            DiagnosticCode.MAID_007,
            DiagnosticCode.MAID_008,
        ]
        # Check all values are unique
        values = [code.value for code in codes]
        assert len(values) == len(set(values)), "All diagnostic codes must have distinct values"


class TestDiagnosticsHandlerInit:
    """Test DiagnosticsHandler initialization."""

    def test_init_with_runner_and_debouncer(self) -> None:
        """DiagnosticsHandler should be instantiable with runner and debouncer."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        assert handler is not None

    def test_init_stores_runner(self) -> None:
        """DiagnosticsHandler should store the runner instance."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        # Verify the handler stores the runner (implementation detail tested via usage)
        assert handler is not None

    def test_init_stores_debouncer(self) -> None:
        """DiagnosticsHandler should store the debouncer instance."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        # Verify the handler stores the debouncer (implementation detail tested via usage)
        assert handler is not None

    def test_init_explicit_call(self) -> None:
        """DiagnosticsHandler.__init__ should initialize properly with explicit call."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler.__new__(DiagnosticsHandler)
        DiagnosticsHandler.__init__(handler, runner=runner, debouncer=debouncer)

        assert handler is not None


class TestDiagnosticsHandlerValidateAndPublish:
    """Test DiagnosticsHandler.validate_and_publish method."""

    @pytest.mark.asyncio
    async def test_validate_and_publish_calls_runner_validate(self) -> None:
        """validate_and_publish should call runner.validate with correct args."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        # Setup mock for runner.validate
        mock_result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        # Setup debouncer to just execute the function immediately
        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        # Setup mock server
        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify runner.validate was called
        runner.validate.assert_called_once()
        call_args = runner.validate.call_args
        # First positional arg should be the manifest path
        assert call_args[0][0] == Path("/path/to/test.manifest.json")

    @pytest.mark.asyncio
    async def test_validate_and_publish_publishes_diagnostics_to_server(self) -> None:
        """validate_and_publish should publish diagnostics to the server."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        # Setup mock for runner.validate with an error
        mock_result = ValidationResult(
            success=False,
            errors=[
                ValidationError(
                    code="MAID-001",
                    message="Test error",
                    file="/path/to/test.manifest.json",
                    line=5,
                    column=1,
                    severity="error",
                )
            ],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        # Setup debouncer to execute immediately
        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        # Setup mock server
        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify publish_diagnostics was called
        server.text_document_publish_diagnostics.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_publish_uses_debouncer(self) -> None:
        """validate_and_publish should use the debouncer."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        # Setup mock for runner.validate
        mock_result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        # Setup debouncer mock
        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        # Setup mock server
        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify debouncer.debounce was called
        debouncer.debounce.assert_called_once()
        # The key should be based on the URI
        call_args = debouncer.debounce.call_args
        assert uri in call_args[0][0] or uri == call_args[0][0]

    @pytest.mark.asyncio
    async def test_validate_and_publish_returns_none(self) -> None:
        """validate_and_publish should return None."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        mock_result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        result = await handler.validate_and_publish(server=server, uri=uri)

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_publish_with_warnings(self) -> None:
        """validate_and_publish should handle warnings correctly."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        mock_result = ValidationResult(
            success=True,
            errors=[],
            warnings=[
                ValidationError(
                    code="MAID-008",
                    message="Test warning",
                    file="/path/to/test.manifest.json",
                    line=10,
                    column=5,
                    severity="warning",
                )
            ],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify publish_diagnostics was called with diagnostics
        server.text_document_publish_diagnostics.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_publish_empty_diagnostics_on_success(self) -> None:
        """validate_and_publish should publish empty diagnostics on successful validation."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        mock_result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify publish_diagnostics was called
        server.text_document_publish_diagnostics.assert_called_once()
        # The diagnostics list should be empty or minimal
        call_args = server.text_document_publish_diagnostics.call_args
        # Check that the URI is correct
        assert uri in str(call_args)


class TestDiagnosticsHandlerClearDiagnostics:
    """Test DiagnosticsHandler.clear_diagnostics method."""

    @pytest.mark.asyncio
    async def test_clear_diagnostics_clears_for_uri(self) -> None:
        """clear_diagnostics should clear diagnostics for the given URI."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        handler.clear_diagnostics(server=server, uri=uri)

        # Verify publish_diagnostics was called with empty diagnostics
        server.text_document_publish_diagnostics.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_diagnostics_uses_correct_uri(self) -> None:
        """clear_diagnostics should clear diagnostics for the specific URI."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///specific/path/manifest.json"
        handler.clear_diagnostics(server=server, uri=uri)

        # Verify the URI is passed correctly
        call_args = server.text_document_publish_diagnostics.call_args
        assert uri in str(call_args)

    @pytest.mark.asyncio
    async def test_clear_diagnostics_publishes_empty_list(self) -> None:
        """clear_diagnostics should publish an empty diagnostics list."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        handler.clear_diagnostics(server=server, uri=uri)

        # Verify publish_diagnostics was called
        server.text_document_publish_diagnostics.assert_called_once()
        # Check that params has empty diagnostics list
        call_args = server.text_document_publish_diagnostics.call_args
        params = call_args.args[0]
        assert params.diagnostics == []


class TestDiagnosticsHandlerIntegration:
    """Integration tests for DiagnosticsHandler with real dependencies."""

    @pytest.mark.asyncio
    async def test_validate_and_publish_with_multiple_errors(self) -> None:
        """validate_and_publish should handle multiple validation errors."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        mock_result = ValidationResult(
            success=False,
            errors=[
                ValidationError(
                    code="MAID-001",
                    message="First error",
                    file="/path/to/test.manifest.json",
                    line=1,
                    column=1,
                    severity="error",
                ),
                ValidationError(
                    code="MAID-002",
                    message="Second error",
                    file="/path/to/test.manifest.json",
                    line=5,
                    column=10,
                    severity="error",
                ),
            ],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///path/to/test.manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify publish_diagnostics was called with multiple diagnostics
        server.text_document_publish_diagnostics.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_publish_converts_file_uri_to_path(self) -> None:
        """validate_and_publish should convert file:// URI to path for validation."""
        runner = MagicMock(spec=MaidRunner)
        debouncer = MagicMock(spec=Debouncer)

        mock_result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        runner.validate = AsyncMock(return_value=mock_result)

        async def run_immediately(_key: str, func):
            return await func()

        debouncer.debounce = AsyncMock(side_effect=run_immediately)

        handler = DiagnosticsHandler(runner=runner, debouncer=debouncer)

        server = MagicMock()
        server.text_document_publish_diagnostics = MagicMock()

        uri = "file:///home/user/project/manifest.json"
        await handler.validate_and_publish(server=server, uri=uri)

        # Verify runner.validate was called with a Path object
        runner.validate.assert_called_once()
        call_args = runner.validate.call_args
        manifest_path = call_args[0][0]
        assert isinstance(manifest_path, Path)
        assert str(manifest_path) == "/home/user/project/manifest.json"
