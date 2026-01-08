"""Behavioral tests for Task 009: Main LSP Server.

These tests verify that the MaidLanguageServer class is properly implemented
as a subclass of pygls LanguageServer, and that the create_server factory
function returns a correctly configured server instance with registered handlers.
"""

from lsprotocol.types import (
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_HOVER,
)
from pygls.lsp.server import LanguageServer

from maid_lsp.server import MaidLanguageServer, create_server


class TestMaidLanguageServerClass:
    """Test MaidLanguageServer class definition."""

    def test_maid_language_server_exists(self) -> None:
        """MaidLanguageServer class should exist and be importable."""
        assert MaidLanguageServer is not None

    def test_maid_language_server_is_subclass_of_language_server(self) -> None:
        """MaidLanguageServer should be a subclass of LanguageServer."""
        assert issubclass(MaidLanguageServer, LanguageServer)

    def test_maid_language_server_instantiation(self) -> None:
        """MaidLanguageServer should be instantiable."""
        server = MaidLanguageServer(name="test-server", version="0.0.1")

        assert server is not None
        assert isinstance(server, MaidLanguageServer)

    def test_maid_language_server_is_language_server_instance(self) -> None:
        """MaidLanguageServer instance should also be a LanguageServer instance."""
        server = MaidLanguageServer(name="test-server", version="0.0.1")

        assert isinstance(server, LanguageServer)

    def test_maid_language_server_has_name_attribute(self) -> None:
        """MaidLanguageServer should have a name attribute."""
        server = MaidLanguageServer(name="test-server", version="0.0.1")

        assert hasattr(server, "name")
        assert server.name == "test-server"

    def test_maid_language_server_has_version_attribute(self) -> None:
        """MaidLanguageServer should have a version attribute."""
        server = MaidLanguageServer(name="test-server", version="0.0.1")

        assert hasattr(server, "version")
        assert server.version == "0.0.1"


class TestCreateServerFunction:
    """Test create_server factory function."""

    def test_create_server_exists(self) -> None:
        """create_server function should exist and be importable."""
        assert create_server is not None
        assert callable(create_server)

    def test_create_server_returns_maid_language_server(self) -> None:
        """create_server should return a MaidLanguageServer instance."""
        server = create_server()

        assert server is not None
        assert isinstance(server, MaidLanguageServer)

    def test_create_server_returns_language_server_instance(self) -> None:
        """create_server should return an instance that is also a LanguageServer."""
        server = create_server()

        assert isinstance(server, LanguageServer)

    def test_create_server_has_correct_name(self) -> None:
        """create_server should configure the server with the correct name."""
        server = create_server()

        assert server.name == "maid-lsp"

    def test_create_server_has_version(self) -> None:
        """create_server should configure the server with a version."""
        server = create_server()

        assert server.version is not None
        assert isinstance(server.version, str)
        assert len(server.version) > 0


class TestHandlerRegistration:
    """Test that handlers are registered for LSP methods."""

    def test_did_open_handler_registered(self) -> None:
        """Server should have a handler registered for textDocument/didOpen."""
        server = create_server()

        # Check if the handler is registered in the feature manager
        # pygls stores handlers in lsp.fm.feature_handlers or similar structures
        # The exact attribute may vary by pygls version
        handlers = _get_registered_handlers(server)

        assert TEXT_DOCUMENT_DID_OPEN in handlers, (
            f"Handler for {TEXT_DOCUMENT_DID_OPEN} not registered. "
            f"Available handlers: {list(handlers.keys())}"
        )

    def test_did_change_handler_registered(self) -> None:
        """Server should have a handler registered for textDocument/didChange."""
        server = create_server()

        handlers = _get_registered_handlers(server)

        assert TEXT_DOCUMENT_DID_CHANGE in handlers, (
            f"Handler for {TEXT_DOCUMENT_DID_CHANGE} not registered. "
            f"Available handlers: {list(handlers.keys())}"
        )

    def test_did_close_handler_registered(self) -> None:
        """Server should have a handler registered for textDocument/didClose."""
        server = create_server()

        handlers = _get_registered_handlers(server)

        assert TEXT_DOCUMENT_DID_CLOSE in handlers, (
            f"Handler for {TEXT_DOCUMENT_DID_CLOSE} not registered. "
            f"Available handlers: {list(handlers.keys())}"
        )

    def test_code_action_handler_registered(self) -> None:
        """Server should have a handler registered for textDocument/codeAction."""
        server = create_server()

        handlers = _get_registered_handlers(server)

        assert TEXT_DOCUMENT_CODE_ACTION in handlers, (
            f"Handler for {TEXT_DOCUMENT_CODE_ACTION} not registered. "
            f"Available handlers: {list(handlers.keys())}"
        )

    def test_hover_handler_registered(self) -> None:
        """Server should have a handler registered for textDocument/hover."""
        server = create_server()

        handlers = _get_registered_handlers(server)

        assert TEXT_DOCUMENT_HOVER in handlers, (
            f"Handler for {TEXT_DOCUMENT_HOVER} not registered. "
            f"Available handlers: {list(handlers.keys())}"
        )


class TestServerIntegration:
    """Integration tests for MaidLanguageServer with create_server."""

    def test_create_server_multiple_calls_return_new_instances(self) -> None:
        """create_server should return new instances on each call."""
        server1 = create_server()
        server2 = create_server()

        assert server1 is not server2
        assert server1 != server2

    def test_server_has_all_required_handlers(self) -> None:
        """Server should have all required handlers registered."""
        server = create_server()

        handlers = _get_registered_handlers(server)

        required_handlers = [
            TEXT_DOCUMENT_DID_OPEN,
            TEXT_DOCUMENT_DID_CHANGE,
            TEXT_DOCUMENT_DID_CLOSE,
            TEXT_DOCUMENT_CODE_ACTION,
            TEXT_DOCUMENT_HOVER,
        ]

        for handler_name in required_handlers:
            assert (
                handler_name in handlers
            ), f"Required handler {handler_name} not registered"


def _get_registered_handlers(server: LanguageServer) -> dict:
    """Helper function to get registered handlers from a pygls server.

    This function abstracts the pygls internal structure for retrieving
    registered feature handlers, making tests more robust against
    pygls version changes.

    Args:
        server: The LanguageServer instance to inspect.

    Returns:
        A dictionary mapping method names to their handlers.
    """
    # pygls stores handlers in lsp.fm (FeatureManager) or protocol.fm
    # The structure may vary between versions, so we check multiple locations
    handlers = {}

    # Try the protocol.fm.features attribute (pygls 2.x)
    if hasattr(server, "protocol") and hasattr(server.protocol, "fm"):
        fm = server.protocol.fm
        if hasattr(fm, "features"):
            handlers.update(fm.features)
        if hasattr(fm, "builtin_features"):
            handlers.update(fm.builtin_features)
        if hasattr(fm, "feature_handlers"):
            handlers.update(fm.feature_handlers)

    # Try the feature_handlers attribute (pygls 1.x)
    if hasattr(server, "lsp") and hasattr(server.lsp, "fm"):
        fm = server.lsp.fm
        if hasattr(fm, "feature_handlers"):
            handlers.update(fm.feature_handlers)
        if hasattr(fm, "features"):
            handlers.update(fm.features)
        if hasattr(fm, "builtin_features"):
            handlers.update(fm.builtin_features)

    # Try lsp._features directly (older versions)
    if hasattr(server, "lsp") and hasattr(server.lsp, "_features"):
        handlers.update(server.lsp._features)

    return handlers
