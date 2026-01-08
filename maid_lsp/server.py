"""Main LSP server with pygls integration.

This module provides the MaidLanguageServer class that extends pygls LanguageServer
and registers handlers for document lifecycle and capability features.
"""

from lsprotocol.types import (
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_HOVER,
    CodeActionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
)
from pygls.lsp.server import LanguageServer

from maid_lsp import __version__
from maid_lsp.capabilities.code_actions import CodeActionsHandler
from maid_lsp.capabilities.diagnostics import DiagnosticsHandler
from maid_lsp.capabilities.hover import HoverHandler
from maid_lsp.utils.debounce import Debouncer
from maid_lsp.validation.runner import MaidRunner


class MaidLanguageServer(LanguageServer):
    """Main LSP server class that extends pygls LanguageServer.

    This class initializes handlers for diagnostics, code actions, and hover
    functionality, and provides the core LSP server implementation for MAID
    manifest validation.

    Attributes:
        diagnostics_handler: Handler for publishing diagnostics.
        code_actions_handler: Handler for code action requests.
        hover_handler: Handler for hover requests.
    """

    def __init__(self, name: str = "maid-lsp", version: str = __version__) -> None:
        """Initialize the MaidLanguageServer.

        Args:
            name: The server name. Defaults to "maid-lsp".
            version: The server version. Defaults to maid_lsp.__version__.
        """
        super().__init__(name=name, version=version)

        # Initialize components
        runner = MaidRunner()
        debouncer = Debouncer()

        # Initialize handlers
        self.diagnostics_handler = DiagnosticsHandler(runner, debouncer)
        self.code_actions_handler = CodeActionsHandler()
        self.hover_handler = HoverHandler()


def create_server() -> MaidLanguageServer:
    """Factory function to create and configure the server.

    Creates a new MaidLanguageServer instance with all handlers registered
    and configured with the default name "maid-lsp" and package version.

    Returns:
        A configured MaidLanguageServer instance.
    """
    server = MaidLanguageServer()
    _register_handlers(server)
    return server


def _register_handlers(server: MaidLanguageServer) -> None:
    """Register all LSP handlers on the server.

    Args:
        server: The server instance to register handlers on.
    """

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    async def _did_open(params: DidOpenTextDocumentParams) -> None:
        """Handle textDocument/didOpen notification.

        Validates the document and publishes diagnostics.
        """
        uri = params.text_document.uri
        await server.diagnostics_handler.validate_and_publish(server, uri)

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    async def _did_change(params: DidChangeTextDocumentParams) -> None:
        """Handle textDocument/didChange notification.

        Validates the document and publishes diagnostics (debounced).
        """
        uri = params.text_document.uri
        await server.diagnostics_handler.validate_and_publish(server, uri)

    @server.feature(TEXT_DOCUMENT_DID_CLOSE)
    def _did_close(params: DidCloseTextDocumentParams) -> None:
        """Handle textDocument/didClose notification.

        Clears diagnostics for the closed document.
        """
        uri = params.text_document.uri
        server.diagnostics_handler.clear_diagnostics(server, uri)

    @server.feature(TEXT_DOCUMENT_CODE_ACTION)
    def _code_action(params: CodeActionParams) -> list:
        """Handle textDocument/codeAction request.

        Returns code actions for the requested range.
        """
        # Get diagnostics from the params context if available
        diagnostics = params.context.diagnostics if params.context else []
        return server.code_actions_handler.get_code_actions(params, list(diagnostics))

    @server.feature(TEXT_DOCUMENT_HOVER)
    def _hover(params: HoverParams) -> Hover | None:
        """Handle textDocument/hover request.

        Returns hover information for the position.
        """
        uri = params.text_document.uri
        try:
            document = server.workspace.get_text_document(uri)
            return server.hover_handler.get_hover(params, document)
        except (FileNotFoundError, KeyError):
            # Document not opened yet or not found
            return None
