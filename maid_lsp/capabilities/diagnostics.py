"""Diagnostics handler for maid-lsp.

This module provides the DiagnosticsHandler class that manages diagnostic
publishing with debouncing support, and the DiagnosticCode enum that defines
MAID diagnostic codes.
"""

from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from lsprotocol.types import PublishDiagnosticsParams

from maid_lsp.utils.debounce import Debouncer
from maid_lsp.validation.models import ValidationMode
from maid_lsp.validation.parser import validation_result_to_diagnostics
from maid_lsp.validation.runner import MaidRunner


class DiagnosticCode(Enum):
    """Enum of MAID diagnostic codes MAID_001 through MAID_008."""

    MAID_001 = "MAID-001"
    MAID_002 = "MAID-002"
    MAID_003 = "MAID-003"
    MAID_004 = "MAID-004"
    MAID_005 = "MAID-005"
    MAID_006 = "MAID-006"
    MAID_007 = "MAID-007"
    MAID_008 = "MAID-008"


class DiagnosticsHandler:
    """Manages diagnostic publishing with debouncing support.

    This class coordinates validation of manifest files and publishing
    of diagnostics to the LSP client, using debouncing to prevent
    excessive validation calls during rapid document changes.

    Attributes:
        runner: MaidRunner instance for executing validations.
        debouncer: Debouncer instance for coalescing rapid calls.
    """

    def __init__(self, runner: MaidRunner, debouncer: Debouncer) -> None:
        """Initialize the diagnostics handler with runner and debouncer.

        Args:
            runner: MaidRunner instance for executing validations.
            debouncer: Debouncer instance for coalescing rapid calls.
        """
        self._runner = runner
        self._debouncer = debouncer

    async def validate_and_publish(self, server: Any, uri: str) -> None:
        """Validate a document and publish diagnostics to the server.

        Extracts the file path from the URI, uses the debouncer to coalesce
        rapid calls, validates the manifest, converts the result to diagnostics,
        and publishes them to the server.

        Args:
            server: LSP server instance with publish_diagnostics method.
            uri: Document URI (file:// format) to validate.

        Returns:
            None
        """
        # Extract file path from URI
        parsed = urlparse(uri)
        file_path = Path(unquote(parsed.path))

        async def _do_validation() -> None:
            # Call runner.validate with the manifest path (positional args)
            result = await self._runner.validate(
                file_path,
                ValidationMode.IMPLEMENTATION,
            )

            # Convert result to diagnostics
            diagnostics = validation_result_to_diagnostics(result, uri)

            # Publish diagnostics to server
            params = PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
            server.publish_diagnostics(params)

        # Use debouncer to coalesce rapid calls
        await self._debouncer.debounce(uri, _do_validation)

    def clear_diagnostics(self, server: Any, uri: str) -> None:
        """Clear diagnostics for a document URI.

        Publishes an empty diagnostics list to clear any existing diagnostics
        for the specified document.

        Args:
            server: LSP server instance with publish_diagnostics method.
            uri: Document URI to clear diagnostics for.

        Returns:
            None
        """
        server.publish_diagnostics(uri, [])
